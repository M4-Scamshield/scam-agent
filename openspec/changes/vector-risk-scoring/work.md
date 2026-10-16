# 진행과 검증 기록

## 2026-10-16 — 스펙 작성 시작

사용자 전달 방향: 보이스피싱범 데이터셋을 pgvector에 임베딩하고, 이번 발화 검색과 통화 누적 검색의 top-k 유사도에 기존 누적 점수를 더해 risk를 만든다. 일정 기준 이상이면 SUSPECT 이상이다. 그 경우 Jev가 VERIFY로 넘어갈 맥락이 있는지 검사한다. SUSPECT는 경고 문구, VERIFY는 Tool 호출로 WARN을 확정한다. 점수와 VERIFY 판단은 port/adapter로 다른 API·ML 모델이 들어올 수 있게 한다. 임베딩은 Gemini embedding을 사용한다. top-k 집계 연산은 미정이다.

작성: [설계 기준](../../../docs/design/risk-scoring.md), 이 change의 proposal·spec·design·tasks·work. Jev는 TypeSafe System One 모델(`jev-latest`)이며 API 키가 아직 없다. 외부 문서(TypeSafe Quick start·Pydantic AI·Gemini Embedding)는 2026-10-16에 확인했다.

에이전트 제안(사용자 미확정): Tool 결과 뒤 Jev 재판단 대신 규칙으로 반영(NOT_FOUND → WARN, FOUND → SUSPECT, ERROR/TIMEOUT → VERIFY 유지 안내). phase 결정은 port 밖 Graph에서 threshold로 한다.

코드 변경·서비스 테스트는 없다.

## 2026-10-16 — 점수 방식·데이터셋·일상 발화 필터 결정

- 사용자 채택: 점수는 (b) 사기 유사도 − 정상 유사도. 에이전트가 코사인 유사도 절댓값의 낮은 변별력과 정상 기준 부재를 설명하고 (a) 정규화·(c) kNN 비율과 비교했다.
- 데이터셋 기본 후보: KorCCVi v2(금감원 사기·AI Hub 정상, 발화 단위·화자 구분). 출처와 label이 완전히 겹치는 저자 명시 한계를 설계에 기록했다. 사용 조건은 미확인.
- 사용자 채택: Jev가 일상 발화를 걸러 점수 반영 없이 넘기고, 걸러진 발화는 안내 없이 종료한다. 에이전트 보완: 걸러진 발화도 transcript에 남기고, 최근 대화를 함께 넘기며, 애매하면 판단 대상으로 둔다. 세 번째 port `UtteranceFilter`로 두었다.
- 사용자 채택: 조회 결과는 규칙으로 반영(NOT_FOUND → WARN, FOUND → SUSPECT 안내, ERROR/TIMEOUT → VERIFY 유지). FOUND는 first-demo에서 에이전트가 Mock 내부 초안으로 추가한 결과임을 사용자에게 설명했고, 사용자가 유지를 선택했다. WARN 시 risk 하한 `max(risk, 0.9)`도 채택.
- 사용자 채택: 통화 누적 검색은 최근 N개 발화 window(B안, 초기 N=5). 결합은 `risk = max(previous_risk × decay, w·utterance + (1−w)·call)`, 초기 w=0.5·decay=0.9(수치는 에이전트 초안). 이전 phase가 VERIFY·WARN이면 감쇠·하향 없음.
- 사용자 채택: SUSPECT 기준 이상 판단 대상 발화마다 VerifyJudge 호출, 이전 VERIFY면 호출 없이 재조회, FOUND 뒤 재VERIFY 허용, VERIFY risk 기준을 0.6에서 suspect_threshold로 변경.
- 사용자 채택: Jev 질문은 영어 Boolean 두 개(is_routine·should_verify, phase 아님), 필터 confidence ≥ 0.8·VERIFY ≥ 0.5, None이면 Boolean만 사용, 기준값은 Graph 설정. 문구·수치는 에이전트 초안.
- 사용자 채택: 임베딩 768차원·SEMANTIC_SIMILARITY, 점수 `clip((top-5 scam 평균 − top-5 normal 평균) / d_scale, 0, 1)`(초기 d_scale 0.1).
- 사용자 지시: 모든 수치는 확정이 아니며, 여러 수치를 넣어 좋은 값을 찾는 탐색 과정이 필수다. 설계 문서에 "수치 탐색 — 필수" 절, spec R8, tasks 구현 항목으로 남겼다.
- 남은 미정: 데이터셋 사용 조건(DATA.md) 확인.

## 검증

| 명령 또는 확인 | 결과 | 근거·한계 |
|---|---|---|
| `python3 .agents/skills/scamshield-docs-sync/scripts/check_docs.py` | PASS: 문서 30개·로컬 링크 365개 (2026-10-16 마지막 실행) | 외부 URL·앵커·의미 정합성은 미검사 |
| `git diff --check` | 통과 | 공백 오류만 확인 |

사용자가 에이전트의 초안으로 [이슈 #3](https://github.com/M4-Scamshield/scam-agent/issues/3)을 직접 생성했다. PR #2가 merge된 `origin/main`에서 `junyheon/3/vector-risk-scoring` 브랜치를 만들고 작성 중이던 문서를 옮겼다. main을 push 대상으로 추적하지 않도록 upstream은 해제했다.

## 남은 사항과 다음 행동

스펙 설계 논의는 데이터셋 사용 조건(DATA.md) 확인만 남았다. 다음: 문서 커밋 → 구현(port·Fake·Graph 분리 → pgvector·Gemini adapter와 적재 → **수치 탐색(필수)** → Jev adapter는 키 발급 후).
