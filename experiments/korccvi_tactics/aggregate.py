"""라벨링 결과(data/korccvi_tactics/annotations/*.jsonl)를 유형·수법별로 집계한다.

원문(quote)은 출력하지 않는다. 저장소에 남기는 결과는 집계 수치와 paraphrase 뿐이다.
출력: experiments/korccvi_tactics/results/summary.json, NEW 수법 label 목록(results/new_labels.txt)

실행: python3 experiments/korccvi_tactics/aggregate.py
"""
import collections
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ANN = REPO / "data" / "korccvi_tactics" / "annotations"
META = REPO / "data" / "korccvi_tactics" / "calls.json"
OUT = Path(__file__).resolve().parent / "results"
CODES = ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "NEW"]


def load():
    rows = [json.loads(line) for f in sorted(ANN.glob("batch_*.jsonl")) for line in open(f, encoding="utf-8") if line.strip()]
    meta = {m["call_id"]: m for m in json.load(open(META, encoding="utf-8"))}
    return rows, meta


def pct(n, d):
    return round(100 * n / d, 1) if d else 0.0


def main():
    rows, meta = load()
    ids = [r["call_id"] for r in rows]
    assert len(ids) == len(set(ids)), "call_id 중복"
    missing = sorted(set(meta) - set(ids))
    by_type = collections.defaultdict(list)
    for r in rows:
        by_type[r["type"]].append(r)

    summary = {"calls": len(rows), "missing": missing,
               "diarization_ok": sum(bool(r.get("diarization_ok")) for r in rows),
               "title_matches": collections.Counter(str(r.get("title_matches")) for r in rows),
               "overall": {}, "types": {}}

    def profile(rs):
        n = len(rs)
        present = {c: sum(any(t["code"] == c for t in r["tactics"]) for r in rs) for c in CODES}
        # 수법이 처음 나온 상대 위치(0=통화 시작, 1=끝). 통화 줄 수로 나눈다
        pos = collections.defaultdict(list)
        orders = collections.Counter()
        for r in rs:
            n_lines = max(meta.get(r["call_id"], {}).get("n_lines", 1), 1)
            first = {}
            for t in r["tactics"]:
                if isinstance(t.get("line"), int):
                    first[t["code"]] = min(first.get(t["code"], t["line"]), t["line"])
            for c, ln in first.items():
                pos[c].append((ln - 1) / n_lines)
            seq = [c for c, _ in sorted(first.items(), key=lambda kv: kv[1]) if c != "NEW"]
            if seq:
                orders["→".join(seq[:4])] += 1
        median = {c: round(sorted(v)[len(v) // 2], 2) for c, v in pos.items() if v}
        labels = {c: collections.Counter(t["label"] for r in rs for t in r["tactics"] if t["code"] == c).most_common(12)
                  for c in CODES}
        return {"n": n, "present": present, "present_pct": {c: pct(v, n) for c, v in present.items()},
                "first_pos_median": median, "top_orders": orders.most_common(8),
                "impersonated": collections.Counter(r.get("impersonated") or "" for r in rs).most_common(10),
                "multi_scammer": sum(len(r.get("scammer_speakers") or []) > 1 for r in rs),
                "labels": labels}

    summary["overall"] = profile(rows)
    for ty, rs in sorted(by_type.items(), key=lambda kv: -len(kv[1])):
        summary["types"][ty] = profile(rs)

    OUT.mkdir(exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    new = collections.Counter((r["type"], t["label"]) for r in rows for t in r["tactics"] if t["code"] == "NEW")
    (OUT / "new_labels.txt").write_text(
        "\n".join(f"{n}\t{ty}\t{lab}" for (ty, lab), n in new.most_common()) + "\n", encoding="utf-8")

    print(f"calls={len(rows)} missing={len(missing)} types=" +
          ", ".join(f"{t}:{len(v)}" for t, v in sorted(by_type.items(), key=lambda kv: -len(kv[1]))))
    print("code  " + " ".join(f"{c:>5}" for c in CODES))
    for ty, p in [("전체", summary["overall"])] + list(summary["types"].items()):
        print(f"{ty[:10]:<10} n={p['n']:<4}" + " ".join(f"{p['present_pct'][c]:>5}" for c in CODES))


if __name__ == "__main__":
    main()
