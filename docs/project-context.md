# 사용자 제공 프로젝트 컨텍스트

출처: 2026-10-10 사용자가 전달한 「ScamShield — 실시간 보이스피싱 탐지 및 Stateful Multi-Agent 대응 시스템」과 후속 State·LangGraph 설계 요청. 아래 내용은 전달된 방향을 보존한 것이며, 구현 완료 보고가 아니다. 상세 계약의 기준은 [ScamShield MVP 전체 스펙](design/state-and-graph.md)에 있다.

## 목적과 첫 완료 조건

컴퓨터공학 졸업프로젝트이자 AI Agent·LangChain·LangGraph 학습 프로젝트다. 분류 모델 연구보다 통화 상태 유지, 역할이 다른 Agent, Tool Calling, 검증 결과 반영과 반복 판단을 경험하는 것이 핵심이다.

첫 완료 조건은 한 통화에서 다음 데모가 실제 코드로 동작하는 것이다.

1. 「서울중앙지검입니다.」 → Jev → OBSERVE → 행동 없이 종료.
2. 「고객님 계좌가 범죄에 연루됐습니다.」 → Jev → SUSPECT → 확인 행동 안내.
3. 「사건번호는 2026-12345입니다.」 → Jev → VERIFY → Verify Agent가 `case_lookup` 선택.
4. Mock 조회 결과 `NOT_FOUND` 저장 → Jev 재판단 → WARN → 고정 경고.

## 합의된 방향과 위임에 따른 공통 보완

기존 사용자 결정과 후속 위임에 따라 에이전트가 보완한 현재 설계를 함께 요약한다. 구분과 근거는 아래 공통 설계/후속 스펙 항목과 기준 설계·work를 따른다.

