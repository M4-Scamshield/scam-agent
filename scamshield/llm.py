"""분석·URL 에이전트가 공유하는 Claude 전송과 오류 분류. 역할별 프롬프트는 agents/에 둔다."""

import os

import anthropic

from scamshield.state import PipelineError

MODEL = "claude-haiku-5-5"
EFFORT = "low"
MAX_TOKENS = 2000
TIMEOUT_S = 12.0


class AnalystError(Exception):
    """해당 분석만 실패하는 오류. code만 기록한다."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class HaikuClient:
    system_prompt = ""

    def __init__(self, api_key: str, *, client=None):
        self.client = client or anthropic.Anthropic(api_key=api_key, timeout=TIMEOUT_S, max_retries=0)

    @classmethod
    def from_env(cls):
        return cls(os.environ.get("ANTHROPIC_API_KEY", "").strip())

    def _create(self, messages: list, tools: list, *, allow_tools=True, required_tool: str | None = None):
        kwargs = {"tools": tools} if tools else {}
        if tools and not allow_tools:
            kwargs["tool_choice"] = {"type": "none"}
        elif tools and required_tool:
            kwargs["tool_choice"] = {"type": "tool", "name": required_tool}
        try:
            return self.client.messages.create(
                model=MODEL, max_tokens=MAX_TOKENS, system=self.system_prompt,
                messages=messages, output_config={"effort": EFFORT}, **kwargs,
            )
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as exc:
            raise PipelineError("llm", "AUTH_FAILED", "Anthropic 키 인증에 실패했습니다. ANTHROPIC_API_KEY를 확인하세요.") from exc
        except anthropic.APITimeoutError as exc:
            raise AnalystError("TIMEOUT") from exc
        except anthropic.APIConnectionError as exc:
            raise AnalystError("CONNECTION_FAILED") from exc
        except (anthropic.BadRequestError, anthropic.NotFoundError) as exc:
            raise PipelineError("llm", "REQUEST_REJECTED", f"Anthropic이 요청을 거부했습니다(HTTP {exc.status_code}). 모델·파라미터를 확인하세요.") from exc
        except anthropic.APIStatusError as exc:
            raise AnalystError(f"HTTP_{exc.status_code}") from exc
