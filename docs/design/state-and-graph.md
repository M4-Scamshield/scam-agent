# ScamShield MVP 전체 스펙

상태: **전체 스펙 초안 — 공통 실행 규칙 정리 완료, 구성요소 계약 초안 포함, 외부 연동·구현·실행 검증 미착수**. 2026-10-11 사용자가 기존 설계 문서를 전체 스펙으로 확장하고 싶다고 요청했다. 기존 결정은 유지하고 필요한 내부 계약을 보완했다. 외부 Jev API·Provider 정보처럼 확인이 필요한 항목은 미정으로 표시한다.

## 문서의 역할과 범위

이 문서는 **ScamShield MVP를 구현할 때 사용하는 통합 스펙**이다. 공통 State·Graph 규칙과 Jev·Agent·Tool의 역할/입출력/동작, 입력·응답 경계, 첫 데모의 검증 기준을 한 문서에서 관리한다. 별도 구성요소 설계 문서를 반드시 만들 필요는 없다. 이번 구성요소 보완은 에이전트가 선택한 내부 스펙 초안이며 실제 외부 서비스의 확인된 계약과 구분한다.

| 영역 | 이 문서에 담는 내용 |
|---|---|
| 목적·범위 | 첫 통화 데모, MVP 기능과 제외 범위 |
| 공통 실행 | State 소유권·초기화·누적, Node·Edge, 전이·검증 한도 |
| 구성요소 | Jev·Suspect·Verify·Tool의 내부 계약과 행동 지침 |
| 입력·응답 | turn 입력, 정상/오류 결과, 사용자 안내 |
| 통화 유지 | callId별 순차 처리, checkpoint, timeout·실패 뒤 다음 입력 |
| 검증·미정 사항 | 시나리오별 인수조건, 외부 연결 전 확인할 계약 |

첫 완료 목표는 한 통화에서 기관 사칭 대화 → 의심 안내 → 사건번호 Mock 조회 → 결과를 반영한 Jev 재판단 → WARN이 동작하는 것이다. 전체 한국어 대화·두 Agent·Tool Calling·State 유지가 MVP 중심이다. 서비스 코드·외부 연동은 이번 문서 작업에 포함하지 않는다.

Conversation DB·MQ·Redis·Microservice, 대화 요약·메모리 압축, Supervisor/번역/정보 추출 LLM, 여러 Tool 병렬 실행, 서버 재시작 복구는 MVP에 추가하지 않는다. 실제 STT·프론트 연결과 공공기관 조회는 외부 연결 계약 확인 뒤 진행한다.

현재 Python 의존성 설정은 있으나 서비스 State·Graph·Agent·Tool·테스트 코드는 없다. 기존 [first-demo](../../openspec/changes/first-demo/work.md)에서 설계 진행을 이어 기록한다. 문서 정리와 구현/실행 검증 완료는 구분한다.

## 실행 모델

- LangChain + LangGraph를 사용하며 새 final utterance 하나가 turn 하나를 시작한다. 입력 없는 background 실행은 없다.
- 같은 통화는 thread_id=callId와 같은 InMemorySaver 인스턴스를 사용한다. 새 통화에는 고유 callId를 사용한다.
- 전체 한국어 transcript와 통화 전체 verification_results를 보존한다. 요약·Sliding Window·별도 Conversation DB·evidence store는 두지 않는다.
- Jev가 risk·phase를 판단한다. Suspect와 Verify의 두 Agent, 고정 warn Node를 사용한다. Supervisor·번역·정보 추출 LLM은 추가하지 않는다.
- verify_agent와 tool_execution은 별도 부모 Graph Node다. Agent는 선택, 실행 Node는 실행과 결과 저장을 맡는다.
- 한 turn에서 실제 Tool 실행은 최대 1회, 결과 저장 후 Jev 재판단은 1회다. 자동 재시도는 없다.
- 데모 입력은 final utterance가 중복 없이 한 번씩 전달된다는 전제다. partial STT·동일 요청 재전송·발화 ID 기반 중복 제거는 이번 범위 밖이다. 실제로 반복해서 말한 동일 문장은 각각 새 발화다.

## State 책임과 내부 형식

다음은 구현할 공통 필드 계약이다. 실제 TypedDict/Pydantic 코드는 후속 구현에서 작성한다. callId는 실행 식별자로 받아 thread 설정에 전달하고 State에 중복 저장하지 않는다. 모든 channel은 기본 교체를 사용한다.

