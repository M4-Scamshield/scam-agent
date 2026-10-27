import io
import json
from unittest.mock import Mock
from urllib.error import HTTPError, URLError

import pytest

from scamshield.jev import JevClient
from scamshield.state import PipelineError


def response(choice="Yes", probabilities=None):
    return {"model": "jev-1.13.0", "answers": {"voice_phishing": {
        "type": "choice", "choice": choice, "confidence": 0.8,
        "probabilities": probabilities if probabilities is not None else {"Yes": 0.9, "No": 0.1},
    }}, "usage": {"input_tokens": 123, "output_tokens": 12}}


def install_response(monkeypatch, raw):
    transport = Mock(return_value=io.BytesIO(json.dumps(raw).encode("utf-8")))
    monkeypatch.setattr("scamshield.jev.urlopen", transport)
    return transport


def test_http_request_matches_official_contract(monkeypatch):
    transport = install_response(monkeypatch, response())
    result = JevClient("synthetic-test-key").detect(["안전계좌로 송금하세요."])
    assert result == {"verdict": "Yes", "probability": 0.9}
    transport.assert_called_once()
    request = transport.call_args.args[0]
    assert request.full_url == "https://api.typesafe.ai/v1/systemone"
    assert request.get_method() == "POST"
    assert request.get_header("Authorization") == "Bearer synthetic-test-key"
    assert transport.call_args.kwargs["timeout"] == 30
    payload = json.loads(request.data)
    assert payload["state"] == {"transcript": ["안전계좌로 송금하세요."]}
    assert payload["model"] == "jev-latest"
    assert set(payload["questions"]["voice_phishing"]["criteria"]) == {"Yes", "No"}
    assert payload["questions"]["voice_phishing"]["type"] == "choice"


def test_no_returns_probability_of_yes_not_probability_of_no(monkeypatch):
    install_response(monkeypatch, response("No", {"Yes": 0.03, "No": 0.97}))
    assert JevClient("test").detect(["점심 약속"]) == {"verdict": "No", "probability": 0.03}


@pytest.mark.parametrize("raw", [
    {}, None, [], response("Maybe"), response("Yes", {"No": 1.0}),
    response("Yes", {"Yes": 0.8, "No": 0.8}),
    response("Yes", {"Yes": 0.1, "No": 0.9}),
    response("Yes", {"Yes": float("nan"), "No": 0.1}),
    response("Yes", {"Yes": True, "No": False}),
    response("Yes", {"Yes": 1.2, "No": -0.2}),
])
def test_invalid_distribution_is_error(monkeypatch, raw):
    install_response(monkeypatch, raw)
    with pytest.raises(PipelineError) as error:
        JevClient("test").detect(["입력"])
    assert error.value.code == "INVALID_OUTPUT"


@pytest.mark.parametrize("failure", [
    HTTPError("https://api.typesafe.ai", 401, "private-key", {}, io.BytesIO(b"private-body")),
    URLError("private-key"), TimeoutError("private-key"),
])
def test_transport_errors_are_safe_and_not_retried(monkeypatch, failure):
    transport = Mock(side_effect=failure)
    monkeypatch.setattr("scamshield.jev.urlopen", transport)
    with pytest.raises(PipelineError) as error:
        JevClient("private-key").detect(["입력"])
    assert error.value.code == "CALL_FAILED"
    assert "private" not in error.value.message
    transport.assert_called_once()


def test_non_json_response_is_invalid_output(monkeypatch):
    monkeypatch.setattr("scamshield.jev.urlopen", Mock(return_value=io.BytesIO(b"not JSON")))
    with pytest.raises(PipelineError) as error:
        JevClient("test").detect(["입력"])
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
