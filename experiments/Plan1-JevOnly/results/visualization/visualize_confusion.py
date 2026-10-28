"""Plan1 결과(predictions.csv)로 Confusion Matrix 히트맵 PNG를 생성한다.

실행:
  uv run --with matplotlib python -X utf8 \
    experiments/Plan1-JevOnly/results/visualization/visualize_confusion.py

기본 입력: ../predictions.csv (Plan1 results), 출력: ./confusion_matrix.png
라벨은 폰트 호환을 위해 영문/숫자로 표기한다.
"""

import argparse
import csv
import pathlib

import matplotlib

matplotlib.use("Agg")  # 화면 없이 파일로 저장
import matplotlib.pyplot as plt  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent


def load_confusion(predictions_path):
    tp = fp = tn = fn = 0
    skipped = 0
    with open(predictions_path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r.get("error"):
                skipped += 1
                continue
            gold = str(r["gold_yes"]).strip().lower() in ("true", "1", "yes")
            pred = str(r["pred_verdict"]).strip() == "Yes"
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
    p = argparse.ArgumentParser(description="Plan1 Confusion Matrix 시각화")
    p.add_argument("--predictions", default=str(HERE.parent / "predictions.csv"))
    p.add_argument("--out", default=str(HERE / "confusion_matrix.png"))
    p.add_argument("--title", default="Jev-only")
    args = p.parse_args(argv)

    cm = load_confusion(args.predictions)
    tp, fp, tn, fn = cm["tp"], cm["fp"], cm["tn"], cm["fn"]
    total = tp + fp + tn + fn
    acc = (tp + tn) / total if total else 0.0
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0

    # 행=실제(Yes,No), 열=예측(Yes,No). 음영은 행 기준 정규화(클래스 불균형 대응).
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

    # 셀 경계를 흰 격자로 구분 (논문 혼동행렬 느낌)
    ax.set_xticks([0.5], minor=True)
    ax.set_yticks([0.5], minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="both", length=0)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_edgecolor("#999999")

    ax.set_title(args.title, fontsize=13.5, pad=20)
    caption = (f"N = {total}      Acc = {acc:.3f}      Prec = {prec:.3f}"
               f"      Rec = {rec:.3f}      F1 = {f1:.3f}")
    if cm["skipped"]:
        caption += f"      (failed: {cm['skipped']})"
    fig.text(0.5, 0.025, caption, ha="center", fontsize=9, color="#333333")

    fig.tight_layout(rect=[0, 0.06, 1, 1])
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200)
    print(f"저장: {out}")
    print(f"TP={tp} FP={fp} TN={tn} FN={fn} | Acc={acc:.4f} Prec={prec:.4f} Rec={rec:.4f} F1={f1:.4f}")


if __name__ == "__main__":
    main()
