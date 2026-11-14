# 정상 면접 통화 100건과 사기·정상 비교 평가셋

사용자 요청에 따라 만든 합성 정상 면접 통화 **100건**이다. [사기 면접 100건](../interview_phishing/README.md)과 직무·경력 사례·길이를 통화별로 맞춰 비교한다. 면접 상황을 유지하며 교육·장비·급여·계정·과제·일정 변경 등 20개 채용 주제와 100개 직무·경력 사례를 사용한다. 각 주제에 5개 종료 경로를 조합한다. 실제 통화 전사문이나 100명의 독립 작성 대본은 아니다.

## 파일과 형식

| 파일 | 내용 |
|---|---|
| `interview_normal_100.json` | 정상 100건 원본, `label: normal`, 화자 `나`·`면접관` |
| `interview_normal_inputs.json` | 정상 100건 평가 입력, A/B 화자, 역할·정답·주석 제외 |
| `interview_comparison_200_inputs.json` | 사기 100건+정상 100건을 고정 시드로 섞은 A/B 평가 입력 |
| `interview_comparison_200_answers.json` | 혼합 입력의 정답과 원본 ID·짝 통화 ID 연결 |
| `validation_report.json` | 실제 파일을 읽어 확인한 수량·길이·화자·주제·중복 검사 보고서 |

기존 사기 원본의 `metadata`, `calls`, `utterances` 구조를 유지한다. 한 항목은 한 문장이고 `sentence_id`, `speaker`, `text`를 담는다. 정상 원본의 `first_evidence_sentence_id`는 `null`, `evidence_sentence_ids`는 빈 배열이다. `paired_source_call_id`는 대응되는 사기 통화 ID이며 정답 정보에만 보관한다.

정상 100건은 **7,451문장**, 통화당 50~100문장·평균 74.51문장이다. 50~100의 모든 정수 길이를 포함하고, 대응되는 사기 통화와 각각 길이가 같다. 전체 문장 중 고유 문장은 2,255개·30.26%이며 통화 간 공유 문답이 있다. 같은 통화 전체의 복제와 통화 내 동일 문장 반복은 없다.

## 비교 평가

모델에는 혼합 입력의 각 `utterances`만 전달한다. `eval_001` 같은 중립 ID로 정답 파일과 결합하며, 정답·원본 ID·파일 경로·짝 통화 ID는 프롬프트에 넣지 않는다. A/B 역할 대응은 각 클래스에서 절반씩 바꾼다. 200건은 총 14,902문장이다.

[생성·검사 도구](../../experiments/build_normal_interview_dataset.py)는 사기 원본의 SHA-256을 확인하고 원본을 수정하지 않는다. 정상 채용 문답과 종료 경로를 새로 작성하며 나머지 면접 문답과 경력 사례를 공유한다. 실제 사기 요구 8개 문답과 사기 측 압박·종료부를 교체한다. 정상 채용 예시는 특정 기업이나 법령의 실제 절차를 보증하지 않는다.

```sh
python3 experiments/build_normal_interview_dataset.py
python3 experiments/build_normal_interview_dataset.py --check
```

생성 시 Plan1이 읽는 `id,transcript,label` CSV도 `experiments/data/interview_200_plan1.csv`에 만든다. CSV의 대화에는 A/B와 본문만 넣고 `label`은 별도 열에 둔다. 생성 도구는 API를 호출하지 않는다.

실제 평가는 [Plan1](../../experiments/Plan1-JevOnly/plan1_jev_only.py)의 전체 통화 1회·서비스 공통 프롬프트·choice Yes/No 판단을 그대로 쓴다. 기존 KorCCVi 결과와 혼합하지 않고 별도로 저장한다.

```sh
uv --cache-dir /private/tmp/scamshield-uv-cache run --locked --no-sync --env-file .env python -X utf8 experiments/Plan1-JevOnly/plan1_jev_only.py --data experiments/data/interview_200_plan1.csv --delay 0.15 --timeout 30 --out experiments/Plan1-JevOnly/results/interview_200
```

실행 결과는 [결과표](../../experiments/Plan1-JevOnly/results/interview_200/metrics.md)와 [confusion matrix 이미지](../../experiments/Plan1-JevOnly/results/interview_200/confusion_matrix.png)에 있다. [분석 기록](../../docs/analysis/interview-phishing-dataset.md)과 [work](../../openspec/changes/interview-phishing-dataset/work.md)에서 조건과 검증 근거를 확인할 수 있다.

## 해석 범위

사기와 정상 모두 있어 이 합성 표본에서 confusion matrix·재현율·오경보율을 계산할 수 있다. 동일 면접의 정상/사기 변형이어서 학습·평가를 섞으면 강한 누출이 생긴다. 이번 자료는 평가용으로 사용하고 짝 통화와 문답 원형을 독립 표본으로 간주하지 않는다. 정상 대화에는 절차 확인·금융·인증·개인정보 등의 말이 등장하지만 상대방에게 자금·인증수단·계정 접근권을 넘기도록 요구하지 않는다. 실제 음성·ASR·화자 분리 오류·다대다 통화 기능은 별도 검증 범위다.
