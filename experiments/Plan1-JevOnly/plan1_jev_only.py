"""Plan 1 — Jev 단독 단일 종합 판단 (baseline).

전체 통화 transcript를 한 번에 Jev에 주고 보이스피싱 Yes/No·P(Yes)를 받아,
정답 라벨과 비교해 Confusion Matrix·Accuracy·Precision·Recall을 측정한다.

실행 예:
  uv run --locked --env-file .env python -X utf8 \
    experiments/Plan1-JevOnly/plan1_jev_only.py --limit 100 --delay 0.3
"""

import argparse
import csv
import pathlib
import sys
from datetime import datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))  # experiments/
import common  # noqa: E402

from scamshield.jev import INSTRUCTIONS  # noqa: E402  서비스와 동일한 탐지 프롬프트 재사용

HERE = pathlib.Path(__file__).resolve().parent
QUESTION = {
    "voice_phishing": {
        "type": "choice",
        "instructions": INSTRUCTIONS,
        "criteria": {
            "Yes": "통화에 보이스피싱을 의심할 구체적인 정황이 있다.",
            "No": "현재 통화 내용에 보이스피싱을 의심할 충분한 정황이 없다.",
        },
    }
}


def main(argv=None):
    import time

    p = argparse.ArgumentParser(description="Plan1: Jev 단독 단일 종합 판단")
    p.add_argument("--data", default=str(common.DATA_PATH))
    p.add_argument("--limit", type=int, default=None, help="앞에서 N건만 평가")
    p.add_argument("--shuffle", action="store_true")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--delay", type=float, default=0.0, help="호출 간 지연(초)")
    p.add_argument("--timeout", type=int, default=30)
    p.add_argument("--price-in", type=float, default=None, help="입력 토큰 단가($/1M), 비용 계산용")
    p.add_argument("--price-out", type=float, default=None, help="출력 토큰 단가($/1M), 비용 계산용")
    p.add_argument("--out", default=str(HERE / "results"))
    args = p.parse_args(argv)

    common.inject_truststore()
    rows = common.load_dataset(args.data, limit=args.limit, shuffle=args.shuffle, seed=args.seed)
    print(f"[Plan1] 평가 대상 {len(rows)}건", flush=True)

    pairs, preds, failures, calls = [], [], [], []
    for i, row in enumerate(rows, 1):
        try:
            res = common.ask(QUESTION, [row["transcript"]], timeout=args.timeout)
            ans = res["answers"]["voice_phishing"]
            pred_yes = ans["verdict"] == "Yes"
            lat, it, ot = res["latency_s"], res["input_tokens"], res["output_tokens"]
            pairs.append((row["gold"], pred_yes))
            calls.append({"latency_s": lat, "input_tokens": it, "output_tokens": ot})
            preds.append(
                (row["id"], row["gold"], ans["verdict"], f"{ans['probability']:.4f}",
                 f"{lat:.3f}", it, ot, it + ot, "")
            )
        except common.JevError as e:
            failures.append((row["id"], e.code))
            preds.append((row["id"], row["gold"], "", "", "", "", "", "", e.code))
        if i % 25 == 0 or i == len(rows):
            print(f"  진행 {i}/{len(rows)} (실패 {len(failures)})", flush=True)
        if args.delay:
            time.sleep(args.delay)

    cm = common.confusion(pairs)
    m = common.metrics(cm)
    perf = common.summarize_perf(calls)

    report = (
        "# Plan 1 결과 — Jev 단독 단일 종합 판단\n\n"
        f"- 실행 시각: {datetime.now().isoformat(timespec='seconds')}\n"
        f"- 데이터: `{args.data}` (평가 {len(rows)}건, 호출 실패 {len(failures)}건 제외)\n\n"
        "## Confusion Matrix (양성 = Yes)\n\n"
        + common.render_confusion_md(cm)
        + "\n## 지표\n\n"
        + common.render_metrics_md(m)
        + "\n## Latency / 토큰 / 비용\n\n"
        + common.render_perf_md(perf, args.price_in, args.price_out)
    )
    if failures:
        from collections import Counter

        report += "\n## 호출 실패 집계\n\n"
        for code, n in Counter(c for _, c in failures).items():
            report += f"- {code}: {n}건\n"

    out_dir = pathlib.Path(args.out)
    common.write_text(out_dir, "metrics.md", report)
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "predictions.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "gold_yes", "pred_verdict", "prob_yes",
                    "latency_s", "input_tokens", "output_tokens", "total_tokens", "error"])
        w.writerows(preds)

    print("\n" + report)
    print(f"[Plan1] 결과 저장: {out_dir}")


if __name__ == "__main__":
    main()
