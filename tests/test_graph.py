import json
import threading

import pytest

from scamshield.graph import CallPipeline, FALLBACK_MESSAGE, build_pipeline
from scamshield.agents.analysis_agent import AnalystError
from scamshield.state import NewLine, PipelineError
from scamshield.tactics import STATES


class FakeDetector:
    """요청마다 Yes인 상태 목록을 차례로 돌려준다."""

    def __init__(self, *turns):
        self.turns = list(turns)
        self.calls = []

    def detect_states(self, lines, n_new):
        self.calls.append((list(lines), n_new))
        yes = self.turns.pop(0)
        return {code: {"verdict": "Yes" if code in yes else "No", "probability": 0.8 if code in yes else 0.1} for code in STATES}


def judged(judgment="uncertain", **extra):
    return {"judgment": judgment, "reason": f"{judgment} 판단 이유", "response": "", **extra}


class FakeAnalyst:
    """상태별 결과(dict, 예외, 또는 요청을 받는 함수)를 돌려주고 받은 요청을 남긴다."""

    def __init__(self, **results):
        self.results = results
        self.requests = []
        self.lock = threading.Lock()

    def judge(self, request):
        with self.lock:
            self.requests.append(request)
        result = self.results.get(request["state"], judged())
        if isinstance(result, Exception):
            raise result
        return result(request) if callable(result) else result

    def called(self):
        return sorted(request["state"] for request in self.requests)


class Call:
    """BE 브리지처럼 history와 state를 들고 요청을 이어 보낸다."""

    def __init__(self, detector, analyst):
        self.pipeline = CallPipeline(detector, analyst)
        self.history, self.state, self.seq = [], None, 0

    def say(self, *texts, now=0.0):
        lines = []
        for text in texts:
            self.seq += 1
            lines.append(NewLine(seq=self.seq, text=text))
        outcome = self.pipeline.analyze(self.history, lines, self.state, now)
        self.history += list(texts)
        self.state = outcome.state
        return outcome


def test_no_yes_is_normal_without_haiku():
    analyst = FakeAnalyst()
    outcome = Call(FakeDetector(set()), analyst).say("[상대] 내일 회의는 3시에 해요.")
    assert outcome.status == "정상"
    assert outcome.score == 0
    assert outcome.message is None and outcome.reason is None and outcome.evidence_seqs == []
    assert outcome.states["F1"].verdict == "No"
    assert analyst.requests == []


def test_jev_gets_last_four_history_lines_and_all_new_lines():
    detector = FakeDetector(set(), set())
    call = Call(detector, FakeAnalyst())
    call.say(*[f"[상대] 예시 문장 {i}" for i in range(1, 7)])
    call.say("[나] 새 줄 하나", "[상대] 새 줄 둘", "[나] 새 줄 셋")
    lines, n_new = detector.calls[1]
    assert n_new == 3
    assert lines == [f"[상대] 예시 문장 {i}" for i in range(3, 7)] + ["[나] 새 줄 하나", "[상대] 새 줄 둘", "[나] 새 줄 셋"]


def test_f3_f5_are_held_until_a_core_state_turns_on():
    analyst = FakeAnalyst(F3=judged("risky", response="링크를 누르지 마세요."), F5=judged("uncertain"), F6=judged("uncertain"))
    call = Call(FakeDetector({"F3"}, {"F5", "F3"}, {"F6"}), analyst)
    first = call.say("[상대] 이 주소로 들어가 보세요.")
    assert analyst.requests == []
    assert first.status == "정상"
    assert first.state["held"]["F3"]["seqs"] == [1]
    call.say("[상대] 아무에게도 말하지 마세요.")
    assert analyst.requests == []
    assert call.state["held"]["F3"]["seqs"] == [1, 2]
    assert call.state["held"]["F5"]["seqs"] == [2]
    third = call.say("[상대] 저는 담당 수사관입니다.", now=10)
    assert analyst.called() == ["F3", "F5", "F6"]
    # 보류했던 상태는 자기 감지 대사를 가리키고, 이번에 켜진 상태는 이번 새 줄을 가리킨다.
    detected = {request["state"]: request["detected_lines"] for request in analyst.requests}
    assert detected == {"F3": [1, 2], "F5": [2], "F6": [3]}
    assert third.state["held"] == {}
    assert [analysis.state for analysis in third.state_analyses] == ["F3", "F5", "F6"]
    assert third.status == "위험"
    assert third.message == "링크를 누르지 마세요."
    # 보류했던 F3의 근거는 보류 동안 쌓인 seq다.
    assert third.evidence_seqs == [1, 2]
    assert third.score == 40 + 10 + 5