| 필드 | 초기값·의미 | 수정 책임 |
|---|---|---|
| utterance: str 또는 None | 이번 새 발화, update_context가 소비하면 None | 입력 경계·update_context |
| transcript: list[str] | 첫 통화 [], 통화 전체 발화 | update_context가 기존 목록 + [새 발화] 전체 목록으로 교체 |
| phase | 첫 통화 OBSERVE, 이후 최신 유효 판단 | 첫 초기화는 update_context, 이후 detect_with_jev |
| risk: float 또는 None | 첫 통화 None. 최초 성공 판단 전 미평가이며 0으로 대신하지 않음 | detect_with_jev |
| verification_results: list[VerificationResult] | 첫 통화 [], 통화 전체 검증 결과 | 첫 초기화는 update_context, 이후 tool_execution이 기존 목록 + [새 결과]로 교체 |
| response: str 또는 None | 새 turn마다 None, 이번 사용자 안내 | update_context·suspect_agent·warn 및 VERIFY 종료를 결정한 기존 Node |
| tool_request: ToolRequest 또는 None | 새 turn마다 None. 선택됐지만 아직 소비하지 않은 요청 | update_context·verify_agent·tool_execution |
| verification_attempted: bool | 새 turn마다 false. 이번 turn에서 Tool 실행을 시도하고 결과를 저장했는지 | update_context·tool_execution |

새 turn에서 phase·risk·대화·검증 결과를 초기값으로 덮어쓰지 않는다. response·tool_request·verification_attempted는 turn 실행 값이므로 매번 초기화한다. Tool 오류/timeout 결과를 저장한 경우도 verification_attempted=true다. Jev 재판단에서는 초기화를 반복하지 않는다.

미평가 risk는 None으로 선택했다. 판단 후 risk는 유한한 숫자여야 한다. 숫자의 척도·허용 범위와 threshold는 이 문서의 Jev 스펙에서 확정할 계약을 적용하며 현재 0~1을 가정하지 않는다. signals는 MVP State에 저장하지 않는다. 별도 previous_phase·phase 이력·messages·Tool 실행 counter는 추가하지 않는다.

### ToolRequest

공통 형식은 {tool: Tool 이름, input: 구조화 인자 object}다. verify_agent는 등록된 Tool의 schema로 검증한 요청 하나 또는 None을 반환한다. Tool별 인자 이름·타입은 이 문서의 Verification Tool 스펙을 따른다. Agent의 원시 Tool Calling 메시지는 이번 Agent 호출 안에서 처리하고 부모 State에는 이 요청만 저장한다.

요청은 State·checkpoint에 보관한다. tool_execution은 선택된 요청을 읽고 결과 목록·tool_request=None·verification_attempted=true를 한 Node 업데이트로 반환한다. 새 turn의 초기화에서도 이전 요청을 비워 오래된 요청이 실행되지 않게 한다.

이 형식을 선택한 이유는 분리된 두 Node의 연결을 checkpoint에서 확인할 수 있고, Agent 라이브러리의 내부 메시지 형식을 부모 State에 퍼뜨리지 않기 때문이다. verification_attempted는 기존 detect_with_jev Node가 최초 판단과 재판단을 구분하도록 하는 단순 boolean이다. 새 재판단 Node나 반복 counter를 만들지 않는다.

### VerificationResult

| 필드 | 의미 |
|---|---|
| tool | 실행한 Tool 이름 |
| input | 조회에 사용한 구조화 인자 |
| status | 실행 상태 OK / ERROR / TIMEOUT |
| result | 조회 내용 또는 실패 상세. JSON으로 표현 가능한 값 |
| is_mock | Mock 데이터 여부(boolean) |

OK는 정상 실행이며 안전 판정이 아니다. 정상 조회의 NOT_FOUND는 result에 저장한다. ERROR/TIMEOUT은 검증하지 못함이며 사기·안전·WARN을 강제하지 않는다. Mock 여부는 실행할 Tool의 설정에서 정하고 Agent가 임의로 지정하지 않는다. Mock 미등록과 실제 기관 미등록을 구분한다.

Tool 실행 예외·결과 schema 위반·timeout은 실행 Node에서 실패 결과로 정규화한다. 실패 상세는 {code, message} object를 사용하며 세부 오류 code와 도구별 정상 result는 Tool 스펙이 정한다. 내부 예외 객체를 result에 직접 저장하지 않는다. 정상·실패 모두 기존 결과 + [새 결과]의 전체 목록을 저장하며 append reducer를 함께 사용하지 않는다. Jev 재판단에서 같은 결과를 다시 추가하지 않는다.

