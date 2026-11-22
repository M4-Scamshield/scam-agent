# 요구사항

1. 새 STT·일반 채팅은 기존 통화 분석, 새 채팅 URL은 URL agent로 전달한다. Jev가 call/url 두 질문을 판단하며 두 경로를 함께 선택할 수 있다. 필요한 경로를 누락한 모델 응답은 오류다.
2. 채팅은 서버 발급 `{id, seq, text}`로 받는다. 완료한 ID를 다시 보내도 모델과 도구를 재호출하지 않는다. 같은 ID를 다른 내용·seq로 재사용하면 입력 오류다.
3. ID와 URL별 처리를 구분한다. 같은 주소의 여러 메시지는 통화 내 결과를 재사용한다. 여러 URL 중 실패한 것만 다시 조회하며, 통화 분석까지 반복하지 않는다.
4. Mock `flagged`는 `risky`, `not_found`는 `unknown`, 실패는 `error`다. 도구를 호출하지 않거나 다른 URL을 호출한 모델은 조회 성공으로 취급하지 않는다. 실제 사이트 안전을 보장하지 않는다.
5. 상태는 호출자가 보관한다. 새 인스턴스도 이전 `state`를 받으면 중복 처리를 건너뛴다. 입력 state를 직접 변경하지 않는다.
6. 기존 `scamshield.graph.build_pipeline`과 `CallPipeline.analyze`는 유지한다. 에이전트 이동 후 기존 테스트·CLI와 새 Supervisor 회귀 검사를 실행한다.

[공통 계약](../../../docs/design/supervisor-and-chat.md), [통화 계약](../../../docs/design/state-and-graph.md), [proposal](proposal.md), [design](design.md)
