# 작업 목록

상태: 진행 중 — 스펙 작성. 근거는 [work](work.md)에 있다.

## 스펙

- [x] 사용자 방향(벡터 점수로 OBSERVE/SUSPECT, Jev는 VERIFY 맥락, port/adapter)을 확인하고 설계 기준·change 문서를 작성한다.
- [x] GitHub 이슈를 만들고 브랜치에 연결한다. 사용자가 [#3](https://github.com/M4-Scamshield/scam-agent/issues/3)을 직접 만들었고 `origin/main`에서 `junyheon/3/vector-risk-scoring`을 만들었다.
- [x] 점수 방식((b) 사기−정상 유사도)·데이터셋 후보·일상 발화 필터·조회 결과 반영 규칙을 사용자와 확정한다.
- [x] 통화 누적 검색(최근 N개 window)과 점수 결합(감쇠 최댓값)·하향 허용 범위를 확정한다.
- [x] Jev 호출 시점(SUSPECT 기준 이상 판단 대상 발화마다, 이전 VERIFY는 바로 재조회, FOUND 뒤 재VERIFY 허용)과 VERIFY risk 기준을 확정한다.
- [x] Jev 질문 문구 초안·confidence 기준값(0.8/0.5)을 확정한다. 문구는 키 발급 후 실제 응답으로 다듬는다.
- [x] 임베딩(768·SEMANTIC_SIMILARITY)과 top-k 집계(top-5 평균 차이 + clip)를 확정한다. 수치는 초기값이다.

## 구현

- [ ] `RiskScorer`·`VerifyJudge` port와 Fake 대역, Graph 노드 분리.
- [ ] API·DB 없는 테스트로 세 발화 흐름·WARN 유지·Tool 1회·기준 미만 VerifyJudge 미호출 확인.
- [ ] Gemini embedding·pgvector adapter와 적재 스크립트, 로컬 compose.
- [ ] 샘플 데이터셋으로 실제 적재·검색·점수 산출 기록.
- [ ] **필수: 수치 탐색.** k·d_scale·suspect_threshold·w·decay·N·confidence 기준·임베딩 차원을 여러 값으로 비교하고(적재에 쓰지 않은 통화로 평가), 결과를 docs/analysis에 기록해 설계 문서의 값을 갱신한다. 이 항목 전에는 수치를 확정으로 표시하지 않는다.
- [ ] TypeSafe Jev adapter (키 발급 후 실제 호출 검증).
- [ ] README·아키텍처·MVP 스펙의 Jev 계약을 실제 구현에 맞춘다.
