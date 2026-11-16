# 진행과 검증 기록

## 범위와 작업 트리

2026-11-15 main에서 `feat/korccvi-scam-tactics`를 만들었다. 시작 시 있던 `.gitignore`의 `data/` 항목 추가(미커밋)를 함께 가져왔다. 2026-11-16 최신 main(98f78b6) 위로 브랜치를 다시 만들어 분석 결과를 커밋했다. PR은 아직 만들지 않았다.

## 데이터 확보

- KorCCVi 원본 저장소는 `.git`만 128MB를 넘어 clone을 멈췄다. GitHub API tree와 raw 파일로 DATA.md, README, 통화 단위 CSV(1,417행), FSS 파일 매핑만 `data/korccvi_src/`에 받았다.
- 화자 표시는 기존 로컬 manifest `data/korccvi/*_segment_manifest_merged.jsonl`의 `speaker_name`을 썼다. 사기 통화의 화자 수 분포는 1명 232, 2명 379, 3명 77, 4명 14, 5명 4다.
- DATA.md 조건에 따라 원문·대본·라벨(quote 포함)은 모두 `data/`(git 제외)에 두었다.

## 라벨링

- `prepare.py --batches 9`를 실행했다. 결과는 706통화, 28,577줄, 1,264,439자이고 묶음당 77~79통화다.
- 묶음마다 Claude 에이전트 하나가 [지침](../../../experiments/korccvi_tactics/ANNOTATION.md)대로 라벨을 달았다.
- 9개 파일 모두 다음을 검사해 통과했다.
  - 통화 수가 묶음과 일치한다.
  - JSON 필드와 code 값이 지침에 맞다.
  - quote가 해당 줄 원문의 부분 문자열이다.

## 집계와 원문 검사

- `python3 experiments/korccvi_tactics/aggregate.py`
  - calls=706, missing=0
  - diarization_ok 590
  - title_matches: True 276 / False 142 / None 288
- `python3 experiments/korccvi_tactics/group_new.py`: NEW label 2,336개 중 483개가 어느 묶음에도 들어가지 않았다.
- 원문 대조
  - 대상은 results의 3개 파일(summary.json, new_labels.txt, new_groups.json)이다.
  - 12자 이상 문자열을 공백을 지운 원문 CSV 전체와 15자 창으로 대조했다.
  - 일치는 2건이다. 사칭 직함 하나와 일반 표현 label 하나이고, 고유 정보가 없어 그대로 두었다.
  - results에는 quote 필드가 없다.
- 결과 해석은 [분석 문서](../../../docs/analysis/korccvi-scam-tactics.md)에 있다.

## 행동 특징 F1~F6 재집계

- 2026-11-15 사용자 요청으로 R1~R9와 N1~N10을 유형과 관계없는 행동 특징 6개로 다시 묶었다. 대화 중 임시 스크립트로 먼저 냈고, 2026-11-16 `regroup_features.py`로 저장소에 남겼다.
- `python3 experiments/korccvi_tactics/regroup_features.py`
  - calls=694(판단불가 12건 제외), 특징 2개 이상 608건(87.6%), F2 강한 신호 29.0%
  - 출현율: F1 20.5, F2 35.6, F3 18.4, F4 78.1, F5 39.5, F6 83.4(%)
  - 첫 등장 위치 중앙값: F1 0.28, F2 0.30, F3 0.53, F4 0.20, F5 0.37, F6 0.03
- 임시 계산과 출현율·2개 이상 통화 수는 같았다. F2 위치만 임시 계산값 0.33과 달라 재현할 수 없었고, 스크립트 값 0.30을 기준으로 삼는다.
- features.json에는 코드·이름·수치만 있고 원문이나 label이 없다.

## 한계와 다음 행동

- 라벨러가 LLM이고, R 목록을 먼저 준 영향이 있다. 편집된 일부 구간이고, 화자 분리 오류가 116건이며, 출처가 FSS 하나다(분석 문서 한계 절 참조).
- 다음 행동
  - 표본 50통화 정도를 사람이 검수한다.
  - 정상 통화에서 R·N 요소 비율을 잰다.
  - N1~N10 중 무엇을 위험 요소 목록에 넣을지 사용자와 정한다.
