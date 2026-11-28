import json

import pytest

from scamshield.graph import CallPipeline
from scamshield.state import NewLine, PipelineError
from test_graph import FakeAnalyst, FakeDetector, judged


@pytest.fixture(autouse=True)
def no_retry_delays(monkeypatch):
    monkeypatch.setattr("scamshield.recovery.sleep", lambda seconds: None)


def test_batch_selects_actual_request_and_separates_context_from_acknowledgment():
    analyst = FakeAnalyst(F1=judged("risky", evidence_lines=[3, 3], context_lines=[1, 3]))
    outcome = CallPipeline(FakeDetector({"F1"}), analyst).analyze([], [
        NewLine(seq=101, text="[p1] 검찰 수사관입니다."),
        NewLine(seq=102, text="[p2] 네."),
        NewLine(seq=103, text="[p1] 이 계좌로 돈을 보내세요."),
    ], None, 0)
    assert outcome.evidence_seqs == [103]
    assert outcome.context_seqs == [101]
    assert outcome.state_analyses[0].evidence_seqs == [103]
    assert outcome.state["handled"]["F1"]["context_seqs"] == [101]


@pytest.mark.parametrize("evidence,expected", [([2, 3], [103]), ([2], [])])
def test_plain_acknowledgment_is_filtered_even_when_model_selects_it(evidence, expected):
    result = CallPipeline(FakeDetector({"F1"}), FakeAnalyst(
        F1=judged("risky", evidence_lines=evidence),
    )).analyze([], [
        NewLine(seq=101, text="[p1] 검찰입니다."),
        NewLine(seq=102, text="[p2] 네, 알겠습니다."),
        NewLine(seq=103, text="[p1] 이 계좌로 보내세요."),
    ], None, 0)
    assert result.evidence_seqs == expected
    if not expected:
        assert result.analysis_status == "failed" and result.status is None


def test_structured_history_keeps_full_context_and_original_noncontiguous_seqs():
    analyst = FakeAnalyst(F1=judged("risky", evidence_lines=[1], context_lines=[3]))
    history = [NewLine(seq=11, text="[p1] 돈을 보내세요."), NewLine(seq=14, text="[p2] 어디로요?")]
    result = CallPipeline(FakeDetector({"F1"}), analyst).analyze(
        history, [NewLine(seq=20, text="[p1] 수사 협조용 계좌입니다.")], None, 0,
    )
    assert analyst.requests[0]["lines"] == [line.text for line in history] + ["[p1] 수사 협조용 계좌입니다."]
    assert result.evidence_seqs == [11] and result.context_seqs == [20]


def test_string_history_uses_json_restored_reference_mapping():
    analyst = FakeAnalyst(F1=judged("risky", evidence_lines=[1]))
    pipeline = CallPipeline(FakeDetector(set(), {"F1"}), analyst)
    first = pipeline.analyze([], [NewLine(seq=41, text="[p1] 앞선 요구")], None, 0)
    restored = json.loads(json.dumps(first.state))
    result = pipeline.analyze(["[p1] 앞선 요구"], [NewLine(seq=60, text="[p1] 설명")], restored, 1)
    assert result.evidence_seqs == [41]
    assert "앞선 요구" not in json.dumps(result.state, ensure_ascii=False)


@pytest.mark.parametrize("evidence", [[], [0], [-1], [99], [True], ["1"]])
def test_invalid_or_missing_risky_evidence_is_not_replaced_by_batch(evidence):
    outcome = CallPipeline(FakeDetector({"F1"}), FakeAnalyst(
        F1=judged("risky", evidence_lines=evidence),
    )).analyze([], [NewLine(seq=10, text="[p1] 송금하세요.")], None, 0)
    assert outcome.evidence_seqs == [] and outcome.state_analyses == []


def test_legacy_history_does_not_invent_seq_from_array_position():
    result = CallPipeline(FakeDetector({"F1"}), FakeAnalyst(
        F1=judged("risky", evidence_lines=[1]),
    )).analyze(["[p1] 번호 없는 과거 발화"], [NewLine(seq=20, text="[p1] 새 설명")], None, 0)
    assert result.evidence_seqs == []


@pytest.mark.parametrize("history", [[], ["[p1] 바뀐 내용"]])
def test_history_loss_or_replacement_is_rejected_before_model_call(history):
    detector = FakeDetector(set())
    pipeline = CallPipeline(detector, FakeAnalyst())
    first = pipeline.analyze([], [NewLine(seq=10, text="[p1] 원문")], None, 0)
    with pytest.raises(PipelineError) as error:
        pipeline.analyze(history, [NewLine(seq=11, text="[p1] 새 발화")], first.state, 1)
    assert error.value.stage == "input" and len(detector.calls) == 1