| 항목 | 방향 |
|---|---|
| Framework | LangChain + LangGraph |
| Detection·phase 결정 | Jev |
| Jev 입력 | 전체 한국어 Transcript + 이전 phase + 기존 검증 결과 |
| Jev 출력 | `risk`, `phase`, 선택적인 `signals` |
| Jev 출력 적용 | Q8 Option A: detect_with_jev가 출력 schema·허용 phase 전이를 검사한 뒤 State에 반영. 최초 판단·검증 후 재판단 모두 적용. 검증 실패는 자동 재시도 없이 오류 반환(Q11). risk 범위와 기준 수치는 미정 |
| Jev·Agent 실패 | Q11 Option A 부분 채택: 호출·출력 검증 실패 시 자동 재시도 없이 이번 실행의 오류 반환. 데모에서는 중간 재개 없이 새 발화로 새 turn을 시작하고 마지막 저장 State를 유지 |
| Tool 실행 실패 | Q11의 Tool 실패 Option A: 오류·timeout을 검증하지 못한 결과로 누적 저장하고 Jev 재판단. Tool 재호출 없이 Q4의 1회 제한 유지. 실행 상태는 Q2의 ERROR/TIMEOUT으로 구분. 공통 실패 상세는 code/message, timeout 뒤 늦은 결과는 폐기. 도구별 상세 오류는 후속 스펙에서 정함 |
| signals 보관 | Q9 Option A: MVP ScamState에서 제외. Jev의 선택적 출력 가능성과 State 저장 여부는 구분 |
| 사용자 안내 response | Q10 Option A: State·checkpoint에 이번 안내를 저장하고 update_context가 새 STT turn 시작 시 None으로 초기화. suspect_agent·warn과 VERIFY 종료를 처리하는 기존 Node가 작성 |
| Phase | OBSERVE, SUSPECT, VERIFY, WARN |
| phase 전이 | WARN 하향 금지. 나머지는 Jev 판단에 따라 유연한 전이, VERIFY에는 의심·검증 정보·필요성 요구 |
| OBSERVE → VERIFY | 일정 risk 기준 이상 + 검증 가능한 정보·검증 필요성이 있어야 진입. 전화번호 등장만으로 진입하지 않음. 이전 SUSPECT 기록은 필수 아님. risk 척도·기준 수치는 Jev 스펙에서 정함 |
| Agent | Suspect Agent, Verify Agent의 두 역할 |
| Trigger | 새로운 STT 발화의 도착 |
| 입력 경계 | `callId`, `utterance`. Q6 Option A: 데모에서는 완성된 final utterance를 중복 없이 한 번씩 전달. partial STT·동일 요청 재전송은 범위 밖, 발화 ID 기반 중복 제거는 현재 추가하지 않음 |
| Transcript | 통화 시작 이후 전체 발화를 State에 누적 |
| 첫 통화 초기값 | Q12: update_context에서 phase=OBSERVE, transcript=[], verification_results=[], response=None을 준비. risk는 최초 성공 Jev 판단 전 None. 기존 통화의 누적 상태는 초기화하지 않음 |
| Persistence | LangGraph Checkpointer, MVP는 InMemorySaver. Q13 Option A: sync로 checkpoint 저장 완료 후 다음 step 진행 |
| 통화 구분 | `thread_id = callId`. Q14에 따라 새 통화마다 고유 callId, 같은 통화의 STT는 동일 callId 사용 |
| State·checkpoint 수명 | Q14 Option A: 초기 데모는 통화 종료 후에도 서버 프로세스 생존 동안 보관. 종료 이벤트 기반 삭제·자동 cleanup은 추가하지 않음 |
| 서버 재시작 복구 | MVP 범위 밖 |
| WARN | 별도 Agent 없이 고정 Warning Node |
| 검증 결과 보관 | 후속 답변에서 통화 전체 Tool 검증 결과 누적(Q2 Option A)과 tool·input·status·result·is_mock 공통 형식을 채택. tool_execution이 기존 결과 + [새 결과] 전체 목록을 기본 교체로 저장하고 append reducer는 사용하지 않음. 상세 계약은 [설계 Q2](design/state-and-graph.md#q2-verification_results는-전체-누적일까-최근-검증-batch일까) 참고 |
| VERIFY 실행 범위 | Q4 Option A: STT turn당 Tool 최대 1회와 결과 저장 후 Jev 재판단 1회. 다시 VERIFY여도 같은 turn에서는 재검증 없이 종료 |
| Tool 실행 위치 | Q7 Option A: verify_agent Node가 Tool·인자를 선택하고 독립 tool_execution Node가 실행·결과 저장. State의 tool_request={tool,input}로 전달·checkpoint 보관·실행 후 소비. verification_attempted로 같은 turn의 재실행 방지 |
| 같은 통화 실행 순서 | Q5 Option A 확정: 같은 callId의 turn을 순차 처리하고 Tool 대기에 시간 제한을 둠. Tool timeout은 실패 결과로 저장해 Jev 재판단(Q11). 데모 기본 timeout 5초·설정 가능, 가능한 취소를 시도하고 늦은 결과는 폐기. Tool 대기 중 새 발화 판단·늦은 결과 반영은 후속 개선으로 연기 |

Suspect Agent는 전체 대화와 현재 State를 보고 사용자에게 확인 행동을 안내하며 초기 외부 Tool은 없다. Verify Agent는 대화를 직접 읽고 Tool과 인자를 선택한다. 독립 tool_execution Node가 Tool을 실행하고 검증 결과를 State에 저장한 뒤 Jev가 다시 판단한다. 정상 검증 이후 위험 단계가 내려가는 전이도 가능해야 한다.

사용자는 ScamShield 내부의 멀티 에이전트 구성을 원한다고 명확히 했다. 이는 개발 도구의 병렬 작업 에이전트를 요청한 것이 아니다.

## MVP에서 제외한 것

- Kafka·RabbitMQ 등 MQ, Redis, 별도 Conversation DB, Microservice, 복잡한 Event Sourcing.
- Transcript 요약, Sliding Window, Long-term Memory, Context 압축, 별도 번역 LLM.
- Supervisor Agent·LLM, Evidence Extraction Agent·Node·LLM, Observe Agent, Warn Agent, 별도 Response Agent.
- Agent 간 비동기 분산 실행, 실제 필요 없는 interface·factory·strategy와 추가 인프라.

State의 출발 후보는 `transcript`, `phase`, `risk`, `verification_results`, `response`다. 초기 후보였던 `signals`는 Q9 Option A로 MVP State에서 제외했다. 후속 답변에서는 이번 발화 `utterance`와 누적 대화 `transcript`를 나누는 방향을 채택했다. [상세 설계 Q1](design/state-and-graph.md#q1-새-stt-입력을-어떻게-전달하고-transcript에-merge할까)에 따라 Graph 입력 channel utterance를 전달하고 update_context가 기존 transcript + [이번 발화]의 새 목록으로 교체한 뒤 utterance=None으로 비운다. Jev·Agent는 갱신된 전체 대화와 현재 State를 읽는다. `summary`, `recent_window`, `long_term_memory`, `pending_events`, 위험도 이력 배열, `extracted_entities`, 별도 evidence store는 현재 요구사항에 없다.

도구는 Mock 데이터나 간단한 함수로 시작할 수 있다. `phone_lookup`, `case_lookup`, `url_lookup`, `account_lookup`은 제공할 수 있는 예시다. Jev의 risk는 Agent의 응답과 별개로 UI에 전달한다.

## 전체 스펙의 통합 관리

[공통 실행 설계](design/state-and-graph.md)는 State·Node·분기·전달·종료·실패·통화 유지 규칙을 정리했다. 2026-10-11 사용자가 필요한 세부 선택을 에이전트에게 맡기고 공통 설계를 마저 진행하도록 요청했다. 에이전트는 기존 결정에 맞춰 Tool 요청 channel, 검증 시도 boolean, 미평가 risk=None, VERIFY 종료 안내, 실패 뒤 새 turn, 내부 결과/오류 경계와 timeout 기본값을 보완했다. 각 선택을 개별 사용자 답변으로 승인받았다고 기록하지 않는다.

후속 요청에서 사용자는 기존 문서를 전체 스펙으로 사용하고 싶다고 했다. 공통 규칙과 구성요소별 내부 계약·데모 검증 기준을 같은 문서에 통합했다. Mock case_lookup의 인자/결과, Agent 행동 지침·오류 분류는 에이전트가 작성한 내부 초안이며 실제 서비스 계약과 구분한다. 별도 구성요소 문서 작성은 필수가 아니다.

이 문서 안에서 남은 외부 연결·설정을 확정한다. 주요 항목은 다음과 같다.

- Jev: 실제 서비스/API·입출력 schema, risk 척도·범위·VERIFY 기준과 의미 조건.
- Agent: Provider·모델·prompt, 확인 행동 출력, 원시 Tool Calling 메시지를 공통 요청으로 변환하는 방법.
- Tool: 도구별 인자·정상 결과·세부 오류·Mock 데이터, 재조회/상충 결과 해석, 실제 도구에 맞춘 timeout 조정.
- 입력·응답 연결: STT Provider, 실제 재전송·callId 생성, HTTP/WebSocket 계약·중간 risk 전달·수신 큐 운영 한도.
- 구현: 실제 코드 구조·환경 동작·서비스 테스트. Python 설정은 있지만 서비스 실행 검증은 없다. FastAPI는 추천 방향이며 아직 선택하지 않았다.

예시 risk는 fixture이며 실제 threshold가 아니다. RTZR은 STT 후보다. 공통 timeout 5초도 데모 기본값이며 외부 조회 서비스의 보장이나 측정 결과가 아니다.

## 작업 범위에 관한 합의

초기 작업은 `Downloads/aTopsMigrator`의 문서 탐색·작업 연속성 방식을 참고한 Harness 구성이었다. 루트 AGENTS.md는 구현 전·중·후의 핵심 행동과 문서·스킬의 사용 시점을 안내하고, 세부 절차·재개 방법·기록 크기·검증 명령은 docs/harness/workflow.md에서 관리한다. 새 작업은 관련 아키텍처·설계를 먼저 읽고, 기존 작업 재개는 change의 진행·인계 기록부터 확인한다. 공통 작업과 문서 동기화는 스킬로 연결한다.

현재 요청은 기존 State·Graph 설계 문서를 기반으로 MVP 전체 스펙을 하나의 문서에 정리하는 것이다. 기존 정책을 유지하며 필요한 세부 선택은 에이전트가 진행한다. 확정 방향을 바꾸는 큰 설계 변경과 실제 외부 계약은 별도로 다룬다. 새 OpenSpec 구현 작업, LangGraph 코드, 실제 Jev 연동과 Tool 구현은 이번 단계에서 수행하지 않는다. Agent 행동 지침과 Tool별 내부 계약은 문서에 포함한다.

사용자는 변경별 기록도 참고 저장소의 OpenSpec 형식으로 관리하도록 요청했다. 공통 방법은 harness에 유지하고, 변경의 목적·요구·설계·진행·검증은 openspec/changes의 proposal·spec·design·tasks·work로 구분한다.

큰 설계 변경이 필요하면 기존 설계의 문제·대안·trade-off를 제안 상태로 기록한다. 사용자가 채택하기 전에는 확정 방향을 대체하지 않는다. 사용자 지시에 이미 포함된 작은 구현과 수정은 해당 범위 안에서 진행한다.
