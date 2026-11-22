"""R1~R9와 NEW 묶음(N1~N10)을 행동 특징 F1~F6으로 다시 묶어 출현율과 첫 등장 위치를 낸다.

판단불가 통화는 뺀다. NEW label은 group_new.py의 규칙으로 N 묶음에 배정한 뒤 F에 넣는다.
원문(quote)은 읽지 않고 출력하지 않는다.
출력: experiments/korccvi_tactics/results/features.json
실행: python3 experiments/korccvi_tactics/regroup_features.py
"""
import json
from pathlib import Path

from aggregate import load, pct
from group_new import group_of

OUT = Path(__file__).resolve().parent / "results"

FEATURES = [
    ("F1", "자산 넘기기", {"R1", "R5"}),
    ("F2", "정보 캐기", {"R2", "N4", "R3"}),
    ("F3", "통화 밖 이동", {"R4", "R9"}),
    ("F4", "공포·미끼", {"R6", "N1", "N5", "N6", "N8", "N10"}),
    ("F5", "고립·의심 차단", {"R7", "N7", "N9"}),
    ("F6", "권위·절차 연출", {"R8", "N2", "N3"}),
]
F2_STRONG = {"R2", "N4"}  # 인증·비밀번호·자산 파악. R3(신원정보)는 약한 신호


def element(tactic):
    return group_of(tactic["label"]) if tactic["code"] == "NEW" else tactic["code"]


def main():
    rows, meta = load()
    rows = [r for r in rows if r["type"] != "판단불가"]
    n = len(rows)
    present = {code: 0 for code, _, _ in FEATURES}
    pos = {code: [] for code, _, _ in FEATURES}
    f2_strong = 0
    multi = 0
    for r in rows:
        n_lines = max(meta.get(r["call_id"], {}).get("n_lines", 1), 1)
        elems = [(element(t), t.get("line")) for t in r["tactics"]]
        hit = 0
        for code, _, members in FEATURES:
            lines = [ln for e, ln in elems if e in members]
            if not lines:
                continue
            hit += 1
            present[code] += 1
            ints = [ln for ln in lines if isinstance(ln, int)]
            if ints:
                pos[code].append((min(ints) - 1) / n_lines)
        f2_strong += any(e in F2_STRONG for e, _ in elems)
        multi += hit >= 2

    out = {"calls": n, "excluded": "판단불가", "multi_feature_calls": multi, "multi_feature_pct": pct(multi, n),
           "f2_strong_pct": pct(f2_strong, n), "features": []}
    for code, name, members in FEATURES:
        v = sorted(pos[code])
        out["features"].append({"code": code, "name": name, "elements": sorted(members),
                                "calls": present[code], "calls_pct": pct(present[code], n),
                                "first_pos_median": round(v[len(v) // 2], 2) if v else None})
    OUT.mkdir(exist_ok=True)
    (OUT / "features.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"calls={n} multi={multi}({out['multi_feature_pct']}%) F2강={out['f2_strong_pct']}%")
    for f in out["features"]:
        print(f["code"], f["name"], f["calls_pct"], f["first_pos_median"])


if __name__ == "__main__":
    main()
