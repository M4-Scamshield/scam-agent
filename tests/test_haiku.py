import json
from types import SimpleNamespace

import anthropic
import httpx
import pytest

from scamshield.agents.analysis_agent import SYSTEM, AnalystError, HaikuAnalyst, build_user
from scamshield.state import PipelineError
from scamshield.tools import check_account, check_app, check_phone, check_url, run_tool

ANSWER = {
    "judgment": "uncertain",
    "absolute_line": False,
    "reason": "아직 요구가 없습니다.",
    "response": "",
    "actions": ["대표번호로 확인하기"],
    "call_context": {"purpose": "계좌 확인", "claimed_identity": "은행 직원"},
    "evidence_lines": [3],
    "context_lines": [1],
}


def text(value):
    return SimpleNamespace(type="text", text=value)


def tool_use(name, arguments, use_id="toolu_1"):
    return SimpleNamespace(type="tool_use", id=use_id, name=name, input=arguments)


class FakeMessages:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return SimpleNamespace(content=response)


def analyst(*responses):
    messages = FakeMessages(*responses)
    return HaikuAnalyst("unused", client=SimpleNamespace(messages=messages)), messages


def request(state="F6", **extra):
    return {
        "state": state,
        "probability": 0.73,
        "lines": ["[상대] 안녕하세요, 은행입니다.", "[나] 네.", "[상대] 계좌 하나 확인할게요."],
        "detected_lines": [3],
        "call_context": {"purpose": "", "claimed_identity": "은행 직원"},
        "previous": None,
        "line_seqs": [1, 2, 3],
        **extra,
    }


def status_error(cls, code):
    response = httpx.Response(code, request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))
    return cls("synthetic", response=response, body=None)


def test_client_has_timeout_and_no_retries():
    client = HaikuAnalyst("synthetic-key").client
    assert client.timeout == 12.0
    assert client.max_retries == 0


def test_request_shape_without_tools():
    haiku, messages = analyst([text("판단 결과: " + json.dumps(ANSWER, ensure_ascii=False))])
    result = haiku.judge(request())
    assert result["judgment"] == "uncertain"
    assert result["call_context"]["purpose"] == "계좌 확인"
    assert result["tools"] == []
    (call,) = messages.calls
    assert call["model"] == "claude-haiku-5-5"
    assert call["output_config"] == {"effort": "low"}
    assert "temperature" not in call
    assert "tools" not in call
    assert call["system"] == SYSTEM


def test_prompt_has_speaker_legend_identity_limit_and_selected_evidence():
    assert "참가자 id" in SYSTEM and "요구하는 쪽을 상대로" in SYSTEM and "[사용자 입력 …]" in SYSTEM
    assert "상대가 말한 기관·지점이 공식인지는 대화로 확인할 수 없습니다." in SYSTEM
    assert '"evidence_lines"' in SYSTEM and '"context_lines"' in SYSTEM
    assert '"actions"' in SYSTEM
    user = build_user(request("F1", previous={"judgment": "uncertain", "reason": "이전 이유"}))
    assert "감지된 행동: F1 자산 넘기기" in user
    assert "절대선:" in user
    assert "감지기 확률: 0.73, 감지된 대사: 3번" in user
    assert "상대 신분=은행 직원" in user and "목적=모름" in user
    assert "이전 판단: uncertain. 이유: 이전 이유" in user
    assert "3. [상대] 계좌 하나 확인할게요." in user
    assert "절대선:" not in build_user(request("F6"))


def test_f1_tool_round_trip_sends_only_extracted_value():
    haiku, messages = analyst(
        [text("조회합니다."), tool_use("check_account", {"account_number": "111-222-333-34444"})],
        [text(json.dumps({**ANSWER, "judgment": "within_normal"}))],
    )
    result = haiku.judge(request("F1", lines=["[p1] 계좌 111-222-333-34444로 보내세요.", "[p2] 네.", "[p1] 지금요."]))
    assert result["tools"] == [{"name": "check_account", "status": "flagged", "evidence_lines": [1]}]
    # 보정은 graph가 한다. 여기서는 Haiku 판단과 tool 결과를 그대로 돌려준다.
    assert result["judgment"] == "within_normal"
    assert len(messages.calls) == 2
    assert [tool["name"] for tool in messages.calls[0]["tools"]] == ["check_account"]
    tool_result = messages.calls[1]["messages"][-1]["content"][0]
    assert tool_result["type"] == "tool_result" and tool_result["tool_use_id"] == "toolu_1"
    assert json.loads(tool_result["content"])["status"] == "flagged"


def test_f3_gets_three_tools_and_at_most_two_api_calls():
    haiku, messages = analyst(
        [tool_use("check_app", {"app_name": "팀뷰어 퀵서포트"}, "a"), tool_use("check_url", {"url": "bad"}, "b")],
        [tool_use("check_phone", {"phone_number": "1332"}, "c")],
    )
    # 두 번째 응답에 판단 글이 없어도 tool이 찾은 위험(flagged)은 버리지 않는다.
    result = haiku.judge(request("F3", lines=["[p1] 팀뷰어 퀵서포트를 설치하세요.", "[p2] 네.", "[p1] 설치하셨나요?"]))
    assert result["judgment"] == "risky"
    assert {"name": "check_app", "status": "flagged", "evidence_lines": [1]} in result["tools"]
    assert len(messages.calls) == 2
    assert [tool["name"] for tool in messages.calls[0]["tools"]] == ["check_url", "check_app", "check_phone"]
    assert "tool_choice" not in messages.calls[0]
    assert messages.calls[1]["tool_choice"] == {"type": "none"}
    assert len(messages.calls[1]["messages"][-1]["content"]) == 2


