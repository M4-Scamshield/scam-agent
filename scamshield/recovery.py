"""분석 시도 한 번 + 최대 세 번 재시도. 진행 이벤트에는 원문을 넣지 않는다."""

import re
from time import sleep

from pydantic import ValidationError

from scamshield.llm import AnalystError
from scamshield.state import AnalysisFailure, AnalysisProgress, PipelineError

MAX_RETRIES = 3
RETRY_DELAYS_S = (0.5, 1.0, 2.0)
_RETRYABLE = {"TIMEOUT", "CONNECTION_FAILED", "CALL_FAILED", "INVALID_OUTPUT", "INVALID_EVIDENCE"}
_FATAL = {"AUTH_FAILED", "REQUEST_REJECTED", "MISSING_API_KEY", "INVALID_CONFIG"}


def attempt_analysis(operation, *, stage, seqs, emit, state=None, retry_wait=None):
    """독립된 분석 작업만 재시도한다. 성공한 다른 상태와 transcript는 건드리지 않는다."""
    wait = retry_wait or sleep
    for attempt in range(1, MAX_RETRIES + 2):
        emit(AnalysisProgress(status="analyzing", stage=stage, state=state, attempt=attempt, seqs=seqs))
        try:
            return operation(), None
        except ValidationError:
            code = "INVALID_OUTPUT"
        except (AnalystError, PipelineError) as exc:
            code = exc.code
            if code not in _RETRYABLE | _FATAL and not re.fullmatch(r"HTTP_\d{3}", code):
                code = "INTERNAL_ERROR"
        except Exception:
            # 알 수 없는 버그나 콜백/모델의 민감한 예외 메시지를 외부로 내보내지 않는다.
            code = "INTERNAL_ERROR"
        retryable = code in _RETRYABLE or code == "HTTP_429" or bool(re.fullmatch(r"HTTP_5\d\d", code))
        if not retryable or attempt == MAX_RETRIES + 1:
            return None, AnalysisFailure(stage=stage, state=state, code=code, attempts=attempt, seqs=seqs)
        wait(RETRY_DELAYS_S[attempt - 1])