## Node와 실행 순서

| Node | 주요 읽기 | 주요 쓰기·동작 | 다음 실행 |
|---|---|---|---|
| update_context | 이번 utterance·복원된 State | 첫 통화 기본값, 새 대화 추가, utterance 소비, turn 실행 값 초기화 | detect_with_jev |
| detect_with_jev | 전체 transcript·호출 직전 phase·누적 검증 결과 | Jev 출력 검증 후 risk·phase 적용. verification_attempted로 재판단 구분 | phase에 따른 분기 |
| suspect_agent | 전체 대화·현재 State | 외부 Tool 없이 이번 확인 행동 response 생성 | END |
| verify_agent | 전체 대화·현재 State·사용 가능한 Tools | 유효한 요청 하나 또는 None, 요청 없음이면 종료 안내 | 요청 있으면 tool_execution, 없으면 END |
| tool_execution | tool_request·기존 결과·Tool 설정 | 최대 1회 실행, 정상/실패 결과 저장, 요청 소비·시도 표시 | detect_with_jev |
| warn | 고정 문구 | 경고 response | END |

```mermaid
flowchart TD
    S([새 final utterance]) --> U[update_context]
    U --> D[detect_with_jev]
    D -->|OBSERVE| E([이번 turn 종료])
    D -->|SUSPECT| A[suspect_agent]
    A --> E
    D -->|VERIFY: 아직 검증 시도 전| V[verify_agent]
    V -->|요청 1개| T[tool_execution]
    V -->|요청 없음: 안내| E
    T --> D
    D -->|VERIFY: 검증 후 재판단, 안내| E
    D -->|WARN| W[warn]
    W --> E
```

Conditional Edge는 적용된 phase와 verification_attempted를 읽어 경로만 선택한다. 새 위험 판단이나 결과 해석을 맡지 않는다. detect_with_jev는 외부 판단을 검증한 뒤 적용하고 Tool 요청은 verify_agent가 검증한다. 검증 오류는 정상 routing으로 보내지 않는다.

한 번의 실행 경로는 update_context → 최초 Jev → phase별 처리다. VERIFY이면 선택 → Tool 결과 저장 → 같은 detect_with_jev의 재판단으로 이어진다. 재판단 뒤 VERIFY는 종료하고, OBSERVE/SUSPECT/WARN은 각 종료 경로를 따른다. 이 Graph 구조와 verification_attempted 검사로 같은 turn의 두 번째 Tool 실행을 막는다. Tool 실행 Node도 이미 true인 요청을 실행하지 않고 실행 계약 오류로 중단한다.

## Phase 전이와 검증 책임

기존 WARN 고정·유연한 진입/하향 방향에 맞춰 나머지 전이도 다음 범위로 정리했다. 허용은 Jev가 해당 phase를 반환할 수 있다는 뜻이며 코드가 상태를 강제로 올리거나 내린다는 뜻이 아니다.

| 이전 phase | OBSERVE | SUSPECT | VERIFY | WARN |
|---|---|---|---|---|
| OBSERVE | 허용 | 허용 | 조건부 허용 | 허용 |
| SUSPECT | 허용 | 허용 | 조건부 허용 | 허용 |
| VERIFY | 허용 | 허용 | 조건부 유지 | 허용 |
| WARN | 금지 | 금지 | 금지 | 유지 |

VERIFY에는 검증 가능한 정보·검증 필요성·충분한 의심이 요구된다. OBSERVE에서 바로 VERIFY로 갈 수 있으며 이전 SUSPECT 이력은 필수가 아니다. 새 위험 정보나 정상 검증으로 OBSERVE/SUSPECT까지 하향할 수 있으나 같은 통화의 WARN 하향은 허용하지 않는다. VERIFY 유지 허용과 같은 turn에서 추가 Tool 실행 금지는 별개다.

Jev 스펙은 risk의 척도·범위·VERIFY 진입 기준과 의미 조건을 정한다. 공통 코드의 detect_with_jev는 유한 숫자·phase enum·전이표와 Jev 스펙에서 정한 수치 조건을 검사한다. 검증 가능한 정보와 필요성을 판단하는 책임은 Jev·Verify의 상세 계약에 둔다. 정책 위반 시 출력을 적용하지 않고 오류 반환하며 자동 phase 보정은 하지 않는다. 최초 판단과 재판단 모두 같은 검증 원칙을 적용한다.

## 종료·출력·실패

