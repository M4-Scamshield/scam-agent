# 상세 설계 문서

구현 전 구조·계약·예외 동작을 구체화하는 위치다. 설계가 존재한다는 사실과 구현이 완료됐다는 사실을 구분한다. 전체 진입점은 [문서 지도](../index.md)다.

## 문서 목록

| 문서 | 포함한 내용 |
|---|---|
| [ScamShield MVP 전체 스펙](state-and-graph.md) | 공통 State·Graph, Jev·역할별 LLM·Tool 내부 계약, 입력/응답·실패 처리·데모 검증 기준. API 없는 검사와 실제 Gemini 데모 완료, 실제 Jev/STT는 후속 범위 |
| [첫 통화 데모 흐름](mvp-flow.md) | 세 발화 시나리오와 Fake/Mock 검증 범위. CLI·상태/조회/한도 검사와 실제 Gemini 안내/Tool Calling 완료 |

데모의 State·Jev·역할별 LLM·Mock Tool 내부 계약은 위 스펙에 통합했다. 다음 항목은 후속 연결에서 보완할 주제이며 현재 데모 미구현 결함을 뜻하지 않는다. 구성요소별 문서를 반드시 분리하지 않는다.

| 주제 | 포함할 내용 |
|---|---|
| 외부 연결 | 실제 Jev·기관 조회·STT 연결의 계약과 검증. 현재 데모 범위와 구분 |
| Jev 계약 | 실제 외부 모델의 입력/출력·risk 기준·인증과 내부 계약 변환 |
| Agent | 역할별 직접 LLM 호출을 Agent 실행 객체/런타임으로 전환하는 TODO |
| Verification Tool | 실제 기관 조회의 인자·결과·시간 초과·인증 계약 |
| 입력과 응답 | 양쪽 화자 STT·화자 구분·발화/State schema·risk 전달·프론트엔드 응답 |

이미 합의한 범위는 [프로젝트 컨텍스트](../project-context.md)에서 확인한다. 선택의 근거는 [결정](../decisions/index.md), 조사·실험은 [분석](../analysis/index.md), 변경별 요구·설계와 구현·검증 진행은 [OpenSpec](../../openspec/index.md)에 연결한다.
