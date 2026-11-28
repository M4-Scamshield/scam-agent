import json
from copy import deepcopy
from unittest.mock import Mock

import pytest

from scamshield.agents.call_agent import CallPipeline
from scamshield.agents.interfaces import OfflineAnalyst, OfflineDetector
from scamshield.agents.supervisor import OfflineSupervisor, SupervisorPipeline, build_supervisor_pipeline
from scamshield.agents.url_agent import OfflineURLAnalyst, failed_lookup
from scamshield.state import ChatMessage, NewLine, PipelineError
from scamshield.llm import AnalystError
from test_graph import FakeAnalyst, FakeDetector

FLAGGED = "https://safe-account-check.example/"
UNKNOWN = "https://example.com/"


def message(text=FLAGGED, mid="chat-1", seq=1):
    return ChatMessage(id=mid, seq=seq, text=text)


def pipeline():
    detector = Mock(wraps=OfflineDetector())
    router = Mock(wraps=OfflineSupervisor())
    urls = Mock(wraps=OfflineURLAnalyst())
    return SupervisorPipeline(CallPipeline(detector, OfflineAnalyst()), router, urls), detector, router, urls


def test_url_only_does_not_invoke_call_agent():
    agent, detector, router, urls = pipeline()
    result = agent.analyze([], [], None, 0, chat=[message()])
    assert result.routes == ["url"] and result.call is None and result.appended_lines == []
    assert result.url_analyses[0].judgment == "risky" and result.url_analyses[0].tool.is_mock
    detector.detect_states.assert_not_called()
    urls.analyze_url.assert_called_once_with(FLAGGED)
    assert result.state["chat_receipts"]["chat-1"]["urls_done"]
    assert FLAGGED not in json.dumps(result.state["chat_receipts"])


def test_old_chat_can_remain_while_new_stt_is_analyzed():
    agent, detector, router, urls = pipeline()
    first = agent.analyze([], [], None, 0, chat=[message()])
    second = agent.analyze([], [NewLine(seq=2, text="[p1] 송금하세요.")], first.state, 1, chat=[message()])
    assert second.routes == ["call"] and second.call.status == "위험"
    assert [line.seq for line in second.appended_lines] == [2]
    assert second.url_analyses == []
    assert router.route_input.call_args.args == (["[p1] 송금하세요."], [], [])
    urls.analyze_url.assert_called_once()


def test_replay_is_skipped_even_with_a_new_instance_and_json_state():
    agent, *_ = pipeline()
    first = agent.analyze([], [], None, 0, chat=[message()])
    agent, detector, router, urls = pipeline()
    second = agent.analyze([], [], json.loads(json.dumps(first.state)), 1, chat=[message(), message()])
    assert second.routes == [] and second.url_analyses == [] and second.call is None
    assert second.state == first.state
    router.route_input.assert_not_called()
    detector.detect_states.assert_not_called()
    urls.analyze_url.assert_not_called()


def test_fresh_state_starts_an_independent_call():
    agent, _, _, urls = pipeline()
    agent.analyze([], [], None, 0, chat=[message()])
    agent.analyze([], [], None, 1, chat=[message()])
    assert urls.analyze_url.call_count == 2


def test_same_url_in_a_new_message_reuses_session_result():
    agent, _, _, urls = pipeline()
    first = agent.analyze([], [], None, 0, chat=[message("https://EXAMPLE.com:443/#first")])
    second = agent.analyze([], [], first.state, 1, chat=[message("https://example.com/#second", "chat-2", 2)])
    assert second.routes == [] and second.url_analyses[0].judgment == "unknown"
    assert second.state["chat_receipts"]["chat-2"]["urls_done"]
    urls.analyze_url.assert_called_once_with(UNKNOWN)


def test_plain_chat_reaches_call_agent_and_is_not_sent_twice():
    agent, detector, router, _ = pipeline()
    first = agent.analyze([], [], None, 0, chat=[message("지금 송금하세요.")])
    assert first.routes == ["call"] and first.call.status == "위험"
    assert first.appended_lines[0].text == "[사용자 입력] 지금 송금하세요."
    second = agent.analyze([line.text for line in first.appended_lines], [], first.state, 1, chat=[message("지금 송금하세요.")])
    assert second.routes == []
    detector.detect_states.assert_called_once()


def test_partial_url_failure_retries_only_failure_without_repeating_call_work():
    agent, detector, router, urls = pipeline()
    good = OfflineURLAnalyst()
    counts = {}

    def analyze(url):
        counts[url] = counts.get(url, 0) + 1
        return failed_lookup(url) if url == UNKNOWN and counts[url] == 1 else good.analyze_url(url)

    urls.analyze_url.side_effect = analyze
    chat = [message(f"지금 송금하세요. {FLAGGED} {UNKNOWN}", seq=2)]
    first = agent.analyze([], [NewLine(seq=1, text="[p1] 비밀번호를 알려 주세요.")], None, 0, chat=chat)
    assert first.routes == ["call", "url"] and first.call.status == "위험"
    receipt = first.state["chat_receipts"]["chat-1"]
    assert receipt["call_done"] and not receipt["urls_done"]
    assert UNKNOWN not in first.state["url_cache"] and FLAGGED in first.state["url_cache"]
    saved = deepcopy(first.state)
    second = agent.analyze([line.text for line in first.appended_lines], [], first.state, 1, chat=chat)
    assert second.routes == ["url"] and second.call is None
    assert second.state["chat_receipts"]["chat-1"]["urls_done"]
    assert counts == {FLAGGED: 1, UNKNOWN: 2}
    detector.detect_states.assert_called_once()
    assert first.state == saved  # 입력 상태를 직접 변경하지 않는다.


