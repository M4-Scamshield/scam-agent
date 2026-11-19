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
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from probe_states import STATES, build_questions, common, load_normals  # noqa: E402
from prepare import load_calls  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--from", dest="src", required=True, help="probe_states.py 결과 파일")
    p.add_argument("--select", choices=["normal-fp"], default="normal-fp",
                   help="normal-fp: 통화 전체 판단에서 상태가 하나라도 켜진 정상 통화")
    p.add_argument("--timeout", type=int, default=60)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--out-name", default="prefix.json")
    args = p.parse_args()

    src = json.loads(Path(args.src).read_text(encoding="utf-8"))["calls"]
    picked = [c for c in src if not c["scam"] and any(c["answers"][s]["verdict"] == "Yes" for s in STATES)]
    lines = {c["call_id"]: c["lines"] for c in load_normals() + load_calls()}
    print(f"calls={len(picked)} requests={sum(len(lines[c['call_id']]) for c in picked)}")
    if args.dry_run:
        return

    common.inject_truststore()
    questions = build_questions()
    results = []
    for i, c in enumerate(picked, 1):
        ls = lines[c["call_id"]]
        steps = []
        for k in range(1, len(ls) + 1):
            try:
                res = common.ask(questions, ls[:k], timeout=args.timeout)
                steps.append({"k": k, "answers": res["answers"], "input_tokens": res["input_tokens"]})
            except common.JevError as e:
                steps.append({"k": k, "error": e.code})
        results.append({"call_id": c["call_id"], "scam": c["scam"], "gold": c["gold"], "n_lines": len(ls),
                        "full": c["answers"], "steps": steps})
        print(f"  {i}/{len(picked)} {c['call_id']} lines={len(ls)} errors={sum('error' in s for s in steps)}", flush=True)

    out = {"source": Path(args.src).name, "select": args.select,
           "questions": {k: v["instructions"] for k, v in questions.items()}, "calls": results}
    (HERE / "results" / args.out_name).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
