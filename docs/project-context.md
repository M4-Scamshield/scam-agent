# 사용자 제공 프로젝트 컨텍스트

출처: 2026-10-10 사용자가 전달한 「ScamShield — 실시간 보이스피싱 탐지 및 Stateful Multi-Agent 대응 시스템」과 후속 대화. 아래 내용은 전달된 방향을 보존한 것이며, 새 상세 설계나 구현 완료 보고가 아니다.

## 목적과 첫 완료 조건

컴퓨터공학 졸업프로젝트이자 AI Agent·LangChain·LangGraph 학습 프로젝트다. 분류 모델 연구보다 통화 상태 유지, 역할이 다른 Agent, Tool Calling, 검증 결과 반영과 반복 판단을 경험하는 것이 핵심이다.

첫 완료 조건은 한 통화에서 다음 데모가 실제 코드로 동작하는 것이다.

1. 「서울중앙지검입니다.」 → Jev → OBSERVE → 행동 없이 종료.
2. 「고객님 계좌가 범죄에 연루됐습니다.」 → Jev → SUSPECT → 확인 행동 안내.
3. 「사건번호는 2026-12345입니다.」 → Jev → VERIFY → Verify Agent가 `case_lookup` 선택.
4. Mock 조회 결과 `NOT_FOUND` 저장 → Jev 재판단 → WARN → 고정 경고.

## 사용자가 확정한 방향

| 항목 | 방향 |
|---|---|
| Framework | LangChain + LangGraph |
| Detection·phase 결정 | Jev |
| Jev 입력 | 전체 한국어 Transcript + 이전 phase + 기존 검증 결과 |
| Jev 출력 | `risk`, `phase`, 선택적인 `signals` |
| Phase | OBSERVE, SUSPECT, VERIFY, WARN |
| Agent | Suspect Agent, Verify Agent의 두 역할 |
| Trigger | 새로운 STT 발화의 도착 |
| 입력 경계 | `callId`, `utterance` |
| Transcript | 통화 시작 이후 전체 발화를 State에 누적 |
| Persistence | LangGraph Checkpointer, MVP는 InMemorySaver |
| 통화 구분 | `thread_id = callId` |
| 서버 재시작 복구 | MVP 범위 밖 |
| WARN | 별도 Agent 없이 고정 Warning Node |

Suspect Agent는 전체 대화와 현재 State를 보고 사용자에게 확인 행동을 안내하며 초기 외부 Tool은 없다. Verify Agent는 대화를 직접 읽고 Tool과 인자를 선택하며 검증 결과를 확인한다. 검증 결과는 State에 저장한 뒤 Jev가 다시 판단한다. 정상 검증 이후 위험 단계가 내려가는 전이도 가능해야 한다.

사용자는 ScamShield 내부의 멀티 에이전트 구성을 원한다고 명확히 했다. 이는 개발 도구의 병렬 작업 에이전트를 요청한 것이 아니다.

## MVP에서 제외한 것

- Kafka·RabbitMQ 등 MQ, Redis, 별도 Conversation DB, Microservice, 복잡한 Event Sourcing.
- Transcript 요약, Sliding Window, Long-term Memory, Context 압축, 별도 번역 LLM.
- Supervisor Agent·LLM, Evidence Extraction Agent·Node·LLM, Observe Agent, Warn Agent, 별도 Response Agent.
- Agent 간 비동기 분산 실행, 실제 필요 없는 interface·factory·strategy와 추가 인프라.

State의 출발점은 `transcript`, `phase`, `risk`, `signals`, `verification_results`, `response`다. `summary`, `recent_window`, `long_term_memory`, `pending_events`, 위험도 이력 배열, `extracted_entities`, 별도 evidence store는 현재 요구사항에 없다.

도구는 Mock 데이터나 간단한 함수로 시작할 수 있다. `phone_lookup`, `case_lookup`, `url_lookup`, `account_lookup`은 제공할 수 있는 예시다. Jev의 risk는 Agent의 응답과 별개로 UI에 전달한다.

## 아직 열려 있는 사항

- Jev의 정확한 서비스·모델·API 문서, 질문 schema, risk 계산과 phase 계약.
- Phase 전이의 세부 정책과 VERIFY 재판단의 종료 규칙.
- `signals` 사용 여부와 구체적인 검증 결과 schema.
- LLM Provider·Model, STT Provider 최종 선택과 Mock 데이터 형식.
- HTTP·WebSocket 등 프론트엔드 통신 방식과 내부 Node 이름.
- 실제 코드 구조와 실행 환경. FastAPI는 사용자 문서의 추천 방향이며 아직 구현 확정 사항이 아니다.

예시의 위험도 수치는 시나리오 설명이며 실제 서비스의 threshold가 아니다. RTZR은 STT 후보로 언급됐을 뿐 확정되지 않았다.

## 작업 범위에 관한 합의

이번 작업은 `Downloads/aTopsMigrator`의 문서 탐색·작업 연속성 방식을 참고한 Harness 구성이다. 루트 AGENTS.md는 구현 전·중·후의 핵심 행동과 문서·스킬의 사용 시점을 안내하고, 세부 절차·재개 방법·기록 크기·검증 명령은 docs/harness/workflow.md에서 관리한다. 새 작업은 관련 아키텍처·설계를 먼저 읽고, 기존 작업 재개는 change의 진행·인계 기록부터 확인한다. 공통 작업과 문서 동기화는 스킬로 연결한다. 상세 설계 문서 작성은 다음 단계다.

사용자는 변경별 기록도 참고 저장소의 OpenSpec 형식으로 관리하도록 요청했다. 공통 방법은 harness에 유지하고, 변경의 목적·요구·설계·진행·검증은 openspec/changes의 proposal·spec·design·tasks·work로 구분한다.

큰 설계 변경이 필요하면 기존 설계의 문제·대안·trade-off를 제안 상태로 기록한다. 사용자가 채택하기 전에는 확정 방향을 대체하지 않는다. 사용자 지시에 이미 포함된 작은 구현과 수정은 해당 범위 안에서 진행한다.