### 정상 종료

| 종료 상황 | 이번 response·처리 |
|---|---|
| OBSERVE | None, 사용자 행동 안내 없음 |
| SUSPECT | suspect_agent의 확인 행동 안내 |
| WARN | 고정 경고 문구 |
| VERIFY에서 유효한 선택 결과가 요청 없음 | verify_agent가 고정 안내를 저장하고 END. Tool·재판단 없음 |
| 결과 저장 후 Jev가 다시 VERIFY | detect_with_jev가 고정 안내를 저장하고 END. 추가 Tool 없음 |

요청 없음 안내의 기본 문구는 “현재 정보로는 조회할 대상을 정하기 어렵습니다. 상대방에게 기관명과 확인 가능한 정보를 요청하세요.”다. 재판단이 VERIFY인 종료 안내는 “확인한 결과만으로는 판단하기 어렵습니다. 상대방의 주장을 추가로 확인하고, 확인 전 송금이나 개인정보 제공을 보류하세요.”다. 문구 개선은 Agent/응답 스펙에서 할 수 있으나 종료와 response 작성 책임은 유지한다.

WARN 기본 문구는 “현재 통화는 보이스피싱일 가능성이 매우 높습니다. 송금, 개인정보 제공, 앱 설치를 중단하고 통화를 종료하세요.”다. Tool 결과만으로 WARN을 강제하지 않고 Jev 판단을 따른다.

내부 정상 결과는 {callId, risk, phase, response, verification_results}다. 정상 완료에는 유효한 Jev 판단이 있어야 하므로 risk는 숫자다. transcript·tool_request·실행 flag는 외부 정상 결과에 포함하지 않는다. 실제 HTTP/WebSocket envelope와 중간 risk 전송은 입력/응답 연결 스펙에서 정한다.

### 실행 오류

- 입력 경계에서 비어 있는 callId·utterance나 잘못된 타입을 거부하고 State를 수정하지 않는다. transcript에는 검증한 발화 원문을 보존한다.
- Jev·Agent 호출 실패/출력 검증 실패는 자동 재시도 없이 이번 실행 오류다. 이전 phase를 새 성공 판단으로 반환하지 않는다.
- Verify의 요청 없음은 유효한 선택 결과다. 알 수 없는 Tool·잘못된 인자·여러 요청은 Agent 출력 검증 실패이며 어느 Tool도 실행하지 않는다. 임의로 첫 요청을 선택하지 않는다.
- Tool 실행 예외·출력 오류·timeout은 검증 실패 결과로 저장하고 Jev 재판단한다. 재판단 Jev가 실패하면 실행 오류를 반환한다.
- checkpoint/State 저장·Graph 내부 계약 실패는 실행 오류다. 저장에 실패한 결과를 정상 처리 완료로 반환하지 않는다.

내부 오류 결과는 {callId, error: {stage, code, message}}다. stage는 input/jev/suspect_agent/verify_agent/tool_execution/checkpoint/runtime 중 실패 위치를 나타낸다. 정상 결과와 오류 결과는 구분하며 error는 State의 사용자 안내 response에 넣지 않는다. 상세 오류 code·외부 API 전달 형식은 각 연결 스펙에서 맞춘다.

### 실패 뒤 다음 발화

데모에서는 실패한 turn을 자동 재시도하거나 중간 checkpoint에서 재개하지 않는다. 실패한 실행을 종료한 뒤 **새 final utterance로 새 turn을 시작**하고 마지막으로 저장된 State를 이어 사용한다. 같은 발화 재전송은 데모 입력 계약 밖이다.

이미 저장된 transcript·성공 판단·검증 결과는 rollback하지 않는다. 예를 들어 최초 Jev 실패 뒤에는 이번 발화가 대화에 남을 수 있고, 결과 저장 후 Jev 재판단 실패 뒤에는 이번 검증 결과가 남는다. 다음 입력은 이 정보를 함께 읽되 update_context부터 시작하며 오래된 다음 실행 위치를 재개하지 않는다. 중간 phase=VERIFY가 남아 있어도 새 turn의 검증 한도는 초기화된다.

실패 시 호출 경계는 pending 실행을 재개 대상으로 사용하지 않고, 기존 도메인 State를 보존해 새 입력이 ENTRY부터 시작하도록 해야 한다. 이 동작은 checkpoint 통합 테스트의 필수 확인 항목이다. checkpoint 접근/저장 자체가 실패해 State를 신뢰할 수 없으면 해당 통화의 후속 처리를 정상으로 계속하지 않고 저장 오류를 반환한다. 상태 복구·수동 재개는 후속 운영 범위다.

