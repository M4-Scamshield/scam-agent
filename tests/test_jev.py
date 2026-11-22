import io
import json
from unittest.mock import Mock
from urllib.error import HTTPError, URLError

import pytest

from scamshield.agents.jev_agent import JevClient
from scamshield.state import PipelineError
from scamshield.tactics import STATES

NO = {"type": "choice", "choice": "No", "confidence": 0.9, "probabilities": {"Yes": 0.05, "No": 0.95}}


def response(choice="Yes", probabilities=None):
    """F1만 주어진 답이고 나머지 상태는 No다."""
    answers = {code: dict(NO) for code in STATES}
    answers["F1"] = {
        "type": "choice", "choice": choice, "confidence": 0.8,
        "probabilities": probabilities if probabilities is not None else {"Yes": 0.9, "No": 0.1},
    }
    return {"model": "jev-1.13.0", "answers": answers, "usage": {"input_tokens": 123, "output_tokens": 12}}


def install_response(monkeypatch, raw):
    transport = Mock(return_value=io.BytesIO(json.dumps(raw).encode("utf-8")))
    monkeypatch.setattr("scamshield.agents.jev_agent.urlopen", transport)
    return transport


def test_http_request_matches_official_contract(monkeypatch):
    transport = install_response(monkeypatch, response())
    lines = ["[상대] 안녕하세요.", "[나] 네.", "[상대] 계좌를 확인할게요.", "[나] 왜요?", "[상대] 지금 이체하세요.", "[상대] 오늘 안에요."]
    result = JevClient("synthetic-test-key").detect_states(lines, 2)
    assert result["F1"] == {"verdict": "Yes", "probability": 0.9}
    assert result["F6"] == {"verdict": "No", "probability": 0.05}
    assert list(result) == list(STATES)
    transport.assert_called_once()
    request = transport.call_args.args[0]
    assert request.full_url == "https://api.typesafe.ai/v1/systemone"
    assert request.get_method() == "POST"
    assert request.get_header("Authorization") == "Bearer synthetic-test-key"
    assert transport.call_args.kwargs["timeout"] == 10
    payload = json.loads(request.data)
    assert payload["state"] == {"transcript": lines[:4] + ["(새) " + line for line in lines[4:]]}
    assert payload["model"] == "jev-latest"
    assert set(payload["questions"]) == set(STATES)
    assert "voice_phishing" not in payload["questions"]
    for question in payload["questions"].values():
        assert question["type"] == "choice"
        assert set(question["criteria"]) == {"Yes", "No"}
        assert '"(새)"로 시작하는 줄이 판단할 새 대사' in question["instructions"]


def test_no_returns_probability_of_yes_not_probability_of_no(monkeypatch):
    install_response(monkeypatch, response("No", {"Yes": 0.03, "No": 0.97}))
    assert JevClient("test").detect_states(["[상대] 점심 약속"], 1)["F1"] == {"verdict": "No", "probability": 0.03}


@pytest.mark.parametrize("raw", [
    {}, None, [], {"answers": {"F1": NO}}, response("Maybe"), response("Yes", {"No": 1.0}),
    response("Yes", {"Yes": 0.8, "No": 0.8}),
    response("Yes", {"Yes": 0.1, "No": 0.9}),
    response("Yes", {"Yes": float("nan"), "No": 0.1}),
    response("Yes", {"Yes": True, "No": False}),
    response("Yes", {"Yes": 1.2, "No": -0.2}),
])
def test_invalid_distribution_is_error(monkeypatch, raw):
    install_response(monkeypatch, raw)
    with pytest.raises(PipelineError) as error:
        JevClient("test").detect_states(["[상대] 입력"], 1)
    assert error.value.code == "INVALID_OUTPUT"


@pytest.mark.parametrize("failure", [
    HTTPError("https://api.typesafe.ai", 401, "private-key", {}, io.BytesIO(b"private-body")),
    URLError("private-key"), TimeoutError("private-key"),
])
def test_transport_errors_are_safe_and_not_retried(monkeypatch, failure):
    transport = Mock(side_effect=failure)
    monkeypatch.setattr("scamshield.agents.jev_agent.urlopen", transport)
    with pytest.raises(PipelineError) as error:
        JevClient("private-key").detect_states(["[상대] 입력"], 1)
    assert error.value.code == "CALL_FAILED"
    assert "private" not in error.value.message
    transport.assert_called_once()


def test_non_json_response_is_invalid_output(monkeypatch):
    monkeypatch.setattr("scamshield.agents.jev_agent.urlopen", Mock(return_value=io.BytesIO(b"not JSON")))
    with pytest.raises(PipelineError) as error:
        JevClient("test").detect_states(["[상대] 입력"], 1)
    assert error.value.code == "INVALID_OUTPUT"


def test_env_configuration_and_missing_key(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")
    monkeypatch.setenv("TYPESAFE_BASE_URL", "https://api.typesafe.ai/")
    monkeypatch.setenv("TYPESAFE_DEFAULT_MODEL", "jev-1.13.0")
    client = JevClient.from_env()
    assert client.base_url == "https://api.typesafe.ai"
    assert client.model == "jev-1.13.0"
    monkeypatch.delenv("TYPESAFE_API_KEY")
    with pytest.raises(PipelineError) as error:
        JevClient.from_env()
    assert error.value.code == "MISSING_API_KEY"
