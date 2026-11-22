"""NEW 수법 label을 키워드 규칙으로 후보 묶음(N1~N10)에 배정하고 유형별 출현 비율을 낸다.

label은 라벨러가 쓴 요약이라 원문이 아니다. 한 label은 규칙 순서상 처음 맞는 묶음 하나에만 넣는다.
출력: experiments/korccvi_tactics/results/new_groups.json
실행: python3 experiments/korccvi_tactics/group_new.py
"""
import collections
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ANN = REPO / "data" / "korccvi_tactics" / "annotations"
OUT = Path(__file__).resolve().parent / "results"

GROUPS = [
    ("N1", "사건 연루 통보", r"연루|발견|압수|도용 사건|사건에|범죄에 사용|범죄 현장|검거 현장|범죄 자금|세탁|불법 자금|사기에 쓰였"),
    ("N2", "용의자·관계 확인", r"아는지|아는 사람|관계 질문|인물|신상|범 일당|일당 규모|주범|용의자|고소인"),
    ("N3", "녹취·조사 절차 연출", r"녹취|조사 진행|약식|진술서|소환|출석|증거|공문|사건번호|메모|조서|추적 동의|복창|담당 검사"),
    ("N4", "자산·금융현황 파악", r"잔액|잔고|자산|거래 은행|금융기관|계좌 수|계좌 개수|계좌 종류|계좌 현황|계좌별|보유|예금|한도|뱅킹|카드론|대출 현황|부채|기존 대출|신용카드|연체|필요 자금"),
    ("N5", "분실·개설·양도 여부 추궁", r"분실|도난|유출|양도|판매|판 가해자|넘겼|해킹|피해자인지|가해자인지|입증|개설|입출금 내역"),
    ("N6", "보상·혜택 약속", r"보상|약속|혜택|저금리|대환|승인|무혐의|벗어나|원상복구|돌려|지원|증액|선지급|이득|유리"),
    ("N7", "안심·의심 무마", r"안심|의심|무마|반박|걱정|불이익이 없|안전하|아니라며|요구하지 않|둘러댐|배려|호의"),
    ("N8", "규모·불신 조성", r"규모|대규모|중대|전국|직원.*연루|불신|은행원|내부 직원|공범|피해 사례|2차 피해|추가.*피해"),
    ("N9", "답변 대본·행동 지시", r"대본|답하라|말하게|정해진 답|낭독|답변 방식|지시|대답|보고하게|설명해 보게"),
    ("N10", "계좌 동결·보호 조치", r"동결|보호 조치|보호조치|안전 조치|지급정지|안전계좌"),
]


# 첫 일치 규칙이 뜻과 다르게 묶은 라벨. 2026-11-16 Jev 상태 실호출의 미탐·오탐 확인에서 찾았다.
OVERRIDES = {
    "고액 일당·수수료율을 제시": "N6",
    "기존 대출이 있어도 연체가 없으면 대환이 가능하다고 권유": "N6",
    "기존 대출이 있어도 추가·저금리 대환이 가능하다고 제시(이득 약속)": "N6",
    "연체가 없으면 예치금을 돌려준다고 약속": "N6",
    "정부 보증 상품이라 연체만 없으면 대출된다고 이득 약속": "N6",
}


def group_of(label):
    if label in OVERRIDES:
        return OVERRIDES[label]
    for code, _, pattern in GROUPS:
        if re.search(pattern, label):
            return code
    return None


def main():
    rows = [json.loads(line) for f in sorted(ANN.glob("batch_*.jsonl")) for line in open(f, encoding="utf-8") if line.strip()]
    n_type = collections.Counter(r["type"] for r in rows)
    labels = [(r, t["label"]) for r in rows for t in r["tactics"] if t["code"] == "NEW"]
    calls = collections.defaultdict(set)
    top = collections.defaultdict(collections.Counter)
    unmatched = 0
    for r, label in labels:
        g = group_of(label)
        if g is None:
            unmatched += 1
            continue
        calls[g].add((r["type"], r["call_id"]))
        top[g][label] += 1

    out = {"new_labels": len(labels), "unmatched": unmatched, "groups": []}
    for code, name, _ in GROUPS:
        by_type = collections.Counter(ty for ty, _ in calls[code])
        out["groups"].append({
            "code": code, "name": name, "calls": len(calls[code]), "calls_pct": round(100 * len(calls[code]) / len(rows), 1),
            "by_type_pct": {ty: round(100 * by_type[ty] / n_type[ty], 1) for ty in n_type if by_type[ty]},
            "top_labels": top[code].most_common(5)})
    OUT.mkdir(exist_ok=True)
    (OUT / "new_groups.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"NEW labels={len(labels)} unmatched={unmatched}")
    for g in out["groups"]:
        print(g["code"], g["name"], g["calls_pct"], g["by_type_pct"])


if __name__ == "__main__":
    main()