## 순차 실행·timeout·checkpoint

같은 callId는 호출 경계에서 도착 순서대로 하나씩 처리한다. 입력 소비 전에 순서를 확보하고 정상/오류 반환 시 실행 소유권을 해제한다. 다른 통화까지 전역으로 막지 않는다. 데모에서는 단일 프로세스·유한한 입력을 전제로 메모리에서 순차 처리하며 MQ나 State의 pending_events를 추가하지 않는다. 실제 STT 수신 큐의 개수/대기 상한은 연결 스펙에서 정한다.

Tool 대기는 초기 데모 기본 5초, 설정으로 변경 가능하게 선택했다. 이는 조회 서비스의 보장이나 검증된 최적값이 아니라 다음 발화의 무제한 대기를 피하는 데모 기본값이다. 실제 도구에 맞춘 값은 Tool 스펙에서 조정한다. timeout이면 TIMEOUT 결과 하나를 저장하고 Jev 재판단한다. 가능한 취소를 시도하되 실제 외부 작업 중단을 보장하지 않는다. 이후 늦게 완료한 결과는 버리고 State를 추가로 수정하거나 background Jev를 실행하지 않는다. Tool 작업 자체가 State를 쓰지 않고 실행 Node가 반환 결과를 반영하도록 해야 한다.

InMemorySaver는 통화마다 같은 thread를 이어 사용한다. sync로 각 super-step 경계의 checkpoint 저장을 끝낸 뒤 다음 step을 진행한다. 순차 Graph에서는 Node 완료 경계와 연결되지만 Node 내부의 함수 호출마다 저장하는 것은 아니다. checkpoint에는 State와 실행 위치가 있으므로 최신 snapshot이 존재한다고 정상 완료를 의미하지 않는다.

통화 종료 후에도 State·checkpoint는 서버 프로세스 생존 동안 유지한다. 종료 이벤트 기반 삭제·자동 cleanup·서버 재시작 복구·여러 프로세스의 State 공유는 현재 데모에 추가하지 않는다. Checkpointer가 요청을 자동 직렬화한다고 가정하지 않는다.

## 결정 이력의 연결

다음 항목은 기존 Q1~Q14를 찾기 위한 진입점이다. 현재 실행 규칙의 기준은 위 본문이며 최초 선택·비교·검증의 시간순 근거는 [work](../../openspec/changes/first-demo/work.md)에 보존한다. 사용자가 핵심 정책을 선택했고, 남은 공통 실행 세부는 에이전트의 선택을 허용한 후속 요청에 따라 본문에 보완했다.

### Q1. 새 STT 입력을 어떻게 전달하고 Transcript에 merge할까?

utterance 입력 channel, 기존 대화 + [새 발화] 전체 목록 기본 교체, 소비 후 None. 입력 재사용 없이 갱신된 전체 대화를 Jev·Agent가 읽는다.

### Q2. verification_results는 전체 누적일까, 최근 검증 batch일까?

통화 전체 누적, 공통 5개 필드, OK/ERROR/TIMEOUT, 기존 결과 + [새 결과] 전체 목록 기본 교체. 도구별 결과·재조회/상충 해석은 Tool 스펙의 역할이다.

### Q3. 어떤 phase transition을 허용할까?

WARN 하향 금지, 나머지는 Jev 판단에 따른 유연한 전이. VERIFY 의미·risk 조건은 유지하며 기준 값은 Jev 스펙에서 정한다.

### Q4. 한 utterance에서 검증과 재판단을 몇 번 할까?

Tool 최대 1회·결과 저장 후 Jev 재판단 1회. 검증 시도 boolean과 Graph routing으로 재진입을 막고 VERIFY 종료 안내를 반환한다.

### Q5. 같은 callId의 STT 실행이 겹치면 어떻게 할까?

통화별 도착 순서대로 실행. Tool 기본 timeout 5초·설정 가능, 늦은 결과는 반영하지 않는다. 수신 큐 운영 한도는 연결 스펙에서 정한다.

### Q6. 무엇을 새 utterance로 보고 중복 append를 막을까?

final utterance의 중복 없는 데모 전제. 실제 재전송·발화 ID 계약은 연결 스펙의 역할이다.

### Q7. Tool 실행은 부모 Graph Node일까, Verify Agent 내부일까?

