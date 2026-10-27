import json
from unittest.mock import Mock, patch

import pytest
from google.genai import types
from google.genai.errors import ClientError

from scamshield.gemini import GeminiAnalyst
from scamshield.graph import CallPipeline
from scamshield.state import LLMAnalysis, PipelineError

STATE = {"transcript": ["안전계좌로 송금하세요."], "jev_decision": {"verdict": "Yes", "probability": 0.9}, "analysis": None}
ANALYSIS = {"reason": "안전계좌로 송금을 요구합니다.", "response": "송금하지 말고 공식 연락처로 확인하세요."}


def test_llm_receives_transcript_and_jev_result_in_single_structured_call():
    model = Mock()
    model.with_structured_output.return_value.invoke.return_value = ANALYSIS
    analyst = GeminiAnalyst(model)
    assert analyst.analyze(STATE) == ANALYSIS
    model.with_structured_output.assert_called_once_with(LLMAnalysis, method="json_schema")
    structured = model.with_structured_output.return_value
    structured.invoke.assert_called_once()
    payload = json.loads(structured.invoke.call_args.args[0][1][1])
    assert payload == {"transcript": STATE["transcript"], "jev_decision": STATE["jev_decision"]}
    model.bind_tools.assert_not_called()


def test_no_does_not_configure_gemini_or_require_its_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    detector = Mock()
    detector.detect.return_value = {"verdict": "No", "probability": 0.01}
    analyst = GeminiAnalyst()
    assert CallPipeline(detector, analyst).run_turn("no", "일상 대화")["analysis"] is None
    assert analyst.model is None


def test_yes_without_gemini_key_fails_explicitly(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(PipelineError) as error:
        GeminiAnalyst().analyze(STATE)
    assert error.value.code == "MISSING_API_KEY"


@pytest.mark.parametrize("raw", [None, {"reason": " ", "response": "안내"}, {"reason": "근거"}])
def test_invalid_structured_response_is_rejected(raw):
    model = Mock()
    model.with_structured_output.return_value.invoke.return_value = raw
    with pytest.raises(PipelineError) as error:
        GeminiAnalyst(model).analyze(STATE)
    assert error.value.code == "INVALID_OUTPUT"


def test_installed_sdk_structured_json_request_and_response_without_api(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-credential")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.8-flash")
    analyst = GeminiAnalyst()
    analyst._configure()
    message = types.GenerateContentResponse(candidates=[types.Candidate(
        content=types.Content(role="model", parts=[types.Part(text=json.dumps(ANALYSIS))]),
        finish_reason="STOP",
    )])
    with patch.object(analyst.model.client.models, "generate_content", return_value=message) as generate:
        assert analyst.analyze(STATE) == ANALYSIS
        generate.assert_called_once()
        request = generate.call_args.kwargs
        assert request["model"] == "gemini-3.8-flash"
        assert request["config"].response_mime_type == "application/json"
        assert not request["config"].tools
        assert request["config"].http_options.retry_options.attempts == 0
        assert request["config"].http_options.timeout == 120000


def test_provider_failure_never_exposes_error_body_or_retries():
    model = Mock()
    model.with_structured_output.return_value.invoke.side_effect = ClientError(401, {"error": {
        "status": "UNAUTHENTICATED", "message": "private-key", "details": [{"secret": "private-body"}],
    }})
    with pytest.raises(PipelineError) as error:
        GeminiAnalyst(model).analyze(STATE)
    assert "HTTP 401" in error.value.message
    assert "private" not in error.value.message
    model.with_structured_output.return_value.invoke.assert_called_once()
