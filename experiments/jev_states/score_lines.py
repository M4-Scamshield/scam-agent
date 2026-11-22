"""window_states.py·prefix_states.py 결과를 대사 단위 KorCCVi 라벨로 채점한다. 집계만 출력한다.

정답: KorCCVi 수법 라벨의 대사 위치(line, 1부터)를 F로 묶는다. 묶는 규칙은 probe_states.gold_of와 같고,
N5(혐의 추궁)는 라벨마다 판단한다. 정상 통화는 모든 대사가 음성이다.

실행:
  .venv/bin/python experiments/jev_states/score_lines.py --window results/window5_dev200_scam40.json \\
    results/window5_dev200_normal20.json --full results/probe_v4_dev200.json --prefix results/prefix_v4_dev200_normal_fp.json
"""
import argparse
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from probe_states import FEATURES, GOLD_EXCLUDE, N5_ACCUSE, STATES, element, load  # noqa: E402

CORE = ("F1", "F2", "F4", "F6")  # F3·F5만 켜진 동안은 LLM을 부르지 않는다(spec 2026-11-19)


def line_gold():
    """call_id → {F: 정답 대사 번호 집합}"""
    rows, _ = load()
    out = {}
    for r in rows:
        if r["type"] == "판단불가":
            continue
        has_r1 = any(element(t) == "R1" for t in r["tactics"])
        g = collections.defaultdict(set)
        for t in r["tactics"]:
            e = element(t)
            if (e == "N6" and not has_r1) or (e == "N5" and not N5_ACCUSE.search(t["label"])):
                continue
            for code, _, members in FEATURES:
                if e in members - GOLD_EXCLUDE.get(code, set()):
                    g[code].add(t["line"])
        out[r["call_id"]] = g
    return out


def yes_lines(call):
    """{F: Yes인 대사 번호 목록}. 오류 난 대사는 뺀다."""
    return {s: [st["k"] for st in call["steps"] if "answers" in st and st["answers"][s]["verdict"] == "Yes"]
            for s in STATES}


def llm_calls(call):
    """라우팅(spec)대로 부를 상태 LLM 횟수. 창 방식은 Yes가 난 대사마다, 누적 방식은 상태가 처음 켜질 때 한 번."""
    n, held, core_on, seen = 0, 0, False, set()
    for st in call["steps"]:
        if "answers" not in st:
            continue
        on = {s for s in STATES if st["answers"][s]["verdict"] == "Yes"}
        new = on if call["_mode"] == "window" else on - seen
        seen |= on
        if not core_on and on & set(CORE):
            core_on, n = True, n + held
        if core_on:
            n += len(new)
        else:
            held += len(new)
    return n


def pct(a, b):
    return f"{a}/{b} ({100 * a / b:.0f}%)" if b else "0/0"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--window", nargs="+", required=True)
    p.add_argument("--full", required=True, help="통화 전체 1회 판단 결과(probe_states.py)")
    p.add_argument("--prefix", help="정상 통화 누적 방식 결과(prefix_states.py)")
    p.add_argument("--tol", type=int, default=1, help="정답 대사 ±tol 안에서 Yes면 맞춘 것으로 본다")
    args = p.parse_args()
    rd = lambda f: json.loads((HERE / f if not Path(f).exists() else Path(f)).read_text(encoding="utf-8"))
    win = [c | {"_mode": "window"} for f in args.window for c in rd(f)["calls"]]
    full = {c["call_id"]: c for c in rd(args.full)["calls"]}
    pre = {c["call_id"]: c | {"_mode": "prefix"} for c in rd(args.prefix)["calls"]} if args.prefix else {}
    gold = line_gold()
    scams = [c for c in win if c["scam"]]
    normals = [c for c in win if not c["scam"]]
    print(f"창 결과: 사기 {len(scams)}, 정상 {len(normals)}, 오류 대사 {sum('error' in s for c in win for s in c['steps'])}")

    print(f"\n[사기] 대사 단위 정답 ±{args.tol}줄 재현율 / 정답 근처 밖 Yes 대사 / 첫 감지 지연(중앙값, 줄)")
    for s in STATES:
        hit = tot = extra = 0
        delays = []
        for c in scams:
            g, y = gold[c["call_id"]].get(s, set()), yes_lines(c)[s]
            tot += len(g)
            hit += sum(any(abs(k - l) <= args.tol for k in y) for l in g)
            extra += sum(all(abs(k - l) > args.tol for l in g) for k in y)
            if g and y:
                delays.append(min(y) - min(g))
        med = sorted(delays)[len(delays) // 2] if delays else "-"
        print(f"  {s}: 재현 {pct(hit, tot)}  밖 Yes {extra}  지연 {med}")

    print("\n[사기] 통화 단위 — 창(한 대사라도 Yes) vs 전체 1회. 재현율 / 정답 없는 통화의 Yes")
    for s in STATES:
        pos = [c for c in scams if s in c["gold"]]
        neg = [c for c in scams if s not in c["gold"]]
        w = lambda cs: sum(bool(yes_lines(c)[s]) for c in cs)
        f = lambda cs: sum(full[c["call_id"]]["answers"][s]["verdict"] == "Yes" for c in cs)
        print(f"  {s}: 창 {pct(w(pos), len(pos))} / {pct(w(neg), len(neg))}   전체 {pct(f(pos), len(pos))} / {pct(f(neg), len(neg))}")
    any_w = sum(any(yes_lines(c)[s] for s in STATES) for c in scams)
    print(f"  상태 하나라도: 창 {pct(any_w, len(scams))}")

    print("\n[정상] 상태가 켜진 통화 / Yes 대사 비율 — 창 vs 누적(같은 통화)")
    for s in STATES:
        wc = sum(bool(yes_lines(c)[s]) for c in normals)
        wl = sum(len(yes_lines(c)[s]) for c in normals)
        nl = sum(c["n_lines"] for c in normals)
        line = f"  {s}: 창 통화 {pct(wc, len(normals))} 대사 {pct(wl, nl)}"
        if pre:
            ps = [pre[c["call_id"]] for c in normals]
            pc = sum(bool(yes_lines(c)[s]) for c in ps)
            pl = sum(len(yes_lines(c)[s]) for c in ps)
            line += f"   누적 통화 {pct(pc, len(ps))} 대사 {pct(pl, nl)}"
        print(line)

    print("\n[LLM 호출 수] 통화당 평균 (F3·F5 단독 보류 적용)")
    for name, cs in (("사기", scams), ("정상", normals)):
        if not cs:
            continue
        print(f"  {name} 창: {sum(map(llm_calls, cs)) / len(cs):.1f}", end="")
        if name == "정상" and pre:
            print(f"   누적: {sum(llm_calls(pre[c['call_id']]) for c in cs) / len(cs):.1f}", end="")
        print()


if __name__ == "__main__":
    main()