독립 verify_agent와 tool_execution Node, State의 tool_request로 전달·checkpoint 저장·소비 후 None. 요청 없음은 안내 후 종료, 여러/잘못된 요청은 실행 오류다.

### Q8. Jev 결과를 코드에서 검증하고 불허 전이를 막을까?

detect_with_jev에서 schema·유한 risk·허용 전이·Jev 스펙의 수치 조건을 검증한 뒤 적용. 실제 Jev 계약은 후속 스펙에서 정한다.

### Q9. signals를 ScamState에 포함할까?

MVP State에서 제외. 실제 Jev 선택 출력과 State 저장 여부를 구분한다.

### Q10. 사용자 안내 response를 State에 보관할까?

State·checkpoint에 최신 turn 안내 저장, 새 turn에 None. 정상·VERIFY 종료의 작성 책임은 종료 표를 따른다.

### Q11. Jev·Agent·Tool이 실패하면 이 turn과 다음 입력은 어떻게 처리할까?

Jev·Agent 실패는 자동 재시도 없는 실행 오류. Tool 실패는 결과 저장 후 재판단. 데모에서 중간 재개 없이 새 발화로 새 turn을 시작하며 마지막 저장 State를 유지한다.

### Q12. 첫 통화의 phase·risk·목록 초기값은 무엇일까?

OBSERVE, risk=None, 빈 대화·검증 결과, response/tool_request=None, verification_attempted=false. 기존 통화의 누적 도메인 상태는 초기화하지 않는다.

### Q13. InMemorySaver를 어떤 durability로 사용할까?

sync checkpoint 저장. 실제 Graph 설정·실패 뒤 새 turn 시작은 구현 통합 테스트에서 검증한다.

### Q14. 종료된 통화의 State는 언제 삭제할까?

통화 종료 후에도 프로세스 생존 동안 유지, 통화마다 고유 callId. 운영 cleanup은 후속 범위다.

## Jev 스펙

역할은 전체 통화를 읽고 현재 risk·phase를 결정하는 것이다. 최초 판단과 Tool 결과 반영 후 재판단은 같은 내부 계약을 사용한다.

| 구분 | 내부 계약 |
|---|---|
| 입력 | transcript: 전체 list[str], previous_phase: 호출 직전 phase, verification_results: 누적 목록(없으면 []) |
| 출력 | risk: 유한한 숫자, phase: OBSERVE/SUSPECT/VERIFY/WARN |
| 선택 출력 | signals는 외부 모델이 제공할 수 있으나 MVP State·routing에서 사용하지 않음 |
| 적용 | detect_with_jev가 형식·전이·확정된 risk 조건을 검사한 뒤 risk와 phase를 함께 반영 |
| 실패 | 호출/출력 검증 오류를 반환, 자동 재시도·phase 보정 없음 |

판단 지침은 개별 번호의 등장보다 대화 맥락·상대의 요구·확인 필요성을 함께 보고, VERIFIED/NOT_FOUND 같은 Tool 내용과 실행 오류를 구분하는 것이다. VERIFY는 충분한 의심과 검증 가능한 대상이 있을 때 선택한다. 정상 조회만으로 OBSERVE를 강제하거나 Mock 미등록·timeout만으로 WARN을 강제하지 않는다. WARN 하향은 허용하지 않는다.

실제 Jev의 endpoint·인증·요청/응답 포맷, risk 척도/허용 범위·threshold는 **외부 계약 미정**이다. 위 입력 이름은 내부 계약이며 외부 API 필드라고 주장하지 않는다. 연동 시 확인된 계약을 내부 계약으로 변환한다.

Fake Jev는 정해진 데모 입력과 조회 결과에 대해 OBSERVE → SUSPECT → VERIFY → WARN을 반환하는 fixture다. fixture risk는 외부 모델 threshold나 탐지 성능의 근거가 아니다. 호출 오류·잘못된 출력·WARN 하향·재판단 VERIFY 등의 별도 fixture로 실행 정책도 확인한다.

## Agent 스펙

### Suspect Agent

입력은 전체 transcript와 현재 State다. 출력은 비어 있지 않은 한국어 안내 문자열이며 response에 저장한다. 외부 Tool·risk/phase 수정·별도 memory는 없다.

행동 지침은 이번 대화에 필요한 확인 행동을 1~2문장으로 안내하는 것이다. 상대가 주장한 기관명·사건번호·연락처 등을 확인하도록 안내하며 확인하지 않은 사실이나 조회 결과를 만들어내지 않는다. 역할은 위험 판정 대신 확인 행동 생성이다. 예시: “상대방에게 정확한 기관명과 사건번호를 물어보세요. 안내받은 정보는 기관의 공식 연락처로 확인하세요.”

