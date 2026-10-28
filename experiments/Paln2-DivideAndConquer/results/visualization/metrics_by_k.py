"""Plan2 predictions.csv로 통합 임계 k(1~4)에 따른 Accuracy·Recall 그래프를 그린다.

yes_count >= k → Yes 규칙으로 각 k의 지표를 계산해 선그래프로 저장한다. 논문 스타일.

실행:
  uv run --with matplotlib python -X utf8 \
    experiments/Paln2-DivideAndConquer/results/visualization/metrics_by_k.py
"""

import argparse
import csv
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent


def load_records(predictions_path):
    recs = []
    with open(predictions_path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            yc = r.get("yes_count", "")
            if yc == "" or yc is None:
                continue
            gold = str(r["gold_yes"]).strip().lower() in ("true", "1", "yes")
            recs.append((gold, int(yc)))
    return recs


def metrics_at_k(recs, k):
    tp = fp = tn = fn = 0
    for gold, yc in recs:
        pred = yc >= k
        if gold and pred:
            tp += 1
        elif gold and not pred:
            fn += 1
        elif not gold and pred:
            fp += 1
        else:
            tn += 1
    total = tp + fp + tn + fn
    acc = (tp + tn) / total if total else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    return acc, rec


def main(argv=None):
    p = argparse.ArgumentParser(description="Plan2 k별 Accuracy·Recall 그래프")
    p.add_argument("--predictions", default=str(HERE.parent / "predictions.csv"))
    p.add_argument("--out", default=str(HERE / "metrics_by_k.png"))
    p.add_argument("--kmax", type=int, default=4)
    args = p.parse_args(argv)

    recs = load_records(args.predictions)
    ks = list(range(1, args.kmax + 1))
    accs, recs_vals = [], []
    for k in ks:
        a, r = metrics_at_k(recs, k)
        accs.append(a)
        recs_vals.append(r)

    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 12,
        "axes.linewidth": 0.8,
        "mathtext.fontset": "dejavuserif",
    })

    fig, ax = plt.subplots(figsize=(6.2, 4.6))
    ax.plot(ks, accs, marker="o", markersize=7, linewidth=2, color="#1f4e79", label="Accuracy")
    ax.plot(ks, recs_vals, marker="s", markersize=7, linewidth=2, color="#c0504d", label="Recall")

    for k, a, r in zip(ks, accs, recs_vals):
        ax.annotate(f"{a:.3f}", (k, a), textcoords="offset points", xytext=(0, 9),
                    ha="center", fontsize=9, color="#1f4e79")
        ax.annotate(f"{r:.3f}", (k, r), textcoords="offset points", xytext=(0, -16),
                    ha="center", fontsize=9, color="#c0504d")

    ax.set_xticks(ks)
    ax.set_xlabel("Threshold k  (Yes categories ≥ k → Yes)", labelpad=8)
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.05)
    ax.set_title("Jev with Categories: Accuracy / Recall vs. k", fontsize=13.5, pad=12)
    ax.grid(True, linestyle=":", linewidth=0.7, color="#bbbbbb")
    ax.legend(frameon=False, loc="center right")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    fig.tight_layout()
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200)
    print(f"저장: {out_path}")
    for k, a, r in zip(ks, accs, recs_vals):
        print(f"  k={k}: Accuracy={a:.4f}  Recall={r:.4f}")


if __name__ == "__main__":
    main()
