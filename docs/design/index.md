# 상세 설계 문서

구현 전 구조·계약·예외 동작을 구체화하는 위치다. 설계가 존재한다는 사실과 구현이 완료됐다는 사실을 구분한다. 전체 진입점은 [문서 지도](../index.md)다.

## 문서 목록

| 문서 | 포함한 내용 |
|---|---|
| [ScamShield MVP 전체 스펙](state-and-graph.md) | 통합 초안. 공통 State·Graph, Jev·Agent·Tool 내부 계약, 입력/응답·실패 처리·데모 검증 기준을 한 문서에서 관리. 실제 외부 API·모델·STT 연결은 미정 |
| [첫 통화 데모 흐름](mvp-flow.md) | 데모 시나리오와 Fake/Mock 검증 범위. 공통 실행은 위 설계를 따르며 Provider와 실제 Jev 계약·서비스 구현은 후속 범위 |

다음 항목은 전체 스펙 안에서 보완할 주제다. 구성요소별 문서를 반드시 분리하지 않는다.

| 주제 | 포함할 내용 |
|---|---|
| 공통 설계의 구현 | State·Graph·checkpoint를 코드로 구성하고 종료/실패 뒤 새 turn·timeout과 늦은 결과 폐기를 통합 검증 |
| Jev 계약 | 전체 한국어 입력·이전 phase·검증 결과·출력 검증·실패 처리 |
| Agent | Suspect·Verify 역할·프롬프트·입출력·Tool 권한과 호출 방식 |
| Verification Tool | 도구 인자·결과 schema·Mock 데이터·조회 한계 |
| 입력과 응답 | STT 진입점·API 검증·risk 전달·프론트엔드 응답 |

이미 합의한 범위는 [프로젝트 컨텍스트](../project-context.md)에서 확인한다. 선택의 근거는 [결정](../decisions/index.md), 조사·실험은 [분석](../analysis/index.md), 변경별 요구·설계와 구현·검증 진행은 [OpenSpec](../../openspec/index.md)에 연결한다.