def test_message_id_cannot_be_reused_with_different_content_or_seq():
    agent, _, router, urls = pipeline()
    first = agent.analyze([], [], None, 0, chat=[message()])
    for changed in (message(UNKNOWN), message(seq=2)):
        with pytest.raises(PipelineError) as error:
            agent.analyze([], [], first.state, 1, chat=[changed])
        assert error.value.stage == "input"
    router.route_input.assert_called_once()
    urls.analyze_url.assert_called_once()


@pytest.mark.parametrize("kwargs", [
    {"chat": [{"id": "x", "seq": 1, "text": " "}]},
    {"chat": [{"id": "", "seq": 1, "text": "x"}]},
    {"chat": [message(), message(UNKNOWN)]},
    {"chat": [message()], "new_lines": [NewLine(seq=1, text="[p1] 안녕")]},
    {"now": float("nan")}, {"now": float("inf")}, {"state": {"handled": {}}},
])
def test_invalid_input_does_not_invoke_models(kwargs):
    agent, detector, router, urls = pipeline()
    inputs = {"history": [], "new_lines": [], "state": None, "now": 0, **kwargs}
    with pytest.raises(PipelineError) as error:
        agent.analyze(**inputs)
    assert error.value.code == "INVALID_INPUT"
    router.route_input.assert_not_called()
    urls.analyze_url.assert_not_called()


@pytest.mark.parametrize("call,url,chat,lines", [
    (False, False, [], [NewLine(seq=1, text="[p1] 송금하세요.")]),
    (False, False, [message()], []),
    (False, False, [message("일반 채팅")], []),
    (False, True, [], []),
])
def test_supervisor_cannot_silently_drop_required_work(call, url, chat, lines):
    agent, detector, router, urls = pipeline()
    router.route_input.return_value = {key: {"verdict": "Yes" if hit else "No", "probability": 0.9 if hit else 0.1} for key, hit in (("call", call), ("url", url))}
    # 마지막 예는 새 일반 채팅이 있지만 URL만 선택하는 응답이다.
    if not chat and not lines:
        chat = [message("안녕하세요")]
    with pytest.raises(PipelineError) as error:
        agent.analyze([], lines, None, 0, chat=chat)
    assert error.value.stage == "supervisor"
    urls.analyze_url.assert_not_called()


def test_bad_url_agent_output_is_error_and_not_cached():
    agent, _, _, urls = pipeline()
    urls.analyze_url.return_value = {**OfflineURLAnalyst().analyze_url(UNKNOWN), "judgment": "safe"}
    result = agent.analyze([], [], None, 0, chat=[message(UNKNOWN)])
    assert result.url_analyses[0].judgment == "error"
    assert not result.state["chat_receipts"]["chat-1"]["urls_done"]
    assert result.state["url_cache"] == {}


def test_auth_errors_propagate_without_mutating_input_state():
    agent, _, _, urls = pipeline()
    state = {"call_state": {}, "chat_receipts": {}, "url_cache": {}}
    saved = deepcopy(state)
    urls.analyze_url.side_effect = PipelineError("llm", "AUTH_FAILED", "인증 오류")
    with pytest.raises(PipelineError):
        agent.analyze([], [], state, 0, chat=[message()])
    assert state == saved


def test_public_builders_keep_legacy_and_supervisor_entrypoints():
    from scamshield.graph import build_pipeline, build_supervisor_pipeline as public_builder
    assert isinstance(build_pipeline(offline=True), CallPipeline)
    assert isinstance(public_builder(offline=True), SupervisorPipeline)
    assert build_supervisor_pipeline(offline=True).analyze([], [], None, 0).routes == []


def test_failed_call_remains_visible_on_completed_chat_replay_without_new_attempts():
    analyst, events = FakeAnalyst(F1=AnalystError("TIMEOUT")), []
    agent = SupervisorPipeline(
        CallPipeline(FakeDetector({"F1"}), analyst, retry_wait=lambda _: None),
        OfflineSupervisor(), OfflineURLAnalyst(),
    )
    first = agent.analyze([], [], None, 0, chat=[message("지금 송금하세요.")], on_progress=events.append)
    assert first.analysis_status == "failed" and first.call.status is None
    assert len(first.appended_lines) == 1 and len(analyst.requests) == 4
    assert all(event.status == "analyzing" for event in events[:-1]) and events[-1].status == "failed"
    second = agent.analyze(first.appended_lines, [], first.state, 1, chat=[message("지금 송금하세요.")])
    assert second.call is None and second.analysis_status == "failed" and len(analyst.requests) == 4
    assert second.failures == first.failures


def test_supervisor_terminal_progress_waits_for_url_work_and_is_emitted_once():
    agent, _, _, urls = pipeline()
    events = []
    good = OfflineURLAnalyst()
    def url_work(url):
        assert events and all(event.status == "analyzing" for event in events)
        return good.analyze_url(url)
    urls.analyze_url.side_effect = url_work
    result = agent.analyze([], [NewLine(seq=1, text="[p1] 송금하세요.")], None, 0,
        chat=[message(UNKNOWN, seq=2)], on_progress=events.append)
    assert result.analysis_status == "completed" and events[-1].status == "completed"
    assert sum(event.status == "completed" for event in events) == 1
