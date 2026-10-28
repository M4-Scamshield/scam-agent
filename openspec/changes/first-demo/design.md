# 데모 구현 방향

> 역사 기록: 이 문서는 2026-10-12 데모 범위의 요구·적용·검증을 보존한다. 현재 구조는 [2AS change](../jev-gemini-two-agent/proposal.md)와 [현행 계약](../../../docs/design/state-and-graph.md)을 따른다. 당시 계약은 [이전 스펙](https://github.com/M4-Scamshield/scam-agent/blob/9ae72bb/docs/design/state-and-graph.md)에서 확인한다.

[전체 스펙](../../../docs/design/state-and-graph.md)의 공통 State/Node 구조를 그대로 구현했다. 이번 리뷰 반영은 데모 실행을 막는 모호함을 줄이고 복구/동시 입력/timeout 검증을 첫 범위에서 제외하는 설계 변경이다. 코드별 책임은 [현재 데모 구성](../../../docs/architecture/overview.md)에 있다.

Fake Jev는 호출 횟수 대신 누적 transcript·이전 phase·해당 사건번호의 최신 결과를 읽는 고정 규칙으로 구현한다. 데모 risk 0~1·VERIFY 기준 0.6과 phase별 0.1/0.5/0.7/0.9를 사용한다. Mock NOT_FOUND와 정해진 기관 사칭 대화를 함께 반영하는 재판단으로 WARN을 보여준다.

Gemini Developer API의 gemini-3.8-flash를 두 역할이 공유하고 prompt/Tool 권한만 분리한다. Verify는 1회 모델 호출의 tool_calls를 0개=None, 1개=검증한 요청, 여러 개=오류로 변환한다. 선택 Node에서 Tool 자동 실행 loop를 사용하지 않는다. `langchain-google-genai` 연결·SDK 전송 대역 검사와 실제 모델 안내/Tool Calling·최종 WARN을 확인했다. 계정의 무료 한도를 검증한 것은 아니다. `GEMINI_MODEL`로 모델을 변경하고 `GEMINI_API_KEY`로 키를 받으며 자동 재시도는 끈다. Gemini에 전달하는 선언에서는 무시되는 additionalProperties를 제외하고 로컬 Pydantic 계약에서 추가 인자를 거부한다.

CLI가 turn 실행 완료를 기다리므로 별도 직렬화 lock/큐를 첫 구현에 추가하지 않는다. 즉시 반환 Mock case_lookup을 쓰고 오류 시 해당 시나리오를 중단해 새 callId로 재시작한다. 실패 checkpoint의 pending 작업 폐기/도메인 State 복원과 timeout 취소 검증은 후속 범위다. sync·통화별 상태·turn당 Tool 1회 구조는 유지한다.

세 문장은 DEMO_UTTERANCES에서 제공하고 CLI의 반복 횟수만 세 번으로 정한다. Graph에는 세 turn 한도가 없다. Fake Jev의 검증 진입과 Mock fixture의 등록 여부는 서로 다른 조건이며 세부 규칙은 전체 스펙을 따른다. 현재 화자 정보 없는 문자열 transcript를 사용하고 양쪽 화자 STT 입력은 후속 계약이다. Tool은 현재 ERROR 결과만 정규화하고 TIMEOUT 생성/취소는 구현하지 않았다.

검증은 [데모 흐름](../../../docs/design/mvp-flow.md)의 핵심 완료 조건에 집중하고 포괄적인 예외 fixture를 추가하지 않는다. [tasks](tasks.md)와 [work](work.md)에서 문서 반영·실제 실행을 구분한다.

리뷰 P2 수정: 공통 validate_request가 단순 부분 문자열 포함 검사 대신 대화의 하이픈 연결 숫자열 전체와 정확히 일치하는지 검사한다. 잘린 번호는 선택 Node에서 INVALID_OUTPUT으로 종료하고 실행·결과 저장으로 넘어가지 않는다. 실제 기관별 사건번호 파서로 확장하지 않는다.

사용자 요청에 따라 지금은 역할별 LLM 호출로 데모를 구현하고, 이후 Agent 실행 객체/런타임으로 전환한다. [기준 설계의 Agent TODO](../../../docs/design/state-and-graph.md#todo--데모-이후-agent-실행-구조로-전환)를 따른다. 현재 1회 호출/Tool 실행 분리 범위는 유지하고 후속 Agent 전환을 구현 완료로 표시하지 않는다.
