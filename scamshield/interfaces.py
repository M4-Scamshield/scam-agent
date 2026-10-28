from typing import Protocol

from scamshield.state import ScamState


class Detector(Protocol):
    def detect(self, transcript: list[str]) -> dict:
        """Return {verdict: Yes | No, probability: P(Yes)}."""
        ...


class Analyst(Protocol):
    def analyze(self, state: ScamState) -> dict:
        """Read transcript and Jev decision; return {reason, response}."""
        ...


class OfflineDetector:
    """Demo-only rule; never a fallback for a failed real Jev call."""

    def detect(self, transcript: list[str]) -> dict:
        suspicious = any(
            any(word in utterance for word in ("범죄에 연루", "안전계좌", "송금"))
            for utterance in transcript
        )
        return {"verdict": "Yes" if suspicious else "No", "probability": 0.9 if suspicious else 0.1}


class OfflineAnalyst:
    """Fixed output for offline wiring checks, not model analysis."""

    def analyze(self, state: ScamState) -> dict:
        return {
            "reason": "[OFFLINE 대역] 준비된 의심 문구 규칙으로 Yes 경로를 확인했습니다.",
            "response": "[OFFLINE 대역] 송금과 개인정보 제공을 보류하고 기관의 공식 연락처로 확인하세요.",
        }