def test_f3_after_core_is_called_directly():
    analyst = FakeAnalyst()
    call = Call(FakeDetector({"F6"}, {"F3"}), analyst)
    call.say("[상대] 저는 은행 직원입니다.")
    call.say("[상대] 이 앱을 깔아 주세요.")
    assert analyst.called() == ["F3", "F6"]
    assert call.state["held"] == {}


def test_held_state_whose_haiku_fails_waits_for_next_yes():
    analyst = FakeAnalyst(F3=AnalystError("TIMEOUT"))
    call = Call(FakeDetector({"F3"}, {"F4"}, set(), {"F3"}), analyst)
    call.say("[상대] 이 주소로 들어가 보세요.")
    call.say("[상대] 계좌가 정지될 수 있어요.")
    assert "F3" not in call.state["handled"] and call.state["held"] == {}
    call.say("[나] 네.")
    assert analyst.called() == ["F3", "F4"]
    analyst.results["F3"] = judged("within_normal")
    call.say("[상대] 다시 이 주소로 들어가세요.")
    assert analyst.called() == ["F3", "F3", "F4"]
    assert call.state["handled"]["F3"]["judgment"] == "within_normal"


def test_recall_rules_risky_never_uncertain_and_normal_again():
    analyst = FakeAnalyst(F1=judged("risky", response="송금하지 마세요."), F4=judged("uncertain"), F6=judged("within_normal"))
    call = Call(FakeDetector({"F1", "F4", "F6"}, {"F1", "F4", "F6"}), analyst)
    call.say("[상대] 오늘 송금하셔야 합니다.")
    analyst.requests.clear()
    second = call.say("[상대] 다시 말씀드리지만 송금하세요.", now=5)
    assert analyst.called() == ["F4", "F6"]
    previous = {request["state"]: request["previous"] for request in analyst.requests}
    assert previous["F4"]["judgment"] == "uncertain"
    assert previous["F6"]["judgment"] == "within_normal"
    assert second.state["handled"]["F1"]["evidence_seqs"] == [1]


def test_parallel_results_are_ordered_by_priority():
    analyst = FakeAnalyst()
    outcome = Call(FakeDetector({"F6", "F4", "F2", "F1", "F3", "F5"}), analyst).say("[상대] 여러 행동")
    assert [analysis.state for analysis in outcome.state_analyses] == ["F1", "F3", "F2", "F5", "F4", "F6"]


def test_haiku_request_carries_full_conversation_probability_and_context():
    analyst = FakeAnalyst(F6=judged("uncertain", call_context={"purpose": "", "claimed_identity": "검찰 수사관"}))
    call = Call(FakeDetector({"F6"}, {"F1"}), analyst)
    call.say("[상대] 검찰 수사관입니다.")
    call.say("[나] 무슨 일이죠?", "[상대] 돈을 보내셔야 합니다.")
    request = analyst.requests[-1]
    assert request["state"] == "F1"
    assert request["probability"] == 0.8
    assert request["lines"] == ["[상대] 검찰 수사관입니다.", "[나] 무슨 일이죠?", "[상대] 돈을 보내셔야 합니다."]
    assert request["detected_lines"] == [2, 3]
    assert request["call_context"] == {"purpose": "", "claimed_identity": "검찰 수사관"}


@pytest.mark.parametrize("code, expected", [("F1", "risky"), ("F2", "risky"), ("F3", "risky"), ("F5", "risky"), ("F4", "uncertain"), ("F6", "uncertain")])
def test_absolute_line_corrects_only_states_that_have_one(code, expected):
    analyst = FakeAnalyst(**{code: judged("uncertain", absolute_line=True)})
    outcome = Call(FakeDetector({code, "F6"} if code in ("F3", "F5") else {code}), analyst).say("[상대] 예시")
    analysis = next(item for item in outcome.state_analyses if item.state == code)
    assert analysis.judgment == expected
    assert analysis.model_judgment == "uncertain"
    assert analysis.corrections == (["absolute_line"] if expected == "risky" else [])


