# 데모데이용 첫 실행 요구사항

> 역사 기록: 이 문서는 2026-10-12 데모 범위의 요구·적용·검증을 보존한다. 현재 구조는 [2AS change](../jev-gemini-two-agent/proposal.md)와 [현행 계약](../../../docs/design/state-and-graph.md)을 따른다. 당시 계약은 [이전 스펙](https://github.com/M4-Scamshield/scam-agent/blob/9ae72bb/docs/design/state-and-graph.md)에서 확인한다.

기준은 [전체 스펙](../../../docs/design/state-and-graph.md)과 [데모 흐름](../../../docs/design/mvp-flow.md)이다. 운영 수준의 확장/복구보다 정해진 세 발화 시나리오의 실제 동작을 완료 조건으로 삼는다.

## 필요한 동작

- CLI가 같은 callId의 세 final 발화를 한 번씩 순차 전달하고 완료를 기다린다.
- 세 발화 제한과 준비된 문장은 데모 CLI의 설정이다. Graph의 정상 통화 상태는 후속 turn에서도 유지하며 현재 화자 정보·STT·상대방 AI는 없다.
- State·InMemorySaver로 전체 대화·검증 결과를 유지하고 새 callId와 분리한다. 초기값·목록 교체·입력/요청 소비는 전체 스펙을 따른다.
- 데모 risk는 0~1·VERIFY >= 0.6이고 OBSERVE/SUSPECT/VERIFY/WARN fixture는 0.1/0.5/0.7/0.9다. 실제 Jev 수치 계약으로 확대하지 않는다.
- Fake Jev는 대화와 해당 사건번호의 결과로 판단하며 동일 세 발화에서 결과 없으면 VERIFY, 정상 Mock NOT_FOUND면 WARN이다. 호출 횟수만으로 WARN을 반환하지 않는다.
- Gemini 같은 모델을 두 Agent가 공유하며 역할·Tool 권한만 분리한다. Suspect 안내와 Verify 실제 Tool Calling을 확인한다.
- 선택한 요청 하나를 독립 tool_execution이 즉시 반환 Mock case_lookup으로 실행/저장한다. 한 turn에서 Tool 최대 1회·결과 후 Jev 재판단 1회를 유지한다.
- 조회 인자는 대화에 제시된 데모 사건번호 전체와 정확히 일치해야 한다. `2026`/`12345`처럼 일부만 선택한 요청은 INVALID_OUTPUT으로 거부하고 Tool 실행·결과 저장을 하지 않는다.
- CLI에서 Node 순서·phase/risk·Tool 요청/결과·response를 보여준다.

## 오류와 제외 범위

기본 입력/출력 검증·금지 전이 거부·자동 재시도 없는 오류 반환을 유지한다. Tool 오류는 실패 결과를 저장해 재판단하되 실행 오류로 끝나면 해당 통화 시나리오를 중단한다. 새 callId로 처음부터 재시작하며 같은 실패 통화의 계속 처리·중간 재개는 요구하지 않는다.

첫 데모에는 동시 요청 제어·수신 큐·timeout wrapper/취소/늦은 완료 검증과 포괄적인 오류 fixture가 필요하지 않다. 실제 Jev·기관 조회·STT/프론트/운영 인프라는 후속 범위다. Fake/Mock 완료와 실제 탐지/기관 확인은 구분한다.

현재 Tool 예외/잘못된 결과는 ERROR로 정규화하고, TIMEOUT 결과 생성은 후속 계약이다. 후속 STT에서는 상대방과 사용자 양쪽의 발화를 화자별로 구분해 같은 통화에 누적한다. 실제 입력/State schema는 아직 구현하지 않았다.

## 검증

API 없는 핵심 Graph 검사와 실제 Agent 모델 호출을 구분한다. 첫 완료 조건은 시나리오·상태 누적/분리·실제 Tool 선택/인자·결과 반영·1회 한도다. 문서 검사만으로 실행 완료를 표시하지 않는다. 진행과 결과는 [tasks](tasks.md)·[work](work.md)에 기록한다.
