# 첫 통화 데모 구현

> 역사 기록: 이 문서는 2026-10-12 데모 범위의 요구·적용·검증을 보존한다. 현재 구조는 [2AS change](../jev-gemini-two-agent/proposal.md)와 [현행 계약](../../../docs/design/state-and-graph.md)을 따른다. 당시 계약은 [이전 스펙](https://github.com/M4-Scamshield/scam-agent/blob/9ae72bb/docs/design/state-and-graph.md)에서 확인한다.

상태: 완료 — 이번 데모의 구현·인수조건 검증. 후속 Agent 전환·실제 외부 연결은 제외.

2026-10-12 현재: [공통 State·Graph 설계](../../../docs/design/state-and-graph.md)를 기준으로 CLI·State·Graph·Fake Jev·Mock 조회·역할별 Gemini 연결을 구현했다. API 없는 검사와 실제 Gemini 세 발화 데모를 완료했다. 기존 change에서 진행을 이어 기록했고 실제 외부 Jev/기관 조회 계약은 후속 범위다. 실행 근거는 [work](work.md)에 있다.

하네스 구성 이후 사용자가 본격적인 구현 시작을 요청했다. 추가 AI 작업 환경 구성보다 기존 문서와 스킬을 사용해 첫 통화의 전체 흐름을 구현한다.

## 범위와 완료 조건

2026-10-12 리뷰 반영: 데모데이용 CLI 시나리오를 우선한다. Fake Jev risk/판단 규칙과 공유 Gemini 모델을 사용하고 실패 뒤 통화 재개·동시 입력·timeout 취소 검증은 후속 범위로 옮겼다. 실제 모델 안내와 Tool Calling을 포함한 이번 데모 완료 조건을 충족했다.

ScamState·LangGraph·InMemorySaver·Fake Jev·두 Agent·Mock 검증 Tool로 첫 시나리오를 실행한다. 같은 통화의 상태 누적과 통화 분리, 검증 후 재판단을 확인한다. 실제 Jev·공공 조회·Streaming STT·프론트 연결은 이후 단계다.

Agent는 Gemini로 먼저 실험하며 실제 Jev 계약은 첫 데모 이후 범위다. API 없는 검증과 실제 모델 호출 결과를 구분한다.

## 관련 문서

- [상위 컨텍스트](../../../docs/project-context.md)
- [MVP 흐름 설계](../../../docs/design/mvp-flow.md)
- [State·LangGraph 공통 실행 설계](../../../docs/design/state-and-graph.md)
- [요구](spec.md) · [적용 설계](design.md) · [작업](tasks.md) · [근거](work.md)
