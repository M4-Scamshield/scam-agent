# 변경 요구사항

계약의 상세는 [설계 기준](../../../docs/design/risk-scoring.md)에 있다. 여기에는 이번 변경이 만족해야 할 동작만 적는다.

## 충족해야 할 동작과 계약

- R0. filter_utterance는 이전 WARN이면 warn으로 보낸다. 그 외에는 `UtteranceFilter`로 이번 발화가 일상 발화인지 판단하고, 일상 발화면 risk·phase를 바꾸지 않고 안내 없이 종료한다. 걸러진 발화도 transcript에 남는다.
- R1. score_risk는 `RiskScorer`로 risk(0~1)를 계산해 State에 적용한다. risk가 SUSPECT 기준 미만이면 OBSERVE로 종료하고 VerifyJudge를 호출하지 않는다.
- R2. 벡터 adapter는 이번 발화 검색과 통화 누적 검색을 모두 수행한다. 통화 누적 검색의 query는 최근 N개 발화 window다. 각 검색 점수는 사기 유사도 − 정상 유사도이며, `risk = max(previous_risk × decay, w·utterance_score + (1−w)·call_score)`로 결합한다. 이전 phase가 VERIFY·WARN이면 감쇠하지 않고 phase를 내리지 않는다. w·decay·N·k·기준값은 설정으로 바꿀 수 있다.
- R3. 이전 phase가 OBSERVE·SUSPECT이고 risk가 SUSPECT 기준 이상인 판단 대상 발화마다 judge_verify가 `VerifyJudge`를 호출한다. should_verify=true이면 VERIFY, 아니면 SUSPECT다. FOUND 뒤 SUSPECT에서도 다시 VERIFY할 수 있다. 이전 phase가 VERIFY면 VerifyJudge 없이 verify_agent로 가서 다시 조회한다. VERIFY에는 risk ≥ SUSPECT 기준을 요구한다(기존 0.6 대체).
- R4. SUSPECT는 suspect_agent의 안내로, VERIFY는 verify_agent → tool_execution → apply_verification으로 이어진다. apply_verification은 Jev를 호출하지 않고 이번 turn 결과로 정한다: NOT_FOUND → WARN(risk 하한 적용), FOUND → SUSPECT 안내, ERROR/TIMEOUT → VERIFY 유지 안내.
- R5. 이전 phase가 WARN이면 필터·점수와 관계없이 WARN을 유지한다. turn당 Tool 실행은 최대 1회다.
- R6. Graph는 `UtteranceFilter`·`RiskScorer`·`VerifyJudge` 구현을 주입받는다. 구현을 바꿔도 Graph 코드를 수정하지 않는다.
- R7. 데이터셋 적재 스크립트는 JSONL `{source_id, text, label, speaker}`를 임베딩해 pgvector에 저장한다. 통화 Graph는 검색만 한다.

## 정상·실패 조건

- UtteranceFilter·RiskScorer·VerifyJudge의 호출 실패나 출력 형식 오류는 각각 stage=`filter`·`risk`·`verify_judge` 실행 오류로 반환하고 자동 재시도하지 않는다.
- 임베딩 차원이 저장소 차원과 다르면 적재·검색 모두 오류로 중단한다.
- Tool ERROR/TIMEOUT은 결과로 저장하며 WARN을 강제하지 않는다.

## 검증 가능한 완료 조건

| 조건 | 검증 방법 |
|---|---|
| 세 발화 흐름과 기존 정책 유지 | Fake Embedder·In-memory store·Fake VerifyJudge로 API·DB 없는 pytest |
| 기준 미만에서 VerifyJudge 미호출 | 호출 기록 대역으로 pytest |
| 감쇠로 SUSPECT → OBSERVE 복귀, VERIFY·WARN 미하향 | Fake 점수 대역으로 pytest |
| 이전 VERIFY에서 VerifyJudge 없이 재조회, FOUND 뒤 재VERIFY | Fake 대역으로 pytest |
| 조회 결과 세 종류의 phase·risk·안내 | Mock 결과 대역으로 pytest |
| 일상 발화의 State 불변·transcript 보존·안내 없음 | Fake Filter로 pytest |
| port 교체 | 다른 대역 구현을 주입한 pytest |
| 실제 적재·검색 | 로컬 pgvector + Gemini embedding 실행 기록(work) |
| Jev | 키 발급 후 실제 호출 기록. 이전에는 미검증으로 표시 |

## 관련 상위 설계와 기준 문서

- [설계 기준](../../../docs/design/risk-scoring.md) · [MVP 전체 스펙](../../../docs/design/state-and-graph.md) · [proposal](proposal.md)
