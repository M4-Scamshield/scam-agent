# 첫 데모 적용 방법

기준은 [공통 State·Graph 실행 설계](../../../docs/design/state-and-graph.md)다. 이번 단계는 공통 설계를 포함한 전체 스펙 초안을 같은 문서에 작성하며 서비스 코드는 작성하지 않는다. 시나리오는 [MVP 흐름](../../../docs/design/mvp-flow.md)을 따른다.

부모 Graph에 update_context·detect_with_jev·suspect_agent·verify_agent·tool_execution·warn을 둔다. Agent 선택과 Tool 실행을 분리하고, 같은 detect_with_jev 함수로 최초/검증 후 판단을 처리한다. State의 verification_attempted로 반복 검증을 막는다. 새 Supervisor·추출 Agent·별도 재판단 Node·복잡한 counter를 추가하지 않는다.

새 turn은 입력 소비와 실행 값 초기화에서 시작한다. Jev 출력 적용 전 검증, phase별 분기, Tool 요청 선택·검증·저장, 실행·결과 저장·요청 소비를 기존 Node에서 처리한다. 대화·검증 결과는 전체 새 목록을 기본 교체로 저장한다. phase·risk·누적 결과의 소유권과 정상/VERIFY 종료 안내는 기준 설계의 표를 따른다.

Tool 요청은 {tool,input}으로 부모 State에 보관한다. Agent 라이브러리의 원시 메시지는 호출 내부에서 공통 요청으로 변환한다. Provider/Tool Calling 세부 구현은 Agent 스펙에서 정하며 선택 Node 내부에서 Tool을 실행하지 않는다.

호출 경계는 같은 callId를 도착 순서대로 직렬화한다. 내부 정상 결과와 실행 오류를 구분하고 실패한 turn을 자동 재개하지 않는다. 다음 새 입력은 마지막 저장 도메인 State를 유지하면서 ENTRY부터 시작한다. sync checkpoint·실패 뒤 실행 시작·늦은 Tool 결과 폐기는 실제 LangGraph 통합 테스트에서 확인한다.

Tool 대기는 설정 가능한 데모 기본 5초다. 늦은 작업이 직접 State를 쓰지 않도록 실행 결과의 반영을 tool_execution 한 곳에서 관리한다. 실제 취소 지원과 개별 Tool의 시간 값은 Tool 스펙에서 맞춘다. 여러 프로세스 공유·MQ·Redis·Conversation DB를 추가하지 않는다.

공통 경계와 Jev·Agent·Tool 내부 계약을 같은 문서에서 맞췄다. 다음은 외부 연결에 필요한 계약을 확정하고 State·Graph·Fake Jev·Mock 조회를 구현/검증하고 두 Agent의 Tool Calling을 연결하는 것이다. 외부 API 없는 검사와 실제 Provider 호출을 구분한다. 실제 Jev API와 risk 척도를 임의로 가정하지 않는다.

진행은 [tasks](tasks.md), 실제 실행 근거는 [work](work.md)를 따른다.
