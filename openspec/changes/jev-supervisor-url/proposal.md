# Jev Supervisor와 채팅 URL 분석

## 문제와 목표

2026-11-23 사용자 요청: 기존 STT 통화 분석 위에 Jev Supervisor를 두고, 채팅의 URL은 별도 에이전트가 Tool Calling으로 확인한다. URL 검색 도구는 Mock 함수로 한정한다. 에이전트는 `scamshield/agents/`에 역할별로 정리하며 `supervisor.py` 외에는 `*_agent.py`, 기존 Haiku 분석은 `analysis_agent.py`로 이름 붙인다.

## 범위와 완료 조건

기존 통화 API를 유지하면서 Supervisor 입구·채팅 ID 중복 방지·URL Mock Tool Calling·역할별 코드 이동을 구현하고 API 없는 테스트와 CLI로 확인한다. 채팅 기록을 삭제하지 않아도 같은 입력이 반복 라우팅되지 않아야 한다. STT와 URL이 함께 오면 두 경로를 실행한다.

BE 구현·DB 변경·실제 URL 평판 조회·실제 모델 성능 평가는 이번 범위 밖이다. 서버의 상태 보존·동시 요청 직렬화가 필요한 경계를 문서로 남긴다.

## 관련 문서

[Supervisor 계약](../../../docs/design/supervisor-and-chat.md), [통화 계약](../../../docs/design/state-and-graph.md), [이전 change](../jev-state-agents/design.md), [spec](spec.md), [design](design.md), [tasks](tasks.md), [work](work.md)
