"""통화 대사를 1줄, 2줄, …로 쌓아 Jev 상태 질문을 보내고 상태가 처음 켜지는 대사를 찾는다.

실제 서비스처럼 대사가 쌓일 때의 판단을 본다. 질문은 probe_states.py(v4)와 같다.
입력: probe_states.py 결과 파일(--from)과 그 통화의 대본(data/, Git 제외)
출력: experiments/jev_states/results/<--out-name> — call_id·대사 수별 상태 판단·확률·토큰만 쓴다. 대본은 쓰지 않는다.

실행:
  python3 experiments/jev_states/prefix_states.py --from experiments/jev_states/results/probe_v4_dev200.json --dry-run
  set -a && . ./.env && set +a && .venv/bin/python -X utf8 experiments/jev_states/prefix_states.py \
    --from experiments/jev_states/results/probe_v4_dev200.json --out-name prefix_v4_dev200_normal_fp.json
"""
import argparse
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from probe_states import STATES, build_questions, common, load_normals  # noqa: E402
from prepare import load_calls  # noqa: E402


def add_args(p):
    p.add_argument("--from", dest="src", required=True, help="probe_states.py 결과 파일")
    p.add_argument("--select", choices=["normal-fp", "scam"], default="normal-fp",
                   help="normal-fp: 통화 전체 판단에서 상태가 하나라도 켜진 정상 통화, scam: 사기 통화")
    p.add_argument("--n", type=int, help="이 수만큼 무작위로 뽑는다(--select scam은 필수)")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--timeout", type=int, default=60)
    p.add_argument("--dry-run", action="store_true")


def pick(args):
    """대상 통화와 call_id별 대사를 돌려준다."""
    src = [c for c in json.loads(Path(args.src).read_text(encoding="utf-8"))["calls"] if "answers" in c]
    if args.select == "scam":
        picked = [c for c in src if c["scam"]]
    else:
        picked = [c for c in src if not c["scam"] and any(c["answers"][s]["verdict"] == "Yes" for s in STATES)]
    if args.n is not None:
        picked = random.Random(args.seed).sample(picked, args.n)
    lines = {c["call_id"]: c["lines"] for c in load_normals() + load_calls()}
    return picked, lines


def run(args, questions, picked, lines, make_input, out_name, **meta):
    """대사 k(1부터)마다 make_input(대사 목록, k)을 보내 상태 판단을 모은다."""
    results = []
    for i, c in enumerate(picked, 1):
        ls = lines[c["call_id"]]
        steps = []
        for k in range(1, len(ls) + 1):
            try:
                res = common.ask(questions, make_input(ls, k), timeout=args.timeout)
                steps.append({"k": k, "answers": res["answers"], "input_tokens": res["input_tokens"]})
            except common.JevError as e:
                steps.append({"k": k, "error": e.code})
        results.append({"call_id": c["call_id"], "scam": c["scam"], "gold": c["gold"], "n_lines": len(ls),
                        "full": c["answers"], "steps": steps})
        print(f"  {i}/{len(picked)} {c['call_id']} lines={len(ls)} errors={sum('error' in s for s in steps)}", flush=True)

    out = {"source": Path(args.src).name, "select": args.select, **meta,
           "questions": {k: v["instructions"] for k, v in questions.items()}, "calls": results}
    (HERE / "results" / out_name).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    p = argparse.ArgumentParser()
    add_args(p)
    p.add_argument("--out-name", default="prefix.json")
    args = p.parse_args()

    picked, lines = pick(args)
    print(f"calls={len(picked)} requests={sum(len(lines[c['call_id']]) for c in picked)}")
    if args.dry_run:
        return
    common.inject_truststore()
    run(args, build_questions(), picked, lines, lambda ls, k: ls[:k], args.out_name)


if __name__ == "__main__":
    main()
