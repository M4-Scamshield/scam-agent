"""새로 작성한 면접 대본을 정답과 분리해 고정한다. API 호출 없음.

scenarios.txt: label|scenario|evidence turn numbers|rationale, 이후 교대 발화.
기존 합성 생성기를 import하거나 기존 문답을 끼워 넣지 않는다.
"""

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import random
import re

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "datasets/interview_holdout"
CSV = ROOT / "experiments/data/interview_holdout_100.csv"
SEED = 261114


def digest(data):
    return hashlib.sha256(data).hexdigest()


def norm(text):
    return re.sub(r"[^가-힣a-z0-9]", "", text.lower())


def encode(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode()


def build():
    source = (DEST / "scenarios.txt").read_text(encoding="utf-8")
    calls = []
    balance = Counter()
    for block in source.strip().split("\n\n"):
        lines = block.splitlines()
        label, scenario, evidence, rationale = lines[0].split("|", 3)
        assert label in ("phishing", "normal"), label
        turns = lines[1:]
        assert 8 <= len(turns) <= 18, (scenario, len(turns))
        assert all(t.strip() == t and t for t in turns)
        evidence = [int(x) for x in evidence.split(",") if x.strip()]
        assert (label == "phishing") == bool(evidence), scenario
        assert all(1 <= e <= len(turns) and e % 2 == 1 for e in evidence)
        # 각 클래스에서 면접관=A/B가 각각 25건, 역할은 입력에 쓰지 않는다.
        flip = balance[label] % 2
        balance[label] += 1
        utterances = [
            {"turn_id": i + 1, "speaker": "AB"[(i + flip) % 2], "text": t}
            for i, t in enumerate(turns)
        ]
        calls.append({"source_id": f"script_{len(calls) + 1:03d}", "label": label,
                      "scenario": scenario, "rationale": rationale,
                      "evidence_turn_ids": evidence, "utterances": utterances})
    assert balance == {"phishing": 50, "normal": 50}, balance
    assert len({c["scenario"] for c in calls}) == 100
    random.Random(SEED).shuffle(calls)
    inputs, answers = [], []
    buf = io.StringIO(newline="")
    writer = csv.writer(buf)
    writer.writerow(["id", "transcript", "label"])
    for i, call in enumerate(calls, 1):
        call_id = f"holdout_{i:03d}"
        inputs.append({"call_id": call_id, "utterances": call["utterances"]})
        answers.append({"call_id": call_id, **{k: v for k, v in call.items() if k != "utterances"}})
        transcript = "\n".join(f"{u['speaker']}: {u['text']}" for u in call["utterances"])
        writer.writerow([call_id, transcript, int(call["label"] == "phishing")])
    # 기존 대본과 비교: 화자 표기를 제외한 전체 대화, 긴 개별 발화의 정확 일치.
    old_calls = []
    for name in ("phishing", "normal"):
        path = ROOT / f"datasets/interview_{name}/interview_{name}_100.json"
        old_calls.extend(json.loads(path.read_text())["calls"])
    full = lambda c: norm("".join(u["text"] for u in c["utterances"]))
    old_full = {full(c) for c in old_calls}
    old_turns = {norm(u["text"]) for c in old_calls for u in c["utterances"] if len(norm(u["text"])) >= 15}
    new_full = [full(c) for c in inputs]
    repeated = [u["text"] for c in inputs for u in c["utterances"]
                if len(norm(u["text"])) >= 15 and norm(u["text"]) in old_turns]
    assert len(set(new_full)) == 100, "duplicate new calls"
    assert not set(new_full) & old_full, "old full call reused"
    assert not repeated, ("old long utterances reused", repeated)
    # 두 클래스의 새 대본에서 같은 긴 발화를 돌려 쓰지 않는다.
    long_turns = [norm(u["text"]) for c in inputs for u in c["utterances"] if len(norm(u["text"])) >= 15]
    assert len(long_turns) == len(set(long_turns)), "new long utterance repeated"
    assert all(set(c) == {"call_id", "utterances"} for c in inputs)
    assert all(set(u) == {"turn_id", "speaker", "text"} and u["speaker"] in "AB"
               for c in inputs for u in c["utterances"])
    outputs = {DEST / "inputs.json": encode({"calls": inputs}),
               DEST / "answers.json": encode({"calls": answers}),
               CSV: buf.getvalue().encode("utf-8-sig")}
    report = {
        "seed": SEED, "calls": len(calls), "labels": dict(balance),
        "turns": sum(len(c["utterances"]) for c in calls),
        "turn_count_distribution": dict(sorted(Counter(len(c["utterances"]) for c in calls).items())),
        "old_full_call_duplicates": 0, "old_long_utterance_exact_matches": 0,
        "new_long_utterance_duplicates": 0, "long_utterance_min_normalized_chars": 15,
        "interviewer_speaker_counts": {label: dict(Counter(c["utterances"][0]["speaker"]
             for c in calls if c["label"] == label)) for label in balance},
        "sha256": {str(p.relative_to(ROOT)): digest(b) for p, b in outputs.items()},
        "source_sha256": digest((DEST / "scenarios.txt").read_bytes()),
        "limitations": ["동일 에이전트 작성·라벨링; 독립적인 사람 검수 없음",
                        "Exact-match checks do not prove semantic independence or model-training absence",
                        "8–18 turns, not the original 50–100 sentence condition; synthetic text only"],
    }
    # JSON 재로딩 후에도 같은 보고서가 되도록 키 형식을 맞춘다.
    report = json.loads(encode(report))
    outputs[DEST / "validation_report.json"] = encode(report)
    return outputs, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs, report = build()
    for path, data in outputs.items():
        if args.check:
            assert path.read_bytes() == data, f"stored file mismatch: {path}"
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
