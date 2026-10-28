# 사용자 제공 프로젝트 컨텍스트

## 현재 확정 방향 — 2AS

2026-10-23 사용자가 기존 아키텍처를 변경했다. Jev에 STT 결과를 보내 보이스피싱 Yes/No와 확률을 받아 State에 저장한다. Yes이면 전체 대화와 그 결과를 Gemini에 전달해 근거 요약과 대응 안내를 남기고, No이면 아무 대응 없이 종료한다. 기존 Suspect/Verify·phase·Mock 조회 구조를 이번 구현에서 대체한다. 실제 STT 제품을 연결하기 전 텍스트 입력 인터페이스부터 만든다. 불필요한 코드 제거와 최종 그래프 출력도 요청했다.

현재 계약은 [2AS State·Graph](design/state-and-graph.md), 구현 상태는 [아키텍처](architecture/overview.md), 검증과 다음 행동은 [2AS work](../openspec/changes/jev-gemini-two-agent/work.md)를 따른다.

## 이전 구조의 사용자 맥락

아래는 2AS 전환 이전의 사용자 결정과 미정 사항을 보존한 역사 자료다. 현재 구조와 충돌하는 phase·조회·역할 정책은 위의 2AS 방향으로 대체됐으며, 후속 초안은 자동 채택되지 않는다.

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
| Jev 출력 적용 | Q8 Option A: detect_with_jev가 출력 schema·허용 phase 전이를 검사한 뒤 State에 반영. 최초 판단·검증 후 재판단 모두 적용. 검증 실패는 자동 재시도 없이 오류 반환(Q11). 데모 risk 0~1·VERIFY >= 0.6. 실제 Jev 척도/기준은 후속 범위 |
| Jev·Agent 실패 | Q11 Option A 부분 채택: 호출·출력 검증 실패 시 자동 재시도 없이 이번 실행의 오류 반환. 데모에서는 실행 오류 시 통화 시나리오를 중단하고 새 callId로 처음부터 재시작 |
| Tool 실행 실패 | 현재 실행 예외/잘못된 결과는 ERROR로 저장하고 Jev 재판단. Tool 재호출 없이 Q4의 1회 제한 유지. 공통 형식에는 TIMEOUT도 남겨두지만 시간 초과 감지/취소/늦은 완료는 후속 구현 범위 |
| signals 보관 | Q9 Option A: MVP ScamState에서 제외. Jev의 선택적 출력 가능성과 State 저장 여부는 구분 |
| 사용자 안내 response | Q10 Option A: State·checkpoint에 이번 안내를 저장하고 update_context가 새 STT turn 시작 시 None으로 초기화. suspect_agent·warn과 VERIFY 종료를 처리하는 기존 Node가 작성 |
| Phase | OBSERVE, SUSPECT, VERIFY, WARN |
| phase 전이 | WARN 하향 금지. 나머지는 Jev 판단에 따라 유연한 전이, VERIFY에는 의심·검증 정보·필요성 요구 |
| OBSERVE → VERIFY | 일정 risk 기준 이상 + 검증 가능한 정보·검증 필요성이 있어야 진입. 전화번호 등장만으로 진입하지 않음. 이전 SUSPECT 기록은 필수 아님. 데모 VERIFY 기준 0.6 이상. 실제 Jev 척도/기준은 후속 범위 |
| Agent | Suspect·Verify의 두 역할. Gemini Developer API/gemini-3.8-flash 공유, prompt·Tool 권한만 분리. 연결 구현·API 없는 SDK 검사·실제 안내/Tool Calling 검증 완료 |
| Trigger | 현재는 CLI 텍스트 발화 입력. 실제 연결에서는 양쪽 화자의 새 final STT 발화 도착 |
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
| 같은 통화 실행 순서 | CLI가 turn 완료를 기다려 세 발화를 순차 실행. 별도 lock/큐·timeout wrapper/취소 검증은 첫 범위 밖. 늦은 결과 반영은 후속 개선 |

Suspect Agent는 전체 대화와 현재 State를 보고 사용자에게 확인 행동을 안내하며 초기 외부 Tool은 없다. Verify Agent는 대화를 직접 읽고 Tool과 인자를 선택한다. 독립 tool_execution Node가 Tool을 실행하고 검증 결과를 State에 저장한 뒤 Jev가 다시 판단한다. 정상 검증 이후 위험 단계가 내려가는 전이도 가능해야 한다.

2026-10-12 후속 설명에서 사용자는 실제 통화에서 상대방과 사용자 양쪽의 STT가 필요함을 확인했다. 실제 연결에서는 화자를 구분해 같은 통화에 누적해야 한다. 현재 CLI 발화·list[str] State에는 화자 정보가 없고, 화자 정보와 STT 전달/State schema는 후속 설계에서 정한다.

