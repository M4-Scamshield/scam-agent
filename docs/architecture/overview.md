# 현재 상태별 판단 구성

2026-11-22 기준 Jev 상태 감지(F1~F6) → 켜진 상태별 Claude Haiku 판단 → 통화 상태·점수 계산 LangGraph를 구현했다. 이전 Jev Yes/No + Gemini 2AS를 대체한다. 계약은 [State·Graph](../design/state-and-graph.md), 실행한 검증·한계는 [jev-state-agents work](../../openspec/changes/jev-state-agents/work.md)에 있다.

![컴파일된 ScamShield LangGraph](scamshield-langgraph.png)

이 이미지는 [export_graph.py](../../scamshield/export_graph.py)가 실제 `build_graph(OfflineDetector(), OfflineAnalyst())`를 컴파일한 뒤 추출한다. 대역과 실제 모델이 같은 Graph를 사용하며 내보내는 동안 모델 호출은 없다. [Mermaid 원본](scamshield-langgraph.mmd)도 함께 저장한다.

## 코드와 책임

| 코드 | 책임 |
|---|---|
| [state.py](../../scamshield/state.py) | 입력 `NewLine`, 출력 `AnalysisOutcome`, 요청 사이 상태 `AgentMemory`, Haiku 출력 검증, `PipelineError` |
| [tactics.py](../../scamshield/tactics.py) | 상태 F1~F6 정의, 우선순위·보류 기준·절대선 상태·점수 |
| [interfaces.py](../../scamshield/interfaces.py) | Detector/Analyst Protocol, 키 없는 offline 대역 |
| [jev.py](../../scamshield/jev.py) | TypeSafe HTTP 호출, 상태 6개 choice 질문, 상태별 Yes/No·P(Yes) 변환 |
| [haiku.py](../../scamshield/haiku.py) | 상태별 Haiku 프롬프트·호출·tool 왕복, 실패 분류 |
| [tools.py](../../scamshield/tools.py) | F1·F3 Mock tool(고정 목록) |
| [graph.py](../../scamshield/graph.py) | 라우팅, 동시 호출, 절대선·tool 보정, 점수·통화 상태·BE 필드, `build_pipeline` |
| [cli.py](../../scamshield/cli.py) | 여러 요청을 이어 보내는 데모 입력과 결과 출력 |
| [export_graph.py](../../scamshield/export_graph.py) | 컴파일된 그래프의 Mermaid·PNG 출력 |

## 수명과 범위

`analyze`는 상태를 저장하지 않는다. 통화 상태는 BE가 `state`로 저장해 다음 요청에 돌려준다. 대화 원문·화자 표기(통화방 참가자 id)·응답 변환은 BE `agent-bridge`가 맡는다. tool은 Mock이고 실제 조회 API는 없다. 실행 방법은 [README](../../README.md)에 있다.

## 검증

API 없는 Graph·Jev HTTP·Haiku 요청·Mock tool·CLI 검사는 [tests](../../tests/test_graph.py)에 연결된 테스트 모음으로 확인한다. 실제 Jev·Haiku 연결과 KorCCVi 평가는 아직이며 결과는 [work](../../openspec/changes/jev-state-agents/work.md)에 구분해 남긴다.
