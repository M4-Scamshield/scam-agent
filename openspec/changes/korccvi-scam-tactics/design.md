# 변경 설계

## 기존 구조와 변경할 부분

기존 실험은 KorCCVi를 통화 단위 분류(Plan1·Plan2)와 사기범 발화 임베딩(최다 화자 규칙)에 썼다. 이번에는 분류가 아니라 내용 분석이다. 서비스 코드는 바꾸지 않고 `experiments/korccvi_tactics/`에 지침·스크립트·결과를 둔다.

## 책임·인터페이스·데이터 흐름

1. `data/korccvi/*_segment_manifest_merged.jsonl`(구간·화자) + `data/korccvi_src/KorCCVi_v2_multimodal_calls.csv`(FSS 제목) → `prepare.py` → `data/korccvi_tactics/batches/batch_NN.txt`, `calls.json`.
2. 묶음마다 LLM 에이전트(Claude) 하나가 지침대로 전부 읽고 `data/korccvi_tactics/annotations/batch_NN.jsonl`을 쓴다.
3. `aggregate.py` → `results/summary.json`, `results/new_labels.txt` → 분석 문서.
4. `group_new.py` → NEW label을 키워드 규칙으로 N1~N10 후보에 묶은 `results/new_groups.json`.

## 선택·대안·trade-off

- 라벨러: 706통화(약 126만 자)를 사람이 읽기는 범위를 넘어 LLM이 읽었다. 대신 지침을 먼저 고정하고, quote와 줄번호를 남겨 나중에 사람이 표본 검수할 수 있게 했다.
- 코드 목록: R1~R9를 주고 맞지 않으면 NEW로 적게 했다. 목록 없이 자유 추출하면 집계가 어렵고, 목록만 주면 새 수법을 놓친다. NEW를 별도로 집계해 목록에 없는 수법을 찾는다. 목록을 먼저 준 영향(끼워 맞추기)은 남는 한계다.
- 유형 판단: FSS 제목과 내용이 어긋나는 사례를 확인해 내용 기준으로 정했다.

## 미정 사항과 검증 방법

사람 검수 일치도, 정상 통화의 같은 요소 비율, 다른 라벨러(Gemini 등)와의 비교는 후속이다.

## 관련 상위 설계와 기준 문서

[proposal](proposal.md), [spec](spec.md), [분석 문서](../../../docs/analysis/korccvi-scam-tactics.md).