def test_tool_flagged_forces_risky_and_not_found_does_not_help():
    analyst = FakeAnalyst(
        F1=judged("within_normal", tools=[{"name": "check_account", "status": "flagged"}]),
        F6=judged("uncertain", tools=[{"name": "check_phone", "status": "not_found"}]),
    )
    outcome = Call(FakeDetector({"F1", "F6"}), analyst).say("[상대] 이 계좌로 보내세요.")
    f1, f6 = outcome.state_analyses
    assert (f1.judgment, f1.corrections) == ("risky", ["tool_flagged"])
    assert f1.tools[0].status == "flagged"
    assert (f6.judgment, f6.corrections) == ("uncertain", [])
    assert outcome.status == "위험"
    # 위험인데 Haiku response가 비면 고정 문구다.
    assert outcome.message == FALLBACK_MESSAGE


def test_uncertain_decays_by_half_each_minute_and_risky_stays():
    analyst = FakeAnalyst(F1=judged("uncertain"), F6=judged("risky", response="확인하세요."))
    call = Call(FakeDetector({"F1"}, set(), set(), set(), {"F6"}, set()), analyst)
    assert call.say("[상대] a", now=0).score == 20
    assert call.say("[나] b", now=59).score == 20
    middle = call.say("[나] c", now=60)
    assert (middle.score, middle.status) == (10, "주의")
    gone = call.say("[나] d", now=180)
    assert (gone.score, gone.status, gone.reason) == (0, "정상", None)
    risky = call.say("[상대] e", now=200)
    assert (risky.score, risky.status) == (10, "위험")
    assert call.say("[나] f", now=10_000).score == 10


def test_rejudgment_replaces_the_cell_and_restarts_decay():
    analyst = FakeAnalyst(F2=judged("uncertain"))
    call = Call(FakeDetector({"F2"}, {"F2"}, set()), analyst)
    call.say("[상대] a", now=0)
    again = call.say("[상대] b", now=120)
    assert again.score == 20
    assert call.say("[나] c", now=150).score == 20


def test_score_is_capped_at_100():
    analyst = FakeAnalyst(F1=judged("risky"), F2=judged("risky"), F3=judged("risky"), F5=judged("risky"))
    outcome = Call(FakeDetector({"F1", "F2", "F3", "F5"}), analyst).say("[상대] 예시")
    assert outcome.score == 100


def test_be_fields_message_reason_and_evidence():
    analyst = FakeAnalyst(
        F1=judged("risky", response="송금을 멈추세요."),
        F2=judged("risky", response="인증번호를 알려 주지 마세요."),
        F4=judged("uncertain"),
        F6=judged("within_normal"),
    )
    call = Call(FakeDetector({"F4", "F6"}, {"F2"}, {"F1"}), analyst)
    call.say("[상대] 계좌가 범죄에 쓰였어요.")
    call.say("[상대] 인증번호를 불러 주세요.", "[나] 잠시만요.")
    outcome = call.say("[상대] 이 계좌로 옮기세요.")
    assert outcome.status == "위험"
    assert outcome.message == "송금을 멈추세요."
    assert outcome.reason == "risky 판단 이유"  # 가장 중요한 risky 상태(F1) 하나만
    assert outcome.evidence_seqs == [2, 3, 4]
    assert outcome.score == 40 + 40 + 5


def test_haiku_failure_skips_only_that_state_and_retries_on_next_yes():
    analyst = FakeAnalyst(F1=AnalystError("HTTP_500"), F6=judged("uncertain"))
    call = Call(FakeDetector({"F1", "F6"}, {"F1"}), analyst)
    first = call.say("[상대] 송금하세요.")
    assert [analysis.state for analysis in first.state_analyses] == ["F6"]
    assert "F1" not in first.state["handled"]
    analyst.results["F1"] = judged("risky")
    second = call.say("[상대] 지금 송금하세요.")
    assert second.state["handled"]["F1"]["judgment"] == "risky"


def test_reason_is_top_state_only_and_uncertain_is_hidden_when_risky():
    analyst = FakeAnalyst(F3=judged("uncertain", reason="주소가 아직 안 나옴"), F4=judged("risky", reason="선입금 요구"))
    call = Call(FakeDetector({"F1"}, {"F3", "F4"}), analyst)
    call.say("[상대] 안녕하세요.")
    caution = Call(FakeDetector({"F1", "F3"}), FakeAnalyst(F1=judged("uncertain", reason="송금 목적 불명"),
                                                           F3=judged("uncertain", reason="주소 불명"))).say("[상대] a")
    assert (caution.status, caution.reason) == ("주의", "송금 목적 불명")
    outcome = call.say("[상대] 먼저 입금하셔야 돌려드립니다.")
    assert (outcome.status, outcome.reason) == ("위험", "선입금 요구")  # F3 uncertain 이 우선순위가 높아도 빼고


