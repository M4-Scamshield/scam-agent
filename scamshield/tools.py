"""F1·F3 Mock tool. 고정 목록으로 조회하며 대화 원문은 받지 않는다.

결과 status는 flagged(위험으로 조회됨), not_found(조회 대상 없음), error(조회 실패)다.
not_found는 안전하다는 뜻이 아니다.
"""

import re
from urllib.parse import urlsplit

# 모두 지어낸 예시 값이다.
FRAUD_ACCOUNTS = {"11122233334444", "99988877776666"}
FLAGGED_DOMAINS = {"safe-account-check.example", "police-case-viewer.example"}
REMOTE_CONTROL_APPS = ("팀뷰어", "teamviewer", "애니데스크", "anydesk", "원격지원", "원격제어", "퀵서포트", "quicksupport")
OFFICIAL_NUMBERS = {
    "금융감독원": {"1332"},
    "경찰청": {"112", "182"},
    "검찰청": {"1301"},
}

_IP_HOST = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


def _digits(value) -> str:
    return re.sub(r"\D", "", value) if isinstance(value, str) else ""


def check_account(account_number: str) -> dict:
    digits = _digits(account_number)
    if not 8 <= len(digits) <= 16:
        return {"status": "error", "detail": "계좌번호 형식을 알 수 없어 조회하지 못했습니다."}
    if digits in FRAUD_ACCOUNTS:
        return {"status": "flagged", "detail": "사기 신고 이력이 있는 계좌입니다."}
    return {"status": "not_found", "detail": "신고 이력이 조회되지 않았습니다. 안전하다는 뜻은 아닙니다."}


def check_url(url: str) -> dict:
    if not isinstance(url, str) or not url.strip():
        return {"status": "error", "detail": "주소가 비어 있어 조회하지 못했습니다."}
    text = url.strip()
    host = (urlsplit(text if "://" in text else "http://" + text).hostname or "").lower()
    if not host:
        return {"status": "error", "detail": "주소 형식을 알 수 없어 조회하지 못했습니다."}
    if host in FLAGGED_DOMAINS or _IP_HOST.match(host):
        return {"status": "flagged", "detail": "피싱 신고 주소이거나 IP 주소로 바로 접속하게 하는 주소입니다."}
    return {"status": "not_found", "detail": "신고 이력이 조회되지 않았습니다. 안전하다는 뜻은 아닙니다."}


def check_app(app_name: str) -> dict:
    if not isinstance(app_name, str) or not app_name.strip():
        return {"status": "error", "detail": "앱 이름이 비어 있어 조회하지 못했습니다."}
    name = app_name.replace(" ", "").lower()
    if any(app in name for app in REMOTE_CONTROL_APPS):
        return {"status": "flagged", "detail": "원격제어 앱입니다.", "remote_control": True}
    return {"status": "not_found", "detail": "원격제어 앱 목록에 없습니다. 안전하다는 뜻은 아닙니다."}


def check_phone(phone_number: str, claimed_institution: str = "") -> dict:
    digits = _digits(phone_number)
    if len(digits) < 3:
        return {"status": "error", "detail": "전화번호 형식을 알 수 없어 조회하지 못했습니다."}
    official = OFFICIAL_NUMBERS.get((claimed_institution or "").strip())
    if official is not None and digits not in official:
        return {"status": "flagged", "detail": f"{claimed_institution} 대표번호({', '.join(sorted(official))})와 다릅니다."}
    return {"status": "not_found", "detail": "대표번호 목록과 비교할 수 없거나 일치합니다. 안전하다는 뜻은 아닙니다."}


TOOL_FUNCTIONS = {
    "check_account": check_account,
    "check_url": check_url,
    "check_app": check_app,
    "check_phone": check_phone,
}

TOOL_SCHEMAS = {
    "check_account": {
        "name": "check_account",
        "description": "대화에 나온 계좌번호가 사기 신고 계좌인지 조회한다. 계좌번호가 대화에 나왔을 때만 부른다.",
        "input_schema": {
            "type": "object",
            "properties": {"account_number": {"type": "string", "description": "대화에 나온 계좌번호"}},
            "required": ["account_number"],
        },
    },
    "check_url": {
        "name": "check_url",
        "description": "대화에서 접속하라고 한 링크·인터넷 주소가 피싱 신고 주소인지 조회한다.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "대화에 나온 주소"}},
            "required": ["url"],
        },
    },
    "check_app": {
        "name": "check_app",
        "description": "대화에서 설치하라고 한 앱이 원격제어 앱인지 조회한다.",
        "input_schema": {
            "type": "object",
            "properties": {"app_name": {"type": "string", "description": "대화에 나온 앱 이름"}},
            "required": ["app_name"],
        },
    },
    "check_phone": {
        "name": "check_phone",
        "description": "대화에서 걸라고 한 전화번호가 상대가 내세운 기관의 대표번호와 같은지 조회한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "phone_number": {"type": "string", "description": "대화에 나온 전화번호"},
                "claimed_institution": {"type": "string", "description": "상대가 내세운 기관 이름(예: 금융감독원)"},
            },
            "required": ["phone_number"],
        },
    },
}

STATE_TOOLS = {"F1": ("check_account",), "F3": ("check_url", "check_app", "check_phone")}


def run_tool(name: str, arguments) -> dict:
    func = TOOL_FUNCTIONS.get(name)
    if func is None or not isinstance(arguments, dict):
        return {"status": "error", "detail": "알 수 없는 조회 요청입니다."}
    try:
        return func(**arguments)
    except TypeError:
        return {"status": "error", "detail": "조회 입력이 잘못되었습니다."}
