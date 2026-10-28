from copy import deepcopy
from unittest.mock import Mock

import pytest

from scamshield.graph import CallPipeline
from scamshield.state import PipelineError

YES = {"verdict": "Yes", "probability": 0.92}
NO = {"verdict": "No", "probability": 0.08}
ANALYSIS = {"reason": "기관 사칭과 안전계좌 송금 요구가 있습니다.", "response": "송금을 중단하고 공식 연락처로 확인하세요."}


def pipeline_for(decision=YES):
    detector = Mock()
    detector.detect.return_value = decision
    analyst = Mock()
    analyst.analyze.return_value = ANALYSIS
    return CallPipeline(detector, analyst), detector, analyst


def test_no_ends_without_calling_llm():
    pipeline, detector, analyst = pipeline_for(NO)
    nodes = []
    result = pipeline.run_turn("normal", "오늘 저녁에 만나요.", on_node=lambda name, _: nodes.append(name))
    assert result == {"callId": "normal", "jev_decision": NO, "analysis": None}
    assert nodes == ["update_context", "detect_with_jev"]
    detector.detect.assert_called_once_with(["오늘 저녁에 만나요."])
    analyst.analyze.assert_not_called()


def test_yes_passes_decision_and_whole_transcript_to_llm_and_saves_analysis():
    pipeline, _, analyst = pipeline_for()
    nodes = []
    result = pipeline.run_turn("fraud", "안전계좌로 송금하세요.", on_node=lambda name, _: nodes.append(name))
    assert nodes == ["update_context", "detect_with_jev", "respond_with_llm"]
    assert result == {"callId": "fraud", "jev_decision": YES, "analysis": ANALYSIS}
    analyst.analyze.assert_called_once_with({
        "utterance": None, "transcript": ["안전계좌로 송금하세요."], "jev_decision": YES, "analysis": None,
    })
    assert pipeline.state("fraud")["analysis"] == ANALYSIS


def test_yes_then_no_clears_analysis_and_isolates_calls():
    pipeline, detector, analyst = pipeline_for()
    detector.detect.side_effect = [YES, NO, NO]
    pipeline.run_turn("a", "첫 발화")
    result = pipeline.run_turn("a", "두 번째 발화")
    assert result["analysis"] is None
    assert pipeline.state("a")["transcript"] == ["첫 발화", "두 번째 발화"]
    assert pipeline.state("a")["utterance"] is None
    pipeline.run_turn("b", "별도 통화")
    assert pipeline.state("b")["transcript"] == ["별도 통화"]
    assert detector.detect.call_args_list[1].args == (["첫 발화", "두 번째 발화"],)
    analyst.analyze.assert_called_once()


@pytest.mark.parametrize("decision", [
    None, {}, {"verdict": "maybe", "probability": 0.5},
    {"verdict": "Yes", "probability": float("nan")},
    {"verdict": "No", "probability": 1.1},
    {"verdict": "Yes", "probability": "0.9"},
    {"verdict": "Yes", "probability": True},
])
def test_invalid_jev_output_never_reaches_llm(decision):
    pipeline, _, analyst = pipeline_for(decision)
    result = pipeline.run_turn("invalid", "입력")
    assert result["error"]["stage"] == "jev"
    assert result["error"]["code"] == "INVALID_OUTPUT"
    analyst.analyze.assert_not_called()
    assert pipeline.state("invalid")["jev_decision"] is None


@pytest.mark.parametrize("call_id, utterance", [("", "text"), ("a", " "), (None, "text"), ("a", 123)])
def test_invalid_input_leaves_state_untouched(call_id, utterance):
    pipeline, detector, analyst = pipeline_for()
    assert pipeline.run_turn(call_id, utterance)["error"]["code"] == "INVALID_INPUT"
    assert pipeline.state("a") == {}
    detector.detect.assert_not_called()
    analyst.analyze.assert_not_called()


def test_provider_failure_is_error_not_no_and_cannot_resume_failed_call():
    pipeline, detector, analyst = pipeline_for()
    detector.detect.side_effect = PipelineError("jev", "CALL_FAILED", "Jev HTTP 401")
    result = pipeline.run_turn("failed", "입력")
    assert "jev_decision" not in result
    assert result["error"]["code"] == "CALL_FAILED"
    before = pipeline.state("failed")
    assert pipeline.run_turn("failed", "다음")["error"]["code"] == "EXECUTION_CONTRACT_VIOLATION"
    assert pipeline.state("failed") == before
    analyst.analyze.assert_not_called()
    detector.detect.assert_called_once()


@pytest.mark.parametrize("analysis", [None, {}, {"reason": " ", "response": "안내"}, {"reason": "근거", "response": ""}])
def test_bad_llm_analysis_is_not_saved(analysis):
    pipeline, _, analyst = pipeline_for()
    analyst.analyze.return_value = analysis
    result = pipeline.run_turn("bad-analysis", "송금 요구")
    assert result["error"]["stage"] == "llm"
    assert result["error"]["code"] == "INVALID_OUTPUT"
    assert pipeline.state("bad-analysis")["jev_decision"] == YES
    assert pipeline.state("bad-analysis")["analysis"] is None


def test_external_dependencies_and_callback_cannot_mutate_checkpoint():
    pipeline, detector, analyst = pipeline_for()

    def detect(transcript):
        transcript.clear()
        return deepcopy(YES)

    def analyze(state):
        state["transcript"].clear()
        state["jev_decision"]["verdict"] = "No"
        return deepcopy(ANALYSIS)

    detector.detect.side_effect = detect
    analyst.analyze.side_effect = analyze
    pipeline.run_turn("copies", "원문", on_node=lambda _, update: update.clear())
    snapshot = pipeline.state("copies")
    assert snapshot["transcript"] == ["원문"]
    assert snapshot["jev_decision"] == YES
    snapshot["transcript"].clear()
    assert pipeline.state("copies")["transcript"] == ["원문"]
