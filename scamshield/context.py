"""전체 대화의 줄 위치와 서버 seq를 대응시킨다. 원문은 호출자가 보관한다."""

from hashlib import sha256

from pydantic import TypeAdapter

from scamshield.llm import AnalystError
from scamshield.state import NewLine, StateJudgment
from scamshield.tactics import ABSOLUTE_STATES

_HISTORY = TypeAdapter(list[str | NewLine])


def prepare_context(history, new_lines: list[dict], memory: dict) -> tuple[list[str], list[int | None]]:
    rows = _HISTORY.validate_python(history)
    old_refs = memory["line_refs"]
    if old_refs and len(old_refs) != len(rows):
        raise ValueError("history and state length mismatch")
    refs, texts = [], []
    for index, row in enumerate(rows):
        text = row if isinstance(row, str) else row.text
        fingerprint = sha256(text.encode("utf-8")).hexdigest()
        seq = None if isinstance(row, str) else row.seq
        if old_refs:
            previous = old_refs[index]
            if previous["fingerprint"] != fingerprint or (seq is not None and previous["seq"] not in (None, seq)):
                raise ValueError("history and state content mismatch")
            seq = seq if seq is not None else previous["seq"]
        texts.append(text)
        refs.append({"seq": seq, "fingerprint": fingerprint})
    all_seqs = [ref["seq"] for ref in refs if ref["seq"] is not None] + [line["seq"] for line in new_lines]
    if len(set(all_seqs)) != len(all_seqs) or all_seqs != sorted(all_seqs):
        raise ValueError("transcript seq must be unique and increasing")
    for line in new_lines:
        if not line["text"].strip():
            raise ValueError("empty utterance")
        refs.append({"seq": line["seq"], "fingerprint": sha256(line["text"].encode("utf-8")).hexdigest()})
    memory["line_refs"] = refs
    return texts, [ref["seq"] for ref in refs]


def validate_evidence(result: StateJudgment, request: dict) -> StateJudgment:
    """위험 근거를 묶음 전체로 대체하지 않는다. 실제 줄·원래 seq만 허용한다."""
    evidence = sorted(set(result.evidence_lines))
    context = sorted(set(result.context_lines) - set(evidence))
    risky = result.judgment == "risky" or (
        request["state"] in ABSOLUTE_STATES and result.absolute_line
    ) or any(tool.status == "flagged" for tool in result.tools)
    if risky and not evidence:
        raise AnalystError("INVALID_EVIDENCE")
    for position in evidence + context:
        if position > len(request["lines"]) or request["line_seqs"][position - 1] is None:
            raise AnalystError("INVALID_EVIDENCE")
    return result.model_copy(update={"evidence_lines": evidence, "context_lines": context})
