"""Plan2 결과(predictions.csv)로 통합 임계 k의 Confusion Matrix PNG를 생성한다.

Plan2는 카테고리별 Yes 개수(yes_count)로 최종 예측을 만든다: yes_count >= k → Yes.
기본 k=1(=OR, F1 최고). 논문 스타일, 우측 컬러바 없음.

실행:
  uv run --with matplotlib python -X utf8 \
    experiments/Paln2-DivideAndConquer/results/visualization/visualize_confusion.py --k 1
"""

import argparse
import csv
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent


def load_confusion(predictions_path, k):
    tp = fp = tn = fn = 0
    skipped = 0
    with open(predictions_path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            yc = r.get("yes_count", "")
            if yc == "" or yc is None:
                skipped += 1
                continue
            gold = str(r["gold_yes"]).strip().lower() in ("true", "1", "yes")
            pred = int(yc) >= k
            if gold and pred:
                tp += 1
            elif gold and not pred:
                fn += 1
            elif not gold and pred:
                fp += 1
            else:
                tn += 1
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn, "skipped": skipped}


def main(argv=None):
    p = argparse.ArgumentParser(description="Plan2 Confusion Matrix 시각화 (임계 k)")
    p.add_argument("--predictions", default=str(HERE.parent / "predictions.csv"))
    p.add_argument("--k", type=int, default=1, help="yes_count >= k → Yes")
    p.add_argument("--out", default=None)
    p.add_argument("--title", default=None)
    args = p.parse_args(argv)

    out = args.out or str(HERE / "confusion_matrix.png")
    title = args.title or f"Jev with Categories (k={args.k})"

    cm = load_confusion(args.predictions, args.k)
    tp, fp, tn, fn = cm["tp"], cm["fp"], cm["tn"], cm["fn"]
    total = tp + fp + tn + fn
    acc = (tp + tn) / total if total else 0.0
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0

    matrix = [[tp, fn], [fp, tn]]
    names = [["TP", "FN"], ["FP", "TN"]]
    row_sums = [tp + fn, fp + tn]
    norm = [[(matrix[i][j] / row_sums[i]) if row_sums[i] else 0.0 for j in range(2)]
            for i in range(2)]

    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 12,
        "axes.linewidth": 0.8,
        "mathtext.fontset": "dejavuserif",
    })

    fig, ax = plt.subplots(figsize=(5.8, 5.4))
    ax.imshow(norm, cmap="Blues", vmin=0.0, vmax=1.0)

    ax.set_xticks([0, 1], labels=["Yes", "No"])
    ax.set_yticks([0, 1], labels=["Yes", "No"])
    ax.set_xlabel("Predicted label", labelpad=10)
    ax.set_ylabel("True label", labelpad=10)
    ax.xaxis.set_label_position("top")
    ax.xaxis.tick_top()

    for i in range(2):
        for j in range(2):
            val = matrix[i][j]
            pct = norm[i][j] * 100
            color = "white" if norm[i][j] > 0.5 else "#1a1a1a"
            ax.text(j, i, f"{names[i][j]}\n{val}\n({pct:.1f}%)", ha="center", va="center",
                    color=color, fontsize=12.5, linespacing=1.5)

    ax.set_xticks([0.5], minor=True)
    ax.set_yticks([0.5], minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="both", length=0)
    for spine in ax.spines.values():
        spine.set_edgecolor("#999999")

    ax.set_title(title, fontsize=13.5, pad=20)
    caption = (f"N = {total}      Acc = {acc:.3f}      Prec = {prec:.3f}"
               f"      Rec = {rec:.3f}      F1 = {f1:.3f}")
    if cm["skipped"]:
        caption += f"      (failed: {cm['skipped']})"
    fig.text(0.5, 0.025, caption, ha="center", fontsize=9, color="#333333")

    fig.tight_layout(rect=[0, 0.06, 1, 1])
    out_path = pathlib.Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200)
    print(f"저장: {out_path}")
    print(f"k={args.k} TP={tp} FP={fp} TN={tn} FN={fn} | "
          f"Acc={acc:.4f} Prec={prec:.4f} Rec={rec:.4f} F1={f1:.4f}")


if __name__ == "__main__":
    main()
