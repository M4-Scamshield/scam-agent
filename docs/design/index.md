# 상세 설계 문서

현재 계약과 후속 제안을 구분한다. 전체 진입점은 [문서 지도](../index.md)다.

| 문서 | 포함한 내용 |
|---|---|
| [2AS State·Graph 계약](state-and-graph.md) | 현재 Jev Yes/No·P(Yes), Gemini 분석·대응, State·실패·통화 수명 |
| [2AS 입력과 실행 흐름](mvp-flow.md) | STT 텍스트 경계와 CLI·offline 실행, Yes/No 종료 |

2AS는 2026-10-23 사용자 요청에 따라 기존 phase·Suspect/Verify·Mock 조회 흐름을 대체한다. 현재 [아키텍처](../architecture/overview.md)와 [2AS change](../../openspec/changes/jev-gemini-two-agent/work.md)를 기준으로 이어간다. 이전 Verify/입력 제안을 새 구조에 채택한 것으로 취급하지 않는다.

후속 주제는 실제 STT·화자/partial/재전송 계약, 서버 전달, 탐지/확률·대응 품질 평가, 필요한 조회 도구의 별도 설계다. 사용자 방향과 과거 맥락은 [프로젝트 컨텍스트](../project-context.md)에 있다.
