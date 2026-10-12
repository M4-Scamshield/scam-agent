# 첫 데모 요구사항

공통 실행 계약의 기준은 [State·Graph 설계](../../../docs/design/state-and-graph.md)다. 공통 설계는 정리 완료했고 구성요소별 내부 계약과 검증 기준은 후속 요청으로 같은 문서에 통합했다. 실제 외부 연결 계약과 서비스 구현·실행 검증은 후속 작업이다. 이번 보완은 사용자가 에이전트의 세부 선택을 허용한 요청에 따른다.

## 실행·상태

- 새 final utterance 하나가 turn 하나를 시작한다. 같은 callId를 순차 처리하고 InMemorySaver의 같은 thread에서 전체 한국어 대화와 검증 결과를 유지한다.
- update_context는 새 발화를 한 번 추가하고 utterance를 소비한다. 대화·검증 결과는 전체 새 목록을 기본 교체로 저장하며 append reducer를 함께 사용하지 않는다.
- 첫 통화는 OBSERVE·risk=None·빈 대화/검증 결과로 시작한다. 새 turn에 response·tool_request·verification_attempted를 초기화하고 기존 누적 도메인 상태는 유지한다.
- Jev가 risk·phase를 결정한다. detect_with_jev가 schema·유한 risk·전이와 후속 Jev 스펙의 수치 조건을 검증한 뒤 적용한다. WARN 하향은 금지하며 VERIFY의 의심·검증 정보·필요성 조건을 유지한다.
- OBSERVE는 안내 없이 종료, SUSPECT는 외부 Tool 없는 확인 행동 안내, WARN은 고정 경고다.

## 검증 경로

- verify_agent가 검증한 Tool 요청 하나를 State의 tool_request로 전달하고 독립 tool_execution Node가 실행·결과 저장·요청 소비를 맡는다.
- 정상 조회와 ERROR/TIMEOUT 결과 모두 tool·input·status·result·is_mock 공통 형식으로 통화 전체에 누적한다. OK와 안전 판정은 구분하며 Mock 미등록을 실제 기관 미등록으로 단정하지 않는다.
- turn당 Tool 최대 1회, 저장 후 Jev 재판단 1회다. verification_attempted와 routing으로 재검증을 막는다.
- 유효한 요청 없음은 안내 후 종료, 여러/잘못된 요청은 Agent 출력 오류로 Tool 실행 없이 종료한다. 재판단이 VERIFY여도 추가 실행 없이 안내 후 종료한다.

## 오류·유지

Jev·Agent 실패는 자동 재시도 없는 실행 오류다. Tool 실패는 검증하지 못한 결과로 저장하고 Jev 재판단한다. 정상 결과와 내부 오류 결과를 구분하며 정확한 형식·각 종료 안내는 기준 설계를 따른다.

실패 뒤에는 중간 재개나 같은 요청 재전송 없이 새 final utterance로 새 turn을 시작한다. 마지막 저장 도메인 State는 유지하고 오래된 pending 실행을 이어 실행하지 않는다. checkpoint 접근 실패는 정상 처리를 이어가지 않는다.

Tool 대기의 데모 기본 timeout은 설정 가능한 5초다. 초과 시 가능한 취소를 시도하고 TIMEOUT 결과 하나를 반영한다. 늦은 완료는 State를 수정하거나 background 판단을 시작하지 않는다. 실제 Tool에 맞춘 값은 상세 스펙에서 조정한다.

sync checkpoint 저장을 사용하고 통화 종료 후에도 프로세스 생존 동안 보관한다. 재시작 복구·cleanup·실시간 늦은 결과 반영은 이번 범위 밖이다. final 발화의 중복 없는 데모 입력 전제와 실제 STT 전달 보장은 구분한다.

## 검증과 후속 계약

실행 가능한 검사는 누적·통화 분리·검증 후 재판단뿐 아니라 요청 소비·한도/실패 종료·잘못된 출력·timeout과 늦은 결과 폐기·실패 뒤 새 ENTRY 실행을 확인해야 한다. 아직 실행 검증은 없다.

Jev·Agent·Tool의 내부 스펙과 데모 인수조건은 같은 전체 스펙의 해당 절을 따른다. 실제 Jev API/risk 기준·Agent Provider·외부 조회·STT/프론트 연결은 이어 확정한다. 범위는 [MVP 흐름](../../../docs/design/mvp-flow.md), 완료 근거는 [work](work.md)에 있다.