현재 상대방 발화는 DEMO_UTTERANCES의 세 문장 또는 직접 입력이며 상대방 AI는 없다. 세 번 입력 후 종료하는 것은 CLI의 데모 선택이고 Graph의 turn 횟수 제한이 아니다. Fake Jev의 검증 진입 규칙과 Mock 등록 번호 때문에 모든 입력이 일반적인 탐지·조회 흐름으로 이어지지는 않는다. 정확한 조건과 실제 Gemini/Fake/Mock의 구분은 [데모 스펙](design/state-and-graph.md)과 [현재 구성](architecture/overview.md)을 따른다.

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

2026-10-12 데모데이 리뷰 반영: 사용자는 필요한 선택만 확인하고 나머지는 에이전트가 진행하도록 요청했다. 데모 risk 0~1·VERIFY 기준 0.6·phase별 fixture 0.1/0.5/0.7/0.9, 대화와 해당 사건번호 결과를 함께 읽는 Fake Jev, CLI 순차 실행과 관찰 출력, 오류 시 새 callId 재시작을 선택했다. 실패 뒤 같은 통화의 재개·동시 요청 제어·timeout 취소/늦은 완료·다양한 오류 fixture는 후속 범위로 옮겼다. 이는 기존 공통 설계보다 첫 구현 범위를 줄인 후속 결정이다.

사용자는 처음 LLM API가 없고 무료 Gemini 또는 GPT로 실험할 계획이라고 답했다. Gemini Developer API/gemini-3.8-flash를 두 역할의 공유 기본값으로 선택했다. 이후 키를 로컬 `.env`에 제공했고 SDK 연결·API 없는 검사와 실제 Gemini 안내/Tool Calling·최종 WARN을 확인했다. 계정별 무료 한도를 검증한 것은 아니다. GPT는 후속 비교 후보이며 무료 API로 가정하지 않는다. 공식 요금/Function Calling 근거는 [전체 스펙](design/state-and-graph.md)에 연결한다.

사용자는 현재 데모의 역할별 LLM 호출 방식을 허용하되 후속 단계에서는 구현한 Agent를 호출하는 구조로 전환하도록 명시적으로 요청했다. [Agent 실행 구조 TODO](design/state-and-graph.md#todo--데모-이후-agent-실행-구조로-전환)에 미완료 작업으로 기록했다. 현재 데모와 Agent 런타임 구현 완료는 구분한다.

실제 Jev/기관 조회·STT·HTTP/WebSocket·프론트·운영 복구/cleanup은 첫 데모 뒤 범위다. [데모 구현](architecture/overview.md)·API 없는 CLI/테스트와 실제 Gemini 안내/Tool Calling 검증을 완료했다. 이는 역할별 LLM 호출 데모 완료이며 후속 Agent 실행 런타임 전환과 구분한다.

## 작업 범위에 관한 합의

초기 작업은 `Downloads/aTopsMigrator`의 문서 탐색·작업 연속성 방식을 참고한 Harness 구성이었다. 루트 AGENTS.md는 구현 전·중·후의 핵심 행동과 문서·스킬의 사용 시점을 안내하고, 세부 절차·재개 방법·기록 크기·검증 명령은 docs/harness/workflow.md에서 관리한다. 새 작업은 관련 아키텍처·설계를 먼저 읽고, 기존 작업 재개는 change의 진행·인계 기록부터 확인한다. 공통 작업과 문서 동기화는 스킬로 연결한다.

2026-10-12 구현 요청은 [이슈 #1](https://github.com/M4-Scamshield/scam-agent/issues/1)과 로컬 스펙을 기준으로 데모를 구현하고 검증하는 것이었다. 기존 미커밋 문서를 보존하며 first-demo 기록에서 Agent 대역 핵심 Graph 검증 → Gemini 연결/Tool Calling → CLI 실행/README 순서로 진행했다. 실제 Gemini 데모 성공 후 리뷰 P2를 수정하고 API 없는 31개 검사로 확인했다. 후속 문서 정합성 감사에서 기록을 맞췄으며, 사용자 요청에 따라 Graph·Gemini·CLI·문서로 나눠 커밋했다. 이어 push·PR 생성 요청을 받아 [PR #2](https://github.com/M4-Scamshield/scam-agent/pull/2)를 main 대상으로 생성했다. 리뷰·merge는 후속 단계다.

사용자는 변경별 기록도 참고 저장소의 OpenSpec 형식으로 관리하도록 요청했다. 공통 방법은 harness에 유지하고, 변경의 목적·요구·설계·진행·검증은 openspec/changes의 proposal·spec·design·tasks·work로 구분한다.

큰 설계 변경이 필요하면 기존 설계의 문제·대안·trade-off를 제안 상태로 기록한다. 사용자가 채택하기 전에는 확정 방향을 대체하지 않는다. 사용자 지시에 이미 포함된 작은 구현과 수정은 해당 범위 안에서 진행한다.
