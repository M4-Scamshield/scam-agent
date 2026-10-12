from scamshield.state import CaseLookupInput

CASE_LOOKUP_SCHEMA = {
    "name": "case_lookup",
    "description": "대화에서 제시된 사건번호를 데모용 Mock 데이터에서 조회합니다. 실제 기관 조회가 아닙니다.",
    # Gemini ignores additionalProperties; enforce extra="forbid" locally.
    "parameters": {
        key: value
        for key, value in CaseLookupInput.model_json_schema().items()
        if key != "additionalProperties"
    },
}


def case_lookup(case_number: str) -> dict[str, str]:
    """Exact matching against demo fixtures, never a real institution."""
    found = case_number == "2026-00001"
    return {
        "lookup_status": "FOUND" if found else "NOT_FOUND",
        "reason": "데모 Mock 테이블에 등록된 번호입니다."
        if found
        else "데모 Mock 테이블에 등록되지 않은 번호입니다. 실제 기관의 사건 존재 여부는 확인하지 않았습니다.",
    }
