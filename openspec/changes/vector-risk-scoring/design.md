# 변경 설계

## 기존 구조와 변경할 부분

| 현재 | 변경 |
|---|---|
| [graph.py](../../../scamshield/graph.py) `build_graph(roles, jev=fake_jev, ...)` | `build_graph(roles, utterance_filter=..., scorer=..., verify_judge=..., ...)`로 세 port 주입 |
| `detect_with_jev` 한 Node가 최초 판단·재판단 | filter_utterance · score_risk · judge_verify · apply_verification 네 Node |
| VERIFY에 risk ≥ 0.6(Fake Jev 데모 값) | VERIFY에 risk ≥ suspect_threshold(설정, 초기 0.5) |
| Jev가 risk 반환 | RiskScorer는 utterance·call 점수만, 결합·감쇠·phase는 score_risk Node |
| Verify 요청 없음이면 phase 유지 | 요청 없음이면 SUSPECT로 복귀 |
| [jev.py](../../../scamshield/jev.py) Fake Jev가 risk·phase 결정 | Fake VerifyJudge(사건번호 진입 규칙)와 TypeSafe Jev adapter |
| — | 새 모듈: 점수 port·벡터 adapter, 임베딩·벡터 저장소 adapter, 적재 스크립트 |
| [cli.py](../../../scamshield/cli.py) `--offline` | offline은 모든 Fake 대역, 그 외는 실제 adapter를 조립 |

공통 State 필드·Agent·Tool·checkpoint는 바꾸지 않는다. 상세 계약은 [설계 기준](../../../docs/design/risk-scoring.md)에 있다.

## 책임·인터페이스·데이터 흐름

모듈 배치(구현 시 조정 가능):

- `scamshield/risk.py`: `RiskScorer`·`RiskScore`, `VectorRiskScorer`, `Embedder`·`ScamVectorStore` Protocol과 In-memory 대역.
- `scamshield/judges.py`: `UtteranceFilter`·`VerifyJudge` port와 Fake·TypeSafe Jev adapter. 두 Jev adapter는 같은 TypeSafe client를 공유한다.
- `scamshield/adapters/`: `GeminiEmbedder`, `PgVectorStore`.
- `scripts/ingest_dataset.py`: JSONL → 임베딩 → pgvector.
- 로컬 DB: `compose.yaml`의 pgvector 서비스, `.env.example`에 `DATABASE_URL`·`TYPESAFE_API_KEY` 추가.

데이터 흐름: update_context → filter_utterance(utterance·최근 대화 → FilterDecision, 일상이면 종료) → score_risk(utterance·transcript·previous_risk → RiskScore) → 기준 비교 → judge_verify(transcript·phase·results → VerifyDecision) → 기존 Agent/Tool 경로 → apply_verification.

의존성 후보: `psycopg[binary]`, `pgvector`(Python), `typesafe-sdk`. 모두 구현 단계에서 lock에 추가하고 버전을 기록한다. LangChain의 vector store 추상화는 쓰지 않는다. 검색 SQL 하나라 직접 쓰는 편이 port 경계가 명확하다.

## 선택·대안·trade-off

- **phase 결정을 port 밖에 둔다.** adapter는 점수만 반환하고 threshold 비교는 Graph가 한다. ML 모델로 바꿔도 단계 정책이 한 곳에 남는다. 대신 adapter가 자체 판단을 내리는 모델이면 점수로 변환해 넘겨야 한다.
- **Tool 결과 뒤 Jev 재판단을 규칙으로 바꾼다(사용자 채택).** Jev가 VERIFY 진입만 맡으면 조회 결과 해석은 단순 규칙으로 충분하고, WARN을 재현 가능하게 테스트할 수 있다. 결과 종류가 늘면 규칙을 추가해야 한다.
- **Embedder·VectorStore도 Protocol로 둔다.** 사용자가 요청한 교체 경계는 점수와 VERIFY 판단이지만, API·DB 없는 테스트를 위해 내부 의존성도 대역이 필요하다. 필요 이상의 factory·registry는 만들지 않는다.

## 미정 사항과 검증 방법

미정 수치·규칙은 [설계 기준의 미확정 사항](../../../docs/design/risk-scoring.md#미확정-사항)에서 관리한다. 검증은 [spec](spec.md)의 완료 조건 표를 따른다.

## 관련 상위 설계와 기준 문서

- [설계 기준](../../../docs/design/risk-scoring.md) · [MVP 전체 스펙](../../../docs/design/state-and-graph.md) · [proposal](proposal.md)