@pytest.mark.parametrize("bad", [{"judgment": "maybe", "reason": "x"}, {"judgment": "risky"}, RuntimeError("boom")])
def test_invalid_haiku_output_is_skipped(bad):
    analyst = FakeAnalyst(F1=bad)
    outcome = Call(FakeDetector({"F1"}), analyst).say("[상대] 송금하세요.")
    assert outcome.state_analyses == []
    assert outcome.status == "정상"


def test_haiku_auth_failure_raises():
    analyst = FakeAnalyst(F1=PipelineError("llm", "AUTH_FAILED", "인증 실패"), F6=judged())
    with pytest.raises(PipelineError) as error:
        Call(FakeDetector({"F1", "F6"}), analyst).say("[상대] 송금하세요.")
    assert error.value.code == "AUTH_FAILED"


@pytest.mark.parametrize("raw", [RuntimeError("private"), {"F1": {"verdict": "Yes", "probability": 0.9}}, None])
def test_jev_failure_is_an_error_not_all_no(raw):
    class Broken:
        def detect_states(self, lines, n_new):
            if isinstance(raw, Exception):
                raise raw
            return raw

    with pytest.raises(PipelineError) as error:
        Call(Broken(), FakeAnalyst()).say("[상대] 입력")
    assert error.value.stage == "jev"
    assert "private" not in error.value.message


def test_state_round_trips_through_json_and_analyze_is_stateless():
    analyst = FakeAnalyst(F4=judged("uncertain", call_context={"purpose": "사건 조사", "claimed_identity": ""}))
    pipeline = CallPipeline(FakeDetector({"F3"}, {"F4"}, {"F4"}), analyst)
    first = pipeline.analyze([], [NewLine(seq=1, text="[상대] 이 주소로 오세요.")], None, 0)
    restored = json.loads(json.dumps(first.state))
    second = pipeline.analyze(["[상대] 이 주소로 오세요."], [{"seq": 2, "text": "[상대] 계좌가 동결됩니다."}], restored, 1)
    assert second.state["call_context"] == {"purpose": "사건 조사", "claimed_identity": ""}
    assert second.state["seen"] == ["F3", "F4"]
    # 같은 요청을 같은 state로 다시 보내도 판단이 두 번 쌓이지 않는다.
    retry = pipeline.analyze(["[상대] 이 주소로 오세요."], [{"seq": 2, "text": "[상대] 계좌가 동결됩니다."}], restored, 1)
    assert retry.state == second.state
    assert json.loads(json.dumps(second.model_dump())) == second.model_dump()


@pytest.mark.parametrize("history, new_lines, state", [
    ([], [], None),
    ("not a list", [{"seq": 1, "text": "[상대] a"}], None),
    ([], [{"seq": 1, "text": ""}], None),
    ([], [{"seq": 1, "text": "[상대] a"}], {"handled": "broken"}),
    ([], [{"seq": 1, "text": "[상대] a"}], {"handled": {"F7": {"judgment": "risky", "reason": "x", "response": "", "actions": [], "evidence_seqs": [], "judged_at": 0}}}),
])
def test_invalid_input_is_rejected(history, new_lines, state):
    with pytest.raises(PipelineError) as error:
        CallPipeline(FakeDetector(set()), FakeAnalyst()).analyze(history, new_lines, state, 0)
    assert error.value.code == "INVALID_INPUT"


@pytest.mark.parametrize("missing", ["TYPESAFE_API_KEY", "ANTHROPIC_API_KEY"])
def test_build_pipeline_requires_both_keys(monkeypatch, missing):
    monkeypatch.setenv("TYPESAFE_API_KEY", "synthetic-jev-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic-anthropic-key")
    monkeypatch.setenv(missing, " ")
    with pytest.raises(PipelineError) as error:
        build_pipeline()
    assert error.value.code == "config"
    assert missing in error.value.message


def test_build_pipeline_live_and_offline(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "synthetic-jev-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic-anthropic-key")
    assert isinstance(build_pipeline(), CallPipeline)
    monkeypatch.setenv("TYPESAFE_BASE_URL", "http://insecure.example")
    with pytest.raises(PipelineError) as error:
        build_pipeline()
    assert error.value.code == "config"
    outcome = build_pipeline(offline=True).analyze([], [NewLine(seq=1, text="[상대] 지금 송금하세요.")], None, 0)
    assert outcome.status == "위험"


def test_graph_nodes():
    nodes = set(CallPipeline(FakeDetector(), FakeAnalyst()).graph.get_graph().nodes)
    assert {"update_context", "detect_states", "judge_states", "finalize"} <= nodes
