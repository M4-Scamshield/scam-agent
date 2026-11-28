import json
from copy import deepcopy

import pytest

from scamshield.graph import CallPipeline
from scamshield.llm import AnalystError
from scamshield.state import NewLine, PipelineError
from test_graph import FakeAnalyst, FakeDetector, judged


def test_three_retries_reuse_full_snapshot_and_do_not_repeat_successful_state():
    seen, delays, events = [], [], []
    def eventually(request):
        seen.append(deepcopy(request))
        request["lines"].clear()  # 모델 대역이 입력을 바꿔도 다음 시도의 원문을 잃지 않는다.
        if len(seen) < 4:
            raise AnalystError("TIMEOUT")
        return judged("risky", evidence_lines=[3], context_lines=[1])
    analyst = FakeAnalyst(F1=eventually, F6=judged("within_normal"))
    result = CallPipeline(FakeDetector({"F1", "F6"}), analyst, retry_wait=delays.append).analyze(
        [NewLine(seq=10, text="[p1] 기관 소개"), NewLine(seq=20, text="[p2] 네")],
        [NewLine(seq=30, text="[p1] 송금 요구")], None, 0, on_progress=events.append,
    )
    assert len(seen) == 4 and all(request == seen[0] for request in seen)
    assert delays == [0.5, 1.0, 2.0]
    assert analyst.called().count("F6") == 1
    assert [event.attempt for event in events if event.state == "F1"] == [1, 2, 3, 4]
    assert all(event.status == "analyzing" for event in events[:-1])
    assert events[-1].status == "completed" and result.analysis_status == "completed"
    assert result.evidence_seqs == [30] and result.context_seqs == [10]


@pytest.mark.parametrize("code", ["TIMEOUT", "CONNECTION_FAILED", "HTTP_429", "HTTP_503", "INVALID_OUTPUT", "INVALID_EVIDENCE"])
def test_exhaustion_is_failed_and_never_normal_or_zero(code):
    events, delays = [], []
    analyst = FakeAnalyst(F1=AnalystError(code))
    result = CallPipeline(FakeDetector({"F1"}), analyst, retry_wait=delays.append).analyze(
        [], [NewLine(seq=81, text="[p1] 송금 요구")], None, 0, on_progress=events.append,
    )
    assert len(analyst.requests) == 4 and len(delays) == 3
    assert result.analysis_status == "failed" and result.status is None and result.score is None
    assert result.failures[0].code == code and result.failures[0].attempts == 4
    assert result.failures[0].seqs == [81]
    assert events[-1].status == "failed" and events[-1].failures == result.failures
    assert all(event.status == "analyzing" for event in events[:-1])


def test_exhausted_failure_survives_json_and_no_new_yes_without_resetting_budget():
    analyst = FakeAnalyst(F1=AnalystError("TIMEOUT"))
    pipeline = CallPipeline(FakeDetector({"F1"}, set()), analyst, retry_wait=lambda _: None)
    first = pipeline.analyze([], [NewLine(seq=7, text="[p1] 송금 요구")], None, 0)
    second = pipeline.analyze(["[p1] 송금 요구"], [NewLine(seq=9, text="[p2] 네")], json.loads(json.dumps(first.state)), 1)
    assert len(analyst.requests) == 4
    assert second.analysis_status == "failed" and second.failures[0].seqs == [7]
    assert second.status is None


@pytest.mark.parametrize("code", ["AUTH_FAILED", "REQUEST_REJECTED"])
def test_permanent_error_fails_immediately_and_keeps_other_successes(code):
    delays = []
    analyst = FakeAnalyst(F1=PipelineError("llm", code, "secret"), F6=judged("within_normal"))
    result = CallPipeline(FakeDetector({"F1", "F6"}), analyst, retry_wait=delays.append).analyze(
        [], [NewLine(seq=1, text="[p1] 요구")], None, 0,
    )
    assert result.analysis_status == "failed" and result.failures[0].attempts == 1
    assert analyst.called() == ["F1", "F6"] and delays == []
    assert [item.state for item in result.state_analyses] == ["F6"]
    assert "secret" not in json.dumps(result.model_dump())


def test_detector_retries_without_turning_failure_into_six_no_answers():
    class Detector:
        calls = 0
        def detect_states(self, lines, n_new):
            self.calls += 1
            raise PipelineError("jev", "CALL_FAILED", "private")
    detector, events = Detector(), []
    result = CallPipeline(detector, FakeAnalyst(), retry_wait=lambda _: None).analyze(
        [], [NewLine(seq=1, text="[p1] 요구")], None, 0, on_progress=events.append,
    )
    assert detector.calls == 4 and result.states == {}
    assert result.failures[0].stage == "jev"
    assert result.analysis_status == events[-1].status == "failed"
    assert "private" not in json.dumps([event.model_dump() for event in events])


def test_existing_risk_is_visible_during_another_state_failure():
    analyst = FakeAnalyst(F1=judged("risky", response="송금 중단"), F2=AnalystError("TIMEOUT"))
    pipeline = CallPipeline(FakeDetector({"F1"}, {"F2"}), analyst, retry_wait=lambda _: None)
    first = pipeline.analyze([], [NewLine(seq=10, text="[p1] 송금 요구")], None, 0)
    second = pipeline.analyze(["[p1] 송금 요구"], [NewLine(seq=20, text="[p1] 인증번호 요구")], first.state, 1)
    assert second.analysis_status == "failed" and second.status == "위험"
    assert second.message == "송금 중단" and second.evidence_seqs == [10] and second.score == 40


def test_broken_progress_sink_does_not_repeat_model_calls_or_expose_exception(caplog):
    analyst = FakeAnalyst(F1=judged("risky"))
    def broken(event):
        raise RuntimeError("secret dialog content")
    result = CallPipeline(FakeDetector({"F1"}), analyst).analyze(
        [], [NewLine(seq=1, text="[p1] 요구")], None, 0, on_progress=broken,
    )
    assert result.analysis_status == "completed" and len(analyst.requests) == 1
    assert "secret dialog content" not in caplog.text