def test_missing_judgment_after_tools_without_flag_is_invalid_output():
    haiku, _ = analyst([tool_use("check_account", {"account_number": "999"})], [text("판단을 못 했습니다.")])
    with pytest.raises(AnalystError) as error:
        haiku.judge(request("F1"))
    assert error.value.code == "INVALID_OUTPUT"


def test_loose_haiku_output_is_accepted():
    loose = {**ANSWER, "response": None, "actions": [{"label": "버튼"}, "대표번호로 확인하기"], "call_context": {"purpose": None, "claimed_identity": "은행 직원"}}
    haiku, _ = analyst([text(json.dumps(loose))])
    result = haiku.judge(request("F6"))
    assert result["response"] == "" and result["actions"] == ["대표번호로 확인하기"]
    assert result["call_context"] == {"purpose": "", "claimed_identity": "은행 직원"}


def test_bad_tool_input_is_a_tool_error_not_a_crash():
    assert run_tool("check_phone", {"phone_number": "1332", "claimed_institution": 7})["status"] == "error"


@pytest.mark.parametrize("finish", [
    AnalystError("TIMEOUT"), AnalystError("HTTP_500"),
    PipelineError("llm", "AUTH_FAILED", "인증 오류"),
    [text("잘못된 JSON")],
    [text(json.dumps({**ANSWER, "judgment": "risky", "evidence_lines": [99]}))],
])
def test_grounded_flagged_evidence_survives_model_finalization_failure(finish):
    haiku, _ = analyst([tool_use("check_account", {"account_number": "11122233334444"})], finish)
    result = haiku.judge(request("F1", lines=["[p1] 111-222-333-34444로 보내세요."]))
    assert result["judgment"] == "risky"
    assert result["evidence_lines"] == [1]
    assert result["tools"][0]["status"] == "flagged"


@pytest.mark.parametrize("name,arguments", [
    ("check_account", {"account_number": "11122233334444"}),
    ("check_app", {"app_name": "팀뷰어"}),
])
def test_unmentioned_value_or_wrong_state_tool_is_not_executed(monkeypatch, name, arguments):
    def forbidden(*args):
        raise AssertionError("unverified lookup must not execute")
    monkeypatch.setattr("scamshield.agents.analysis_agent.run_tool", forbidden)
    haiku, _ = analyst([tool_use(name, arguments)], [text(json.dumps(ANSWER))])
    result = haiku.judge(request("F1"))
    assert result["tools"][0]["status"] == "error"
    assert result["tools"][0]["evidence_lines"] == []


@pytest.mark.parametrize("failure, code", [
    (anthropic.APITimeoutError(request=httpx.Request("POST", "https://api.anthropic.com")), "TIMEOUT"),
    (anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com")), "CONNECTION_FAILED"),
    (status_error(anthropic.InternalServerError, 500), "HTTP_500"),
    (status_error(anthropic.RateLimitError, 429), "HTTP_429"),
])
def test_transient_failures_skip_the_state(failure, code):
    haiku, _ = analyst(failure)
    with pytest.raises(AnalystError) as error:
        haiku.judge(request())
    assert error.value.code == code


@pytest.mark.parametrize("cls, code", [(anthropic.AuthenticationError, 401), (anthropic.PermissionDeniedError, 403)])
def test_auth_failures_raise_pipeline_error(cls, code):
    haiku, _ = analyst(status_error(cls, code))
    with pytest.raises(PipelineError) as error:
        haiku.judge(request())
    assert error.value.code == "AUTH_FAILED"


@pytest.mark.parametrize("output", ["JSON이 아닙니다", '{"judgment": "risky"}', '{"judgment": "nope", "reason": "x"}'])
def test_invalid_output_skips_the_state(output):
    haiku, _ = analyst([text(output)])
    with pytest.raises(AnalystError) as error:
        haiku.judge(request())
    assert error.value.code == "INVALID_OUTPUT"


def test_mock_tools_distinguish_flagged_not_found_and_error():
    assert check_account("111-222-333-34444")["status"] == "flagged"
    assert check_account("123-456-789012")["status"] == "not_found"
    assert check_account("12")["status"] == "error"
    assert check_url("https://safe-account-check.example/login")["status"] == "flagged"
    assert check_url("http://10.0.0.1/app")["status"] == "flagged"
    assert check_url("www.example.com")["status"] == "not_found"
    assert check_url("")["status"] == "error"
    app = check_app("Team Viewer")
    assert app["status"] == "flagged" and app["remote_control"] is True
    assert check_app("메모장")["status"] == "not_found"
    assert check_phone("02-1234-5678", "금융감독원")["status"] == "flagged"
    assert check_phone("1332", "금융감독원")["status"] == "not_found"
    assert check_phone("02-1234-5678")["status"] == "not_found"
    assert check_phone("")["status"] == "error"
    assert run_tool("unknown", {})["status"] == "error"
    assert run_tool("check_app", {"wrong": "x"})["status"] == "error"


@pytest.mark.parametrize("cls, code", [(anthropic.BadRequestError, 400), (anthropic.NotFoundError, 404)])
def test_rejected_request_raises_instead_of_silently_skipping(cls, code):
    haiku, _ = analyst(status_error(cls, code))
    with pytest.raises(PipelineError) as error:
        haiku.judge(request("F6"))
    assert error.value.code == "REQUEST_REJECTED"
