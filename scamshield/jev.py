from scamshield.state import JevDecision, Phase, VerificationResult


def fake_jev(
    transcript: list[str],
    previous_phase: Phase,
    verification_results: list[VerificationResult],
) -> dict:
    """Rules for the prepared dialogue only; no detection accuracy claim."""
    phase: Phase = "OBSERVE"
    conversation = "\n".join(transcript)
    suspicious = "서울중앙지검" in conversation and any(
        all(word in utterance for word in ("계좌", "범죄", "연루"))
        for utterance in transcript
    )
    if previous_phase == "WARN":
        phase = "WARN"
    elif suspicious:
        phase = "SUSPECT"
        if "2026-12345" in conversation:
            phase = "VERIFY"
            latest = next(
                (
                    result
                    for result in reversed(verification_results)
                    if result["tool"] == "case_lookup"
                    and result["input"].get("case_number") == "2026-12345"
                ),
                None,
            )
            if latest and latest["status"] == "OK" and latest["is_mock"]:
                lookup_status = latest["result"].get("lookup_status")
                if lookup_status == "NOT_FOUND":
                    phase = "WARN"
                elif lookup_status == "FOUND":
                    phase = "SUSPECT"
    risks = {"OBSERVE": 0.1, "SUSPECT": 0.5, "VERIFY": 0.7, "WARN": 0.9}
    return JevDecision(phase=phase, risk=risks[phase]).model_dump()
