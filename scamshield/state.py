from typing import Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field


class JevDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    verdict: Literal["Yes", "No"]
    # Always P(voice phishing / Yes), including when verdict is No.
    probability: float = Field(ge=0, le=1, allow_inf_nan=False)


class LLMAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)

    reason: str = Field(min_length=1, description="대화에 근거한 탐지 이유와 불확실성의 요약")
    response: str = Field(min_length=1, description="사용자에게 전달할 한국어 대응 안내")


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
