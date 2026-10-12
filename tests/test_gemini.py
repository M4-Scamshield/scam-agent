from copy import deepcopy
from unittest.mock import Mock

import pytest
from langchain_core.messages import AIMessage

from scamshield.gemini import GeminiRoles
from scamshield.graph import CallDemo
from scamshield.state import DEMO_UTTERANCES, DemoError
from scamshield.tools import CASE_LOOKUP_SCHEMA, case_lookup


def model_double(response):
    model = Mock()
    model.invoke.return_value = AIMessage(content="기관명과 사건번호를 물어보세요.")
    model.bind_tools.return_value.invoke.return_value = response
    return model


def tool_message(name="case_lookup", args=None):
    return AIMessage(content="", tool_calls=[{"name": name, "args": args if args is not None else {"case_number": "2026-12345"}, "id": "call-1"}])


def test_single_model_calls_and_separate_execution_with_message_double():
    model = model_double(tool_message())
    lookup = Mock(side_effect=case_lookup)
    demo = CallDemo(GeminiRoles(model), lookup=lookup)
    events = []

    def observe(name, update):
        events.append(name)
        if name == "verify_agent":
            lookup.assert_not_called()

    for utterance in DEMO_UTTERANCES:
        result = demo.run_turn("a", utterance, on_node=observe)
    assert result["phase"] == "WARN"
    model.bind_tools.assert_called_once_with([CASE_LOOKUP_SCHEMA])
    model.invoke.assert_called_once()
    model.bind_tools.return_value.invoke.assert_called_once()
    lookup.assert_called_once_with(case_number="2026-12345")
    assert events[-4:] == ["verify_agent", "tool_execution", "detect_with_jev", "warn"]
    prompt = model.bind_tools.return_value.invoke.call_args.args[0][1][1]
    assert all(u in prompt for u in DEMO_UTTERANCES)


@pytest.mark.parametrize("message", [
    tool_message("unknown"),
    tool_message(args={"case_number": " "}),
    tool_message(args={"case_number": 202612345}),
    tool_message(args={"case_number": "made-up"}),
    tool_message(args={"case_number": "2026"}),
    tool_message(args={"case_number": "12345"}),
    tool_message(args={"case_number": "2026-12345", "extra": "bad"}),
    AIMessage(content="", tool_calls=[
        {"name": "case_lookup", "args": {"case_number": "2026-12345"}, "id": "1"},
        {"name": "case_lookup", "args": {"case_number": "2026-12345"}, "id": "2"},
    ]),
    AIMessage(content="", invalid_tool_calls=[{"name": "case_lookup", "args": "{bad", "id": "1", "error": "invalid"}]),
])
def test_bad_model_selection_executes_no_tool(message):
    model = model_double(message)
    lookup = Mock()
    demo = CallDemo(GeminiRoles(model), lookup=lookup)
    result = demo.run_turn("a", "\n".join(DEMO_UTTERANCES))
    assert result["error"]["stage"] == "verify_agent"
    assert result["error"]["code"] == "INVALID_OUTPUT"
    lookup.assert_not_called()
    assert demo.state("a")["verification_results"] == []
    model.bind_tools.return_value.invoke.assert_called_once()


def test_zero_tool_calls_is_valid_none():
    roles = GeminiRoles(model_double(AIMessage(content="조회할 정보가 부족합니다.")))
    assert roles.verify({"transcript": list(DEMO_UTTERANCES)}) is None


def test_suspect_text_blocks_skip_thinking():
    model = model_double(tool_message())
    model.invoke.return_value = AIMessage(content=[
        {"type": "thinking", "thinking": "internal"},
        {"type": "text", "text": "사건번호를 물어보세요."},
    ])
    assert GeminiRoles(model).suspect({"transcript": []}) == "사건번호를 물어보세요."


def test_model_failure_has_no_retry_and_failed_call_must_restart():
    model = model_double(tool_message())
    model.bind_tools.return_value.invoke.side_effect = RuntimeError("provider failure")
    demo = CallDemo(GeminiRoles(model))
    result = demo.run_turn("a", "\n".join(DEMO_UTTERANCES))
    assert result["error"]["code"] == "CALL_FAILED"
    before = deepcopy(demo.state("a"))
    result = demo.run_turn("a", "다음 발화")
    assert result["error"]["code"] == "EXECUTION_CONTRACT_VIOLATION"
    model.bind_tools.return_value.invoke.assert_called_once()
    assert demo.state("a") == before


