"""KorCCVi 사기 통화를 화자 표시 대본으로 바꿔 읽기 묶음으로 나눈다.

입력(재배포 금지 자료라 data/ 에만 둔다, Git 제외):
  data/korccvi/{train,val,test}_segment_manifest_merged.jsonl  (구간 텍스트·speaker_name)
  data/korccvi_src/KorCCVi_v2_multimodal_calls.csv             (fss_source_file: FSS 원본 제목 = 유형 단서)
출력:
  data/korccvi_tactics/batches/batch_NN.txt  통화마다 "## <call_id> | 제목: …" 뒤에 "<줄번호> [A] 발화" 줄(줄번호는 통화 안에서 1부터)
  data/korccvi_tactics/calls.json            통화별 화자 수·구간 수·글자 수·묶음 번호

실행: python3 experiments/korccvi_tactics/prepare.py [--batches 9]
"""
import argparse
import collections
import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data"
OUT = DATA / "korccvi_tactics"


def load_calls():
    segs = collections.defaultdict(list)
    for split in ("train", "val", "test"):
        for line in open(DATA / "korccvi" / f"{split}_segment_manifest_merged.jsonl", encoding="utf-8"):
            d = json.loads(line)
            if d["label"] == 1:
                segs[d["call_id"]].append(d)
    csv.field_size_limit(10**9)
    titles = {r["call_id"]: r["fss_source_file"]
              for r in csv.DictReader(open(DATA / "korccvi_src" / "KorCCVi_v2_multimodal_calls.csv", encoding="utf-8-sig"))}
    calls = []
    for cid, ss in segs.items():
        ss.sort(key=lambda s: s["start"])
        lines = [f"[{s['speaker_name']}] {s['text'].strip()}" for s in ss if s["text"].strip()]
        calls.append({"call_id": cid, "title": titles.get(cid, ""), "lines": lines,
                      "n_speakers": len({s["speaker_name"] for s in ss}), "chars": sum(len(l) for l in lines)})
    return sorted(calls, key=lambda c: int(c["call_id"].split("_")[1]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--batches", type=int, default=9)
    n = p.parse_args().batches
    calls = load_calls()
    # 글자 수가 고르게 나뉘도록 긴 통화부터 가장 가벼운 묶음에 넣는다
    loads, groups = [0] * n, [[] for _ in range(n)]
    for c in sorted(calls, key=lambda c: -c["chars"]):
        i = loads.index(min(loads))
        groups[i].append(c)
        loads[i] += c["chars"]
        c["batch"] = i
    (OUT / "batches").mkdir(parents=True, exist_ok=True)
    for i, g in enumerate(groups):
        g.sort(key=lambda c: int(c["call_id"].split("_")[1]))
        text = "\n\n".join(f"## {c['call_id']} | 제목: {c['title']}\n" + "\n".join(f"{j} {l}" for j, l in enumerate(c["lines"], 1)) for c in g)
        (OUT / "batches" / f"batch_{i:02d}.txt").write_text(text + "\n", encoding="utf-8")
    meta = [{k: c[k] for k in ("call_id", "title", "n_speakers", "chars", "batch")} | {"n_lines": len(c["lines"])}
            for c in calls]
    (OUT / "calls.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"calls={len(calls)} chars={sum(loads)} per_batch={loads}")


if __name__ == "__main__":
    main()
