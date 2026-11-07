from typing import Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field, model_validator


class JevDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    verdict: Literal["Yes", "No"]
    # Always P(voice phishing / Yes), including when verdict is No.
    probability: float = Field(ge=0, le=1, allow_inf_nan=False)


class LLMAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)

    # Gemini의 재판단. Jev의 Yes가 실제 대화 근거로도 피싱이면 True다.
    # 저장된 jev_decision(Yes/No·확률)은 덮어쓰지 않고 이 필드로 나란히 보존한다.
    is_phishing: bool = Field(description="Jev의 Yes를 재판단한 결과(실제 피싱이면 True)")
    reason: str = Field(min_length=1, description="대화에 근거한 재판단 이유와 불확실성의 요약")
    # 피싱(True)일 때만 사용자 대응 안내를 담고, 오탐(False)이면 None이다.
    response: str | None = Field(default=None, description="피싱일 때 사용자에게 전달할 한국어 대응 안내")

    @model_validator(mode="after")
    def _response_matches_verdict(self):
        if self.is_phishing:
            if not (self.response and self.response.strip()):
                raise ValueError("is_phishing=True이면 response가 필요합니다.")
        else:
            if self.response and self.response.strip():
                raise ValueError("is_phishing=False이면 response를 비워야 합니다.")
            # 빈 문자열도 None으로 정규화해 오탐 턴의 응답을 일관되게 비운다.
            self.response = None
        return self


class TurnInput(TypedDict):
    utterance: str | None


class ScamState(TurnInput, total=False):
    transcript: list[str]
    jev_decision: dict | None
    analysis: dict | None


class PipelineError(Exception):
    def __init__(self, stage: str, code: str, message: str):
        super().__init__(message)
        self.stage = stage
        self.code = code
        self.message = message

    def as_dict(self) -> dict[str, str]:
        return {"stage": self.stage, "code": self.code, "message": self.message}


DEMO_UTTERANCES = (
    "오늘 저녁에 같이 밥 먹을까요?",
    "서울중앙지검입니다. 고객님 계좌가 범죄에 연루되었습니다.",
    "수사를 위해 지금 안전계좌로 전액 송금하세요. 다른 사람에게는 알리지 마세요.",
)
