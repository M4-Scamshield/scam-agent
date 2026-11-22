from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scamshield.agents.url_agent import HaikuURLAnalyst, MockURLLookup, extract_urls, normalize_url
from scamshield.state import PipelineError

URL = "https://safe-account-check.example/"


def text(value="{}"):
    return SimpleNamespace(type="text", text=value)


def tool(url=URL, name="check_url", use_id="tool-1"):
    return SimpleNamespace(type="tool_use", name=name, input={"url": url}, id=use_id)


def analyst(*responses):
    calls = []

    def create(**kwargs):
        calls.append(deepcopy(kwargs))
        response = queue.pop(0)
        if isinstance(response, Exception):
            raise response
        return SimpleNamespace(content=response)

    queue = list(responses)
    lookup = Mock(wraps=MockURLLookup())
    agent = HaikuURLAnalyst("unused", client=SimpleNamespace(messages=SimpleNamespace(create=create)), lookup=lookup)
    return agent, lookup, calls


def test_extract_multiple_urls_and_ignore_email():
    assert extract_urls("문의: first.last@example.com, https://EXAMPLE.com:443/a?q=1#top 및 (www.example.org).") == [
        "https://example.com/a?q=1", "https://www.example.org/",
    ]
    assert extract_urls("example.com/path?q=1 https://example.com/path?q=1") == ["https://example.com/path?q=1"]
    assert extract_urls("일반 채팅입니다.") == []


def test_url_paths_and_queries_are_not_conflated():
    assert extract_urls("https://example.com/a?x=1 https://example.com/a?x=2 https://example.com/A?x=1") == [
        "https://example.com/a?x=1", "https://example.com/a?x=2", "https://example.com/A?x=1",
    ]
    assert normalize_url("https://example.com/path(a)") == "https://example.com/path(a)"
    assert extract_urls("(https://example.com/path(a))") == ["https://example.com/path(a)"]


@pytest.mark.parametrize("url", ["", "https://a b.com", "https://user:pass@example.com", "ftp://example.com", "https://[", "https://example.com:invalid", "https://example.com\\other"])
def test_reject_unsupported_or_ambiguous_urls(url):
    with pytest.raises(ValueError):
        normalize_url(url)


def test_url_tool_roundtrip_is_bounded_and_model_cannot_override_mock():
    agent, lookup, calls = analyst([tool(), tool(use_id="tool-2")], [text('{"judgment":"safe"}')])
    result = agent.analyze_url(URL)
    assert result["judgment"] == "risky" and result["tool"]["is_mock"]
    lookup.check.assert_called_once_with(URL)
    assert len(calls) == 2
    assert calls[0]["tool_choice"] == {"type": "tool", "name": "check_url"}
    assert calls[1]["tool_choice"] == {"type": "none"}
    assert len(calls[1]["messages"][-1]["content"]) == 2
    assert json.loads(calls[0]["messages"][0]["content"]) == {"url": URL}


def test_not_found_never_becomes_safe_even_if_model_says_so():
    unknown = "https://example.com/"
    agent, _, _ = analyst([tool(unknown)], [text('{"judgment":"safe"}')])
    result = agent.analyze_url(unknown)
    assert result["judgment"] == "unknown" and result["tool"]["status"] == "not_found"


@pytest.mark.parametrize("blocks", [[text("안전합니다")], [tool("https://other.example/")], [tool(name="check_account")]])
def test_missing_or_unrequested_tool_calls_are_not_success(blocks):
    agent, lookup, _ = analyst(blocks, [text()])
    assert agent.analyze_url(URL)["judgment"] == "error"
    lookup.check.assert_not_called()


def test_model_finishing_failure_preserves_completed_lookup():
    agent, lookup, calls = analyst([tool()], TimeoutError("private-response"))
    result = agent.analyze_url(URL)
    assert result["judgment"] == "risky" and "private" not in result["reason"]
    lookup.check.assert_called_once()
    assert len(calls) == 2


def test_first_model_failure_is_retryable_error():
    agent, lookup, calls = analyst(TimeoutError("private-response"))
    result = agent.analyze_url(URL)
    assert result["judgment"] == "error" and "private" not in result["reason"]
    lookup.check.assert_not_called()
    assert len(calls) == 1


def test_auth_error_is_not_hidden_as_unknown():
    agent, _, _ = analyst(PipelineError("llm", "AUTH_FAILED", "인증 오류"))
    with pytest.raises(PipelineError):
        agent.analyze_url(URL)