### Verify Agent

입력은 전체 transcript·현재 State·누적 검증 결과·등록된 Tool 설명과 인자 schema다. 출력은 유효한 ToolRequest 하나 또는 None이다. 대화에 없는 인자를 만들어내지 않고 검증 목적에 맞는 도구를 선택한다. 충분한 인자가 없으면 None을 반환한다.

LangChain의 모델 Tool Calling 출력에서 선택한 이름·인자를 공통 {tool,input}으로 변환한다. 이 선택 단계에서 Tool을 자동 실행하는 Agent loop는 사용하지 않는다. 원시 메시지는 이번 호출 안에서 처리하며 부모 Graph의 tool_execution이 실제 실행을 맡는다. 여러 요청·알 수 없는 도구·잘못된 인자는 출력 검증 실패다. 모델이 None을 선택한 경우는 정상 종료 안내 경로다.

기존 동일 대상 결과는 참고하되 MVP에서 자동 cache·재조회 차단은 추가하지 않는다. 새 turn에 실제로 같은 Tool 요청을 선택하면 다시 실행하고 결과를 별도 누적한다. 상충 결과는 이전 것을 지우지 않고 Jev가 전체 목록과 Mock 여부를 보고 재판단한다.

두 Agent의 Provider·모델·인증·SDK의 정확한 호출 코드는 **연동 설정 미정**이다. 행동 지침과 내부 입출력은 위 계약으로 유지한다. API 없는 테스트는 Agent 대역, 실제 Tool Calling 검증은 선택한 모델을 사용하며 결과를 구분한다.

## Verification Tool 스펙

첫 데모에서 실제 제공할 Tool은 **Mock case_lookup 하나**로 시작한다. phone_lookup/url_lookup/account_lookup은 추가 후보이며 이번 데모에 모두 구현해야 하는 목록은 아니다.

| case_lookup 항목 | 내부 스펙 초안 |
|---|---|
| 입력 | {case_number: 비어 있지 않은 문자열} |
| 정상 result | {lookup_status: FOUND 또는 NOT_FOUND, reason: 결과 설명 문자열} |
| Mock fixture | 2026-12345는 NOT_FOUND, 2026-00001은 FOUND인 테스트 데이터 |
| 조회 범위 | Mock 테이블의 정확한 사건번호 일치. 실제 기관의 사건 존재 여부를 확인하는 기능은 아님 |
| 저장 | 원래 조회 인자·정상 내용, status=OK, is_mock=true를 공통 VerificationResult로 감쌈 |
| 실행 실패 | 공통 result={code,message}, status=ERROR 또는 TIMEOUT으로 감쌈 |

case_number를 원문에서 선택하되 기관별 사건번호 정규식이나 실재성을 임의로 가정하지 않는다. 입력 타입/공백 여부는 검증하고 인자 변조·추측으로 조회하지 않는다. Agent가 과거 결과를 참조하더라도 이번 요청의 원래 인자를 저장한다.

공통 실패 code의 초안은 TOOL_EXECUTION_FAILED(호출 오류), TOOL_RESULT_INVALID(정상 결과 schema 위반), TOOL_TIMEOUT(시간 초과)다. message는 실패 설명이며 내부 예외 객체는 저장하지 않는다. timeout은 설정 가능한 기본 5초이고 늦은 결과는 버린다. 실제 공공기관 조회 데이터·API·기관별 인자 형식은 **외부 연결 미정**이다.

이 Tool별 object result는 기존 공통 result 필드를 구체화한 내부 초안이다. 이전 NOT_FOUND 문자열 예시는 결과 의미를 설명한 것이며 실제 외부 조회의 확정 포맷이 아니다.

## 입력·응답 스펙

내부 turn 진입점은 {callId: 비어 있지 않은 문자열, utterance: 비어 있지 않은 final 발화 문자열}을 받는다. 공백만 있는 입력은 거부하며 유효한 발화 원문은 transcript에 보존한다. callId는 호출자가 통화마다 고유하게 생성하고 같은 통화에서 재사용한다. 내부 입력은 식별자와 발화만 받으며 호출자가 phase·risk·누적 검증 결과를 덮어쓰게 하지 않는다.

