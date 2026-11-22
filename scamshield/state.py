from typing import Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field, field_validator

StateCode = Literal["F1", "F2", "F3", "F4", "F5", "F6"]


class JevDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    verdict: Literal["Yes", "No"]
    # Always P(Yes), including when verdict is No.
    probability: float = Field(ge=0, le=1, allow_inf_nan=False)


class NewLine(BaseModel):
    seq: int
    # "[화자] 발화"
    text: str = Field(min_length=1)


class ToolRecord(BaseModel):
    name: str
    status: Literal["flagged", "not_found", "error"]


def _none_to_empty(value):
    return "" if value is None else value


class CallContext(BaseModel):
    purpose: str = ""
    claimed_identity: str = ""

    _empty = field_validator("purpose", "claimed_identity", mode="before")(_none_to_empty)


class StateJudgment(BaseModel):
    """상태별 Haiku 출력. tools는 Haiku가 부른 tool의 결과 상태다(입력값은 남기지 않는다)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    judgment: Literal["risky", "within_normal", "uncertain"]
    absolute_line: bool = False
    reason: str = Field(min_length=1)
    response: str = ""
    actions: list[str] = []
    call_context: CallContext = CallContext()
    tools: list[ToolRecord] = []

    # 저노력 Haiku가 null이나 객체 항목을 내도 그 상태를 버리지 않는다.
    _empty = field_validator("response", mode="before")(_none_to_empty)

    @field_validator("call_context", mode="before")
    @classmethod
    def _context(cls, value):
        return {} if value is None else value

    @field_validator("actions", mode="before")
    @classmethod
    def _actions(cls, value):
        return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


class StateAnalysis(BaseModel):
    """이번 요청에서 부른 상태의 보정 후 판단."""

    state: str
    judgment: Literal["risky", "within_normal", "uncertain"]
    # 보정 전 Haiku 판단과 보정 이유("absolute_line", "tool_flagged")
    model_judgment: Literal["risky", "within_normal", "uncertain"]
    corrections: list[str]
    reason: str
    response: str
    actions: list[str]
    tools: list[ToolRecord]


class Handled(BaseModel):
    judgment: Literal["risky", "within_normal", "uncertain"]
    reason: str
    response: str
    actions: list[str]
    evidence_seqs: list[int]
    judged_at: float


class Held(BaseModel):
    probability: float
    seqs: list[int]
    # 대화상 줄 번호(1부터). 보류했다 부를 때 Haiku에게 감지된 대사를 가리킨다.
    lines: list[int] = []


class AgentMemory(BaseModel):
    """요청 사이에 넘기는 agent 상태. AnalysisOutcome.state로 나가고 다음 요청의 state로 돌아온다."""

    handled: dict[StateCode, Handled] = {}
    call_context: CallContext = CallContext()
    seen: list[StateCode] = []
    held: dict[StateCode, Held] = {}


class AnalysisOutcome(BaseModel):
    status: Literal["위험", "주의", "정상"]
    score: int = Field(ge=0, le=100)
    message: str | None
    reason: str | None
    evidence_seqs: list[int]
    states: dict[str, JevDecision]
    state_analyses: list[StateAnalysis]
    state: dict


class AnalyzeInput(TypedDict):
    history: list[str]
    new_lines: list[dict]
    memory: dict
    now: float


class AgentState(AnalyzeInput, total=False):
    lines: list[str]
    states: dict
    todo: dict
    state_analyses: list[dict]
    outcome: dict


class PipelineError(Exception):
    def __init__(self, stage: str, code: str, message: str):
        super().__init__(message)
        self.stage = stage
        self.code = code
        self.message = message

    def as_dict(self) -> dict[str, str]:
        return {"stage": self.stage, "code": self.code, "message": self.message}


DEMO_UTTERANCES = (
    "[상대] 오늘 저녁에 같이 밥 먹을까요?",
    "[상대] 서울중앙지검입니다. 고객님 계좌가 범죄에 연루되었습니다.",
    "[상대] 수사를 위해 지금 안전계좌로 전액 송금하세요. 다른 사람에게는 알리지 마세요.",
)
