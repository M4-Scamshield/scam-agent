from typing import Protocol

from scamshield.tactics import STATES


class Detector(Protocol):
    def detect_states(self, lines: list[str], n_new: int) -> dict:
        """Return {F1..F6: {verdict: Yes | No, probability: P(Yes)}} for the last n_new lines."""
        ...


class Analyst(Protocol):
    def judge(self, request: dict) -> dict:
        """Judge one state; return StateJudgment fields. Raise PipelineError only for auth failure."""
        ...


OFFLINE_KEYWORDS = {
    "F1": ("송금", "이체", "보내"),
    "F2": ("인증번호", "비밀번호", "OTP"),
    "F3": ("설치", "링크", "접속"),
    "F4": ("연루", "동결", "처벌"),
    "F5": ("알리지", "비밀"),
    "F6": ("지검", "검찰", "경찰", "금융감독원"),
}


class OfflineDetector:
    """Demo-only keyword rule; never a fallback for a failed real Jev call."""

    def detect_states(self, lines: list[str], n_new: int) -> dict:
        new = lines[-n_new:]
        result = {}
        for code in STATES:
            hit = any(word in line for line in new for word in OFFLINE_KEYWORDS[code])
            result[code] = {"verdict": "Yes" if hit else "No", "probability": 0.9 if hit else 0.1}
        return result


class OfflineAnalyst:
    """Fixed output for offline wiring checks, not model analysis: F1·F2 risky, others uncertain."""

    def judge(self, request: dict) -> dict:
        risky = request["state"] in ("F1", "F2")
        return {
            "judgment": "risky" if risky else "uncertain",
            "absolute_line": False,
            "reason": f"[OFFLINE 대역] {request['state']} 고정 판단으로 경로를 확인했습니다.",
            "response": "[OFFLINE 대역] 송금과 개인정보 제공을 멈추고 기관의 공식 대표번호로 확인하세요." if risky else "",
            "actions": [],
            "call_context": {"purpose": "", "claimed_identity": ""},
            "tools": [],
        }
