# 아키텍처 문서

현재 시스템의 구성·책임 경계·데이터 흐름과 실제 구현 범위를 확인하는 위치다. 전체 진입점은 [문서 지도](../index.md)다.

## 현재 구현

[CLI 데모](overview.md)를 구현하고 API 없는 Graph·상태·Tool·CLI 검사와 실제 Gemini 안내/Tool Calling·최종 WARN 실행을 완료했다. 상세 계약은 [MVP 전체 스펙](../design/state-and-graph.md), 실행 근거는 [first-demo change](../../openspec/changes/first-demo/work.md)에서 확인한다.

## 문서 목록

| 문서 | 포함한 내용 |
|---|---|
| [현재 데모 구성](overview.md) | 컴파일된 LangGraph 구조도, CLI·Graph·State·Fake Jev·역할별 Gemini·독립 Mock 실행의 책임, 상태 수명과 실제 검증 범위 |

사용자가 제공한 방향은 [프로젝트 컨텍스트](../project-context.md), 세부 설계의 분류는 [설계 인덱스](../design/index.md)에 있다.
