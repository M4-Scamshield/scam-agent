# 분석과 실험

기존 자산 조사·외부 API 확인·기술 실험·재현 자료와 결과의 한계를 남기는 위치다. 전체 진입점은 [문서 지도](../index.md)다.

## 문서 목록

- [실시간 통화 분석의 기능상 위험 검토](runtime-risk-review.md): 분석 실패의 정상 오인, 보류·이력 복구·재평가·라우팅·도구 근거의 위험과 API 없는 재현. 첫 개선인 분석 실패 대응의 원인·timeout 설정·조치 후보와 미측정 사항.

- [KorCCVi 사기 통화의 유형별 수법](korccvi-scam-tactics.md): 실제 사기 706통화를 유형별로 라벨링한 결과다. 사칭 대상, 요구 사항, 압박 방식, R1~R9 출현율, 목록에 없는 수법 후보(N1~N10), 유형과 관계없는 행동 특징 F1~F6을 정리했다.

- [Jev 상태 질문 버전별 변경 이력](jev-state-question-versions.md): F1~F6 상태 질문을 v1부터 버전마다 어떤 미탐·오탐 때문에 바꿨는지, 같은 정답으로 다시 채점한 상태별 결과와 커밋을 정리했다.

- [새 면접 대본으로 Jev 재평가](interview-holdout-eval.md): 기존 100% 감사·문답 공유 확인, 새 대본 각 50건 동결 후 실제 Jev 평가(정확도 98%·정상 오탐 2건), 오류와 해석 한계.

- [면접 사기·정상 합성 통화와 Plan1 평가](interview-phishing-dataset.md): 사기·정상 각 100건의 JSON 형식·분포·검증 및 실제 Jev confusion matrix와 해석 한계.

첫 데모의 API 없는 검사·실제 Gemini 성공/실패·리뷰 회귀 검증은 [first-demo work](../../openspec/changes/first-demo/work.md)에 조건과 실행 근거를 남겼다. 현재 구현의 범위는 [아키텍처](../architecture/overview.md), Harness 참고 저장소와 적용 범위는 [Harness 안내](../harness/index.md)에 있다. 같은 검증 기록을 별도 분석 문서에 복제하지 않는다.

새 분석에는 관찰한 대상·시점·방법·결과·한계·관련 설계를 적는다. 외부 API 문서 확인과 실제 API 호출 성공을 구분하고, Mock 결과를 실제 기관 검증 결과로 표현하지 않는다.