정상 결과는 위 종료 계약의 {callId,risk,phase,response,verification_results}다. 검증하지 않은 외부 정보가 확인된 것처럼 보이지 않도록 Mock 결과에는 is_mock=true를 유지한다. 실행 오류는 {callId,error:{stage,code,message}}이고 식별자부터 잘못된 입력의 callId는 None일 수 있다. 오류 code의 내부 초안은 INVALID_INPUT, CALL_FAILED, INVALID_OUTPUT, INVALID_TRANSITION, CHECKPOINT_FAILED, EXECUTION_CONTRACT_VIOLATION이다. stage로 실패 위치를 구분하며 외부 API 상태 코드와 동일하다고 가정하지 않는다.

실제 STT Provider·partial/final 변환·발화 재전송, HTTP/WebSocket route/envelope·중간 risk 이벤트, 수신 큐 운영 한도는 **외부 연결 미정**이다. 내부 turn 계약은 이러한 전달 방식에 공통으로 적용한다.

## 구현·검증 기준

| 시나리오 | 확인할 결과 |
|---|---|
| 첫 데모 | 세 발화로 OBSERVE → SUSPECT → VERIFY, case_lookup(2026-12345) Mock 결과 저장 뒤 Jev 재판단 → WARN |
| 대화·통화 유지 | 발화 한 번 누적·입력 소비, 같은 callId의 상태 유지, 다른 callId의 분리 |
| 선택·실행 분리 | verify_agent에서 실제 Tool 실행 없음, 유효 요청 하나만 tool_execution에서 실행 |
| 결과 누적 | 정상/실패 모두 원래 인자·공통 필드 보존, 전체 목록 교체, 재판단에서 재추가 없음 |
| 정상 종료 | OBSERVE의 response=None, SUSPECT 안내·WARN 고정 경고, 새 turn에 이전 안내 초기화 |
| VERIFY 종료 | 요청 없음/재판단 VERIFY에서 안내 후 END, 두 번째 Tool·추가 재판단 없음 |
| 유효성·오류 | 잘못된 Jev/Agent 출력과 금지 전이를 적용하지 않음, 자동 재시도 없음 |
| timeout | TIMEOUT 한 건 반영 후 재판단, 늦은 완료의 State 수정·background 판단 없음 |
| 실패 뒤 새 입력 | 마지막 저장 State 유지, 새 ENTRY 시작, 오래된 요청/pending 실행 재개 없음 |
| checkpoint | 동일 saver·thread 사용, sync 설정, 통화 종료 후 유지, 저장 실패를 정상 성공으로 반환하지 않음 |

검증은 API 없는 Graph/Fake Jev/Mock Tool/Agent 대역 검사와 실제 Agent 모델의 Tool Calling 검사를 구분한다. Fake/Mock 성공은 실제 탐지 정확도나 공공기관 조회 성공의 근거가 아니다. 아직 서비스 테스트·빌드·Provider 호출 결과는 없다.

## 남은 확정 항목

이 문서 안에서 남은 Jev API/risk 계약, Agent 모델·호출 설정, 실제 Tool 조회와 STT/프론트 연결을 이어 작성한다. 일상적인 세부 선택은 에이전트가 진행하고 기존 핵심 방향을 크게 바꾸거나 외부 정보가 꼭 필요한 경우만 사용자에게 확인한다. 구현 전에 해당 실행 모드에 필요한 계약을 확정해야 한다.

MVP 전체 스펙은 하나로 관리하되 실제 운영 범위는 별도 후속 작업이다. Tool 대기 중 다음 발화를 먼저 판단하고 늦은 결과를 반영하는 방식은 기존 합의대로 Future Optimization으로 남긴다.

## 관련 문서와 확인 근거

- [프로젝트 컨텍스트](../project-context.md) · [상세 설계 인덱스](index.md) · [아키텍처 인덱스](../architecture/index.md)
- [MVP 흐름 설계](mvp-flow.md) — 데모 시나리오와 Fake/Mock 검증 범위
- [기존 first-demo change](../../openspec/changes/first-demo/proposal.md) · [작업·검증 근거](../../openspec/changes/first-demo/work.md)
- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) — schemas, reducers, runtime context, recursion limit
- [LangGraph Checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers) — super-step, snapshot, durability
- [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) — thread memory와 InMemorySaver의 RAM 보관

공식 문서 확인일: 2026-10-10. 저장소 lock의 LangGraph는 1.2.14, langgraph-checkpoint는 4.2.0이다. 위 근거는 Framework 동작 설명이며 프로젝트의 미정 정책을 승인하는 근거가 아니다.
