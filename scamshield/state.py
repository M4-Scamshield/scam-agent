from typing import Any, Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field, field_validator

Phase = Literal["OBSERVE", "SUSPECT", "VERIFY", "WARN"]


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class CaseLookupInput(ContractModel):
    case_number: str

    @field_validator("case_number")
    @classmethod
    def nonempty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("case_number must not be blank")
        return value


class CaseLookupResult(ContractModel):
    lookup_status: Literal["FOUND", "NOT_FOUND"]
    reason: str = Field(min_length=1)


class ToolRequest(ContractModel):
    tool: Literal["case_lookup"]
    input: CaseLookupInput


class VerificationResult(TypedDict):
    tool: str
    input: dict[str, Any]
    status: Literal["OK", "ERROR", "TIMEOUT"]
    result: dict[str, Any]
    is_mock: bool


class JevDecision(ContractModel):
    risk: float = Field(ge=0, le=1, allow_inf_nan=False)
    phase: Phase


class TurnInput(TypedDict):
    utterance: str | None


class ScamState(TurnInput, total=False):
    transcript: list[str]
    phase: Phase
    risk: float | None
    verification_results: list[VerificationResult]
    response: str | None
    tool_request: dict[str, Any] | None
    verification_attempted: bool


class DemoError(Exception):
    def __init__(self, stage: str, code: str, message: str):
        super().__init__(message)
        self.stage = stage
        self.code = code
        self.message = message

    def as_dict(self) -> dict[str, str]:
        return {"stage": self.stage, "code": self.code, "message": self.message}


WARN_RESPONSE = "현재 통화는 보이스피싱일 가능성이 매우 높습니다. 송금, 개인정보 제공, 앱 설치를 중단하고 통화를 종료하세요."
NO_TOOL_RESPONSE = "현재 정보로는 조회할 대상을 정하기 어렵습니다. 상대방에게 기관명과 확인 가능한 정보를 요청하세요."
VERIFY_RESPONSE = "확인한 결과만으로는 판단하기 어렵습니다. 상대방의 주장을 추가로 확인하고, 확인 전 송금이나 개인정보 제공을 보류하세요."

DEMO_UTTERANCES = (
    "안녕하세요. 서울중앙지검입니다.",
    "고객님 계좌가 범죄에 연루되었습니다.",
    "사건번호는 2026-12345입니다.",
)
