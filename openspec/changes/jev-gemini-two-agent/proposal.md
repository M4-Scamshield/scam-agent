# Jev 탐지와 Gemini 분석으로 2AS 전환

## 문제와 목표

2026-10-23 사용자는 기존 Suspect/Verify·Mock 조회 흐름을 바꾸고 Jev와 Gemini를 두 판단 역할로 사용하는 구조를 요청했다. STT 결과에 대해 Jev의 Yes/No·확률을 저장하고 Yes일 때만 LLM이 분석·대응한다. 2026-10-27 중단한 작업을 재개했다.

## 범위와 제외 범위

실제 TypeSafe Jev HTTP 연결, 두 역할 인터페이스, State·LangGraph·CLI·테스트·문서 전환, 쓰지 않는 역할/도구 코드 제거, 컴파일된 그래프 출력을 포함한다. 실제 STT 제품·Kafka·화자 구분·도구 조회·웹 서버·UI·운영 복구는 이번 범위 밖이다.

## 완료 조건

- Jev 판정과 P(Yes)를 State에 저장한다.
- Yes이면 대화·Jev 결과를 Gemini에 전달해 근거 요약과 대응 안내를 저장한다.
- No이면 LLM 호출 없이 종료하고 이전 안내가 남지 않는다.
- API 없는 검증과 실제 API 연결 결과를 구분해 기록한다.
- 새 구조도와 문서가 실제 코드에 맞는다.

## 관련 문서

[현재 계약](../../../docs/design/state-and-graph.md) · [아키텍처](../../../docs/architecture/overview.md) · [요구](spec.md) · [적용 설계](design.md) · [작업](tasks.md) · [실행 근거](work.md)
