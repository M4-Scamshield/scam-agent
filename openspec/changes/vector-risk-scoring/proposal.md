# 벡터 유사도 위험 점수와 Jev VERIFY 판단

상태: 진행 중 — 스펙 작성 단계. 구현 전.

GitHub 이슈: [#3 — 데이터셋 벡터 유사도로 위험 점수를 산출하고 Jev가 검증 진입을 판단하기](https://github.com/M4-Scamshield/scam-agent/issues/3). 브랜치: `junyheon/3/vector-risk-scoring`.

## 문제와 목표

현재 [Fake Jev](../../../scamshield/jev.py)는 정해진 데모 문장에만 반응하는 규칙으로 risk와 phase를 모두 정한다. 자유로운 통화에는 판단 근거가 없다. 실제 Jev(TypeSafe System One)는 한국어 정확도와 점수 품질을 아직 확인하지 못했고 API 키도 없다.

2026-10-16 사용자 방향: 보이스피싱범 발화 데이터셋을 pgvector에 임베딩해 두고, 벡터 유사도와 기존 누적 점수로 risk와 OBSERVE/SUSPECT를 정한다. SUSPECT 이상일 때만 Jev가 VERIFY로 넘어갈 맥락이 있는지 판단한다. SUSPECT는 경고·확인 안내, VERIFY는 Tool 조회로 WARN을 확정한다. 점수와 VERIFY 판단은 port/adapter로 분리해 다른 API·ML 모델로 교체할 수 있게 한다.

## 범위와 제외 범위

포함:

- `UtteranceFilter`·`RiskScorer`·`VerifyJudge` port와 Graph 주입, 벡터 유사도 adapter(Gemini embedding + pgvector), Fake 대역.
- `detect_with_jev`를 filter_utterance·score_risk·judge_verify·apply_verification으로 분리.
- 데이터셋 적재 스크립트와 로컬 pgvector 실행 환경.
- TypeSafe Jev adapter(키 발급 후 실제 검증).

제외: threshold·결합 연산의 최종 보정, 분류 모델 학습, 데이터셋 수집·정제, 실제 기관 조회, STT·프론트, Agent 런타임 전환.

## 완료 조건

1. 스펙: [설계 기준](../../../docs/design/risk-scoring.md)과 이 change의 요구·설계를 기록하고 미정 수치를 구분한다.
2. API·DB 없는 테스트로 세 발화 데모가 OBSERVE → SUSPECT → VERIFY → WARN을 거치고 기존 정책(WARN 하향 금지·turn당 Tool 1회)을 유지한다.
3. 로컬 pgvector + Gemini embedding으로 실제 적재·검색·점수 산출을 실행하고 결과를 기록한다. 탐지 성능은 주장하지 않는다.
4. Jev adapter는 키 발급 후 실제 호출을 별도로 검증한다. 그 전에는 Fake 검증만 했다고 구분한다.

## 관련 상위 설계와 change 문서

- [벡터 유사도 위험 점수와 VERIFY 판단](../../../docs/design/risk-scoring.md) — 이 change의 설계 기준
- [MVP 전체 스펙](../../../docs/design/state-and-graph.md) — 공통 State·Graph 규칙
- [first-demo](../first-demo/work.md) — 선행 데모 구현
- [요구](spec.md) · [적용 설계](design.md) · [작업](tasks.md) · [근거](work.md)
