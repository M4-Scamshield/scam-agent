from typing import Protocol

from scamshield.state import ScamState


class Roles(Protocol):
    """Single model call per role; not an agent execution runtime."""

    def suspect(self, state: ScamState) -> str: ...

    def verify(self, state: ScamState) -> dict | None: ...


class DemoRoles:
    """Explicit offline substitute; does not demonstrate Gemini calls."""

    def suspect(self, state: ScamState) -> str:
        return "상대방에게 정확한 기관명과 사건번호를 물어보세요. 안내받은 정보는 기관의 공식 연락처로 확인하세요."

    def verify(self, state: ScamState) -> dict | None:
        if any("2026-12345" in utterance for utterance in state["transcript"]):
            return {"tool": "case_lookup", "input": {"case_number": "2026-12345"}}
        return None
