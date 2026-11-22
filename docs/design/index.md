# 상세 설계 문서

현재 계약과 후속 제안을 구분한다. 전체 진입점은 [문서 지도](../index.md)다.

| 문서 | 포함한 내용 |
|---|---|
| [State·Graph 계약](state-and-graph.md) | 현재 Jev 상태 감지·상태별 Haiku 판단·점수, `analyze` 입출력·실패 |
| [입력과 실행 흐름](mvp-flow.md) | 요청 하나의 흐름과 CLI·offline 실행 |
| [Jev Supervisor·채팅·URL 계약](supervisor-and-chat.md) | 상위 라우팅, 메시지 ID·경로별 처리 상태, Mock URL Tool Calling, 서버 저장 책임 |

2026-11-22 [jev-state-agents](../../openspec/changes/jev-state-agents/work.md) 구현으로 2AS(2026-10-23, [2AS change](../../openspec/changes/jev-gemini-two-agent/work.md))를 대체했다. 현재 [아키텍처](../architecture/overview.md)와 jev-state-agents change를 기준으로 이어간다. 이전 Verify/입력 제안을 새 구조에 채택한 것으로 취급하지 않는다.

2026-11-23 상위 [Supervisor](supervisor-and-chat.md)를 추가했다. 기존 통화 계약은 유지한다. 후속 주제는 실제 STT·화자/partial/재전송 계약, 서버의 Supervisor 연결·저장·직렬화, 탐지 품질 평가와 실제 조회 도구다. 사용자 방향은 [프로젝트 컨텍스트](../project-context.md)에 있다.
