"""Jev 단독 실험 공용 유틸.

서비스 Graph/State를 바꾸지 않고, Jev(TypeSafe System One) 단독 호출로
보이스피싱 탐지 성능을 측정하기 위한 공통 코드다. Plan1/Plan2가 함께 쓴다.

- 데이터 로딩(KorCCVi CSV: id, transcript, label[0/1])
- TypeSafe System One 호출(임의 questions, 429 지수 백오프 재시도)
- Confusion Matrix·Accuracy·Precision·Recall 계산과 Markdown 표 렌더링
"""

import csv
import json
import os
import pathlib
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# 저장소 루트를 import 경로에 추가해 scamshield 설정·프롬프트를 재사용한다.
_REPO = pathlib.Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

DEFAULT_BASE_URL = "https://api.typesafe.ai"
DEFAULT_MODEL = "jev-latest"
DATA_PATH = _REPO / "experiments" / "data" / "KorCCVi_v2_cleaned.csv"


def inject_truststore() -> bool:
    """TLS 가로채기 환경에서 OS 인증서 저장소를 쓰도록 주입한다. 없으면 무시."""
    try:
        import truststore

        truststore.inject_into_ssl()
        return True
    except Exception:
        return False


class JevError(Exception):
    """호출 실패를 지표와 분리해 집계하기 위한 오류(코드 보존)."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def load_dataset(path=DATA_PATH, limit=None, shuffle=False, seed=0):
    """CSV를 읽어 [{id, transcript(str), gold(bool)}] 로 반환. gold=label==1."""
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            label = (r.get("label") or "").strip()
            rows.append(
                {
                    "id": (r.get("id") or "").strip(),
                    "transcript": r.get("transcript") or "",
                    "gold": label == "1",
                }
            )
    if shuffle:
        import random

        random.Random(seed).shuffle(rows)
    if limit is not None:
        rows = rows[:limit]
    return rows


def _config():
    api_key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if not api_key:
        raise JevError("MISSING_API_KEY", "TYPESAFE_API_KEY 환경변수가 필요합니다.")
    base_url = os.environ.get("TYPESAFE_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")
    model = os.environ.get("TYPESAFE_DEFAULT_MODEL", DEFAULT_MODEL).strip()
    return api_key, base_url, model


def ask(questions: dict, transcript, *, timeout=30, max_retries=5, base_delay=2.0) -> dict:
    """System One에 questions를 보내고 {key: {"verdict","probability"}}를 반환.

    questions: {key: {"type":"choice","instructions":str,"criteria":{"Yes","No"}}}
    429는 지수 백오프로 재시도하고, 그 외 오류는 JevError로 올린다.
    """
    api_key, base_url, model = _config()
    body = json.dumps(
        {"model": model, "state": {"transcript": transcript}, "questions": questions},
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    headers = {"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}

    attempt = 0
    while True:
        request = Request(base_url + "/v1/systemone", data=body, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=timeout) as response:
                raw = json.load(response)
            break
        except HTTPError as exc:
            if exc.code == 429 and attempt < max_retries:
                time.sleep(base_delay * (2 ** attempt))
                attempt += 1
                continue
            raise JevError(f"HTTP_{exc.code}", f"Jev HTTP {exc.code}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            if attempt < max_retries:
                time.sleep(base_delay * (2 ** attempt))
                attempt += 1
                continue
            raise JevError("CONN_FAILED", "Jev 연결/응답 대기 실패") from exc
        except (ValueError, UnicodeError) as exc:
            raise JevError("BAD_JSON", "Jev 응답이 유효한 JSON이 아님") from exc

    try:
        answers = raw["answers"]
        out = {}
        for key, ans in answers.items():
            prob = float(ans["probabilities"]["Yes"])
            out[key] = {"verdict": ans["choice"], "probability": prob}
        return out
    except (KeyError, TypeError, ValueError) as exc:
        raise JevError("BAD_OUTPUT", "Jev 응답 형식이 예상과 다름") from exc


# --- 지표 ---------------------------------------------------------------

def confusion(pairs):
    """pairs: [(gold_yes bool, pred_yes bool)] -> {tp,fp,tn,fn}. 양성=Yes(보이스피싱)."""
    tp = fp = tn = fn = 0
    for gold, pred in pairs:
        if gold and pred:
            tp += 1
        elif gold and not pred:
            fn += 1
        elif not gold and pred:
            fp += 1
        else:
            tn += 1
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def metrics(cm):
    tp, fp, tn, fn = cm["tp"], cm["fp"], cm["tn"], cm["fn"]
    total = tp + fp + tn + fn
    acc = (tp + tn) / total if total else 0.0
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return {"accuracy": acc, "precision": prec, "recall": rec, "f1": f1, "n": total}


def render_confusion_md(cm):
    return (
        "|            | 예측 Yes | 예측 No |\n"
        "|------------|---------|--------|\n"
        f"| **실제 Yes** | {cm['tp']} (TP) | {cm['fn']} (FN) |\n"
        f"| **실제 No**  | {cm['fp']} (FP) | {cm['tn']} (TN) |\n"
    )


def render_metrics_md(m):
    return (
        f"- 평가 샘플 수(실패 제외): **{m['n']}**\n"
        f"- Accuracy: **{m['accuracy']:.4f}**\n"
        f"- Precision: **{m['precision']:.4f}**\n"
        f"- Recall: **{m['recall']:.4f}**\n"
        f"- F1: {m['f1']:.4f}\n"
    )


def write_text(out_dir, name, text):
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    path.write_text(text, encoding="utf-8")
    return path