def test_missing_key_is_explicit(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(DemoError, match="GEMINI_API_KEY"):
        GeminiRoles.from_env()


def test_installed_sdk_request_and_response_conversion_without_api(monkeypatch):
    from unittest.mock import patch

    from google.genai import types

    # Synthetic test credential; SDK transport is replaced before invocation.
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-credential")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.8-flash")
    roles = GeminiRoles.from_env()
    assert roles.model.max_retries == 0
    assert roles.model.vertexai is False
    responses = [
        types.GenerateContentResponse(candidates=[types.Candidate(
            content=types.Content(role="model", parts=[types.Part(text="사건번호를 물어보세요.")]),
            finish_reason="STOP",
        )]),
        types.GenerateContentResponse(candidates=[types.Candidate(
            content=types.Content(role="model", parts=[types.Part(function_call=types.FunctionCall(
                name="case_lookup", args={"case_number": "2026-12345"},
            ))]),
            finish_reason="STOP",
        )]),
    ]
    with patch.object(roles.model.client.models, "generate_content", side_effect=responses) as generate:
        demo = CallDemo(roles)
        for utterance in DEMO_UTTERANCES:
            result = demo.run_turn("sdk", utterance)
        assert result["phase"] == "WARN"
        assert generate.call_count == 2
        suspect_request, verify_request = [call.kwargs for call in generate.call_args_list]
        assert suspect_request["model"] == verify_request["model"] == "gemini-3.8-flash"
        assert not suspect_request["config"].tools
        declaration = verify_request["config"].tools[0].function_declarations[0]
        assert declaration.name == "case_lookup"
        assert declaration.parameters.required == ["case_number"]
        assert verify_request["config"].http_options.retry_options.attempts == 0
        assert verify_request["config"].thinking_config.thinking_level == types.ThinkingLevel.LOW
        assert verify_request["config"].http_options.timeout == 120000


def test_sdk_provider_error_does_not_reinvoke(monkeypatch):
    from unittest.mock import patch

    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-credential")
    roles = GeminiRoles.from_env()
    with patch.object(roles.model.client.models, "generate_content", side_effect=RuntimeError("provider unavailable")) as generate:
        demo = CallDemo(roles)
        result = demo.run_turn("sdk-error", "\n".join(DEMO_UTTERANCES))
        assert result["error"]["stage"] == "verify_agent"
        generate.assert_called_once()


@pytest.mark.parametrize("stage", ["suspect_agent", "verify_agent"])
def test_sdk_api_error_reports_reason_and_redacts_key(monkeypatch, stage):
    from unittest.mock import patch

    from google.genai.errors import ClientError

    test_key = "offline-secret-test-key"
    monkeypatch.setenv("GEMINI_API_KEY", test_key)
    roles = GeminiRoles.from_env()
    failure = ClientError(404, {"error": {
        "status": "NOT_FOUND",
        "message": f"Model not found. credential={test_key}",
        "details": [{"private": "should-never-be-printed"}],
    }})
    with patch.object(roles.model.client.models, "generate_content", side_effect=failure) as generate:
        demo = CallDemo(roles)
        utterance = "\n".join(DEMO_UTTERANCES[:2 if stage == "suspect_agent" else 3])
        result = demo.run_turn("api-error", utterance)
        assert result["error"]["stage"] == stage
        message = result["error"]["message"]
        assert "HTTP 404 NOT_FOUND" in message
        assert "Model not found" in message
        assert test_key not in message
        assert "should-never-be-printed" not in message
        assert "[REDACTED]" in message
        generate.assert_called_once()


def test_unknown_exception_does_not_print_raw_secrets():
    model = model_double(tool_message())
    model.invoke.side_effect = RuntimeError("raw-private-credential")
    demo = CallDemo(GeminiRoles(model))
    result = demo.run_turn("private-error", "\n".join(DEMO_UTTERANCES[:2]))
    assert "RuntimeError" in result["error"]["message"]
    assert "raw-private-credential" not in result["error"]["message"]
    model.invoke.assert_called_once()
