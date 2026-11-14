# 새 면접 대본 100건과 재평가

2026-11-14 사용자가 기존 100% 결과를 재검토하고 **면접 상황의 다른 합성 대본**으로 평가하도록 요청했다. 기존 생성기나 면접 문답을 재사용하지 않고 새 대본을 작성했다. 사기 50건·정상 50건, 총 960발화다. 실제 통화나 실제 기업의 절차를 재현한 자료는 아니다.

각 클래스는 8발화 20건·10발화 20건·12발화 10건이다. 한 발화에 여러 문장이 들어갈 수 있다. 기존 데이터의 50~100문장 조건을 재현한 장편 통화 평가가 아니므로 점수 차이를 데이터 중복 해소의 효과 하나로 설명할 수 없다.

## 파일

| 파일 | 용도 |
|---|---|
| [scenarios.txt](scenarios.txt) | 직접 작성한 원본. 블록 첫 줄은 정답·상황·근거 발화 번호·작성 근거이며 이후에는 면접관/지원자 교대 발화 |
| [inputs.json](inputs.json) | 섞인 중립 ID와 A/B 발화만 있는 평가용 자료 |
| [answers.json](answers.json) | ID별 정답·작성 근거·원본 연결. 모델 입력에 포함하지 않음 |
| [validation_report.json](validation_report.json) | 수량·중복·화자 균형·출력 해시 검사 |

실행은 [변환·검사 도구](../../experiments/build_interview_holdout.py)로 재현한다. CSV는 Git 제외 경로인 `experiments/data/interview_holdout_100.csv`에 만들어진다.

```sh
python3 experiments/build_interview_holdout.py
python3 experiments/build_interview_holdout.py --check
```

모델에는 `inputs.json`의 발화에서 만든 `A: 본문`/`B: 본문` 문자열만 보낸다. `call_id`, 정답, 상황 제목, 근거, 원본 파일을 프롬프트에 넣지 않는다. 각 클래스에서 면접관 A/B는 각각 25건이다. seed 261114로 순서를 고정했다.

## 정답과 구성 원칙

사기는 면접·채용을 빌미로 지원자의 돈·금융 인증수단·계정 접근권·명의를 넘기게 하는 구체적인 요구가 있는 장면이다. 정상은 현재 면접 통화의 당사자가 그런 행위를 하지 않는 장면이다. 사기 사례에 어떻게 대응할지 묻는 직무 면접은 정상으로 작성했다. 유료 교육·기숙사 공제·보험·계약 조건을 언급한다는 사실만으로 사기로 정하지 않았다. 정상 라벨은 실제 계약의 적법성이나 유리함을 보증하지 않는다.

사기·정상 양쪽에 인증, 급여, 과제, 원격 지원, 계좌, 상품권 등의 주제를 포함했다. 일부 수법·키워드·안전 절차는 기존 대본과 겹친다. 기존 200건과 정규화한 전체 대화 일치 0건, 정규화 후 15자 이상 발화의 정확 일치 0건이며 새 대본끼리도 같은 긴 발화를 반복하지 않는다. 이 검사는 의미적 독립성이나 모델의 사전학습 자료 미포함을 증명하지 않는다. `holdout`이라는 폴더명은 이번 실행 전 사용하지 않은 평가 자료를 뜻하며, 실제 학습/시험 분할이나 독립 작성자 검수를 뜻하지 않는다.

## 실제 평가

대본·정답·입력·프롬프트·코드의 해시를 [동결 기록](../../experiments/Plan1-JevOnly/results/interview_holdout_100/run_manifest.json)에 저장한 뒤 기존 Plan1으로 한 번씩 호출했다. 결과 확인 후 데이터·정답·프롬프트·판정 기준을 조정하지 않았으며 실행 후 해시 일치도 확인했다.

```sh
uv --cache-dir /private/tmp/scamshield-uv-cache run --locked --no-sync --env-file .env python -X utf8 experiments/Plan1-JevOnly/plan1_jev_only.py --data experiments/data/interview_holdout_100.csv --delay 0.15 --timeout 30 --out experiments/Plan1-JevOnly/results/interview_holdout_100
```

성공 100건·실패 0건, TP 50·FN 0·FP 2·TN 48, 정확도 98%·정밀도 96.15%·재현율 100%·특이도 96%다. 결과와 해석은 [분석](../../docs/analysis/interview-holdout-eval.md), [오류 사례](../../experiments/Plan1-JevOnly/results/interview_holdout_100/error_cases.md), [혼동행렬](../../experiments/Plan1-JevOnly/results/interview_holdout_100/confusion_matrix.png), [검증 기록](../../openspec/changes/interview-phishing-dataset/work.md)에 있다.

작성과 라벨링은 같은 에이전트가 수행했다. 실제 통화·ASR 오류·독립 사람 검수·모델 버전 고정·반복 측정은 검증하지 않았다. 사기 50건에서 누락이 없었다는 관측이 모든 면접 사기를 탐지한다는 뜻은 아니다.
