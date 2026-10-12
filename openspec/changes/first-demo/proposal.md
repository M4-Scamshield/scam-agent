# 첫 통화 데모 구현

상태: 진행 중

2026-10-11 현재: [공통 State·Graph 설계](../../../docs/design/state-and-graph.md)를 정리 완료했다. 후속 요청에 따라 같은 문서를 MVP 전체 스펙 초안으로 확장해 공통 규칙·구성요소별 내부 계약·검증 기준을 통합했다. 실제 외부 연결 계약은 이어 확정한다. 현재 서비스 구현은 미착수이며 이번 설계 단계에서 새 구현 change를 만들지 않는다.

하네스 구성 이후 사용자가 본격적인 구현 시작을 요청했다. 추가 AI 작업 환경 구성보다 기존 문서와 스킬을 사용해 첫 통화의 전체 흐름을 구현한다.

## 범위와 완료 조건

ScamState·LangGraph·InMemorySaver·Fake Jev·두 Agent·Mock 검증 Tool로 첫 시나리오를 실행한다. 같은 통화의 상태 누적과 통화 분리, 검증 후 재판단을 확인한다. 실제 Jev·공공 조회·Streaming STT·프론트 연결은 이후 단계다.

Provider와 실제 Jev 계약은 후속 구성요소 스펙에서 정한다. API 없는 검증과 실제 모델 호출 결과를 구분한다.

## 관련 문서

- [상위 컨텍스트](../../../docs/project-context.md)
- [MVP 흐름 설계](../../../docs/design/mvp-flow.md)
- [State·LangGraph 공통 실행 설계](../../../docs/design/state-and-graph.md)
- [요구](spec.md) · [적용 설계](design.md) · [작업](tasks.md) · [근거](work.md)
