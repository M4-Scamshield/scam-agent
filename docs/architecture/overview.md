# 현재 2AS 구성

2026-10-27 기준 Jev 탐지 → Yes일 때 Gemini 분석·대응하는 LangGraph를 구현했다. 계약은 [State·Graph](../design/state-and-graph.md), 실행한 검증·한계는 [2AS work](../../openspec/changes/jev-gemini-two-agent/work.md)에 있다.

![컴파일된 ScamShield 2AS LangGraph](scamshield-langgraph.png)

이 이미지는 [export_graph.py](../../scamshield/export_graph.py)가 실제 `build_graph(OfflineDetector(), OfflineAnalyst())`를 컴파일한 뒤 추출한다. 대역과 실제 모델이 같은 Graph를 사용하며 내보내는 동안 모델 호출은 없다. [Mermaid 원본](scamshield-langgraph.mmd)도 함께 저장한다.

## 코드와 책임

| 코드 | 책임 |
|---|---|
| [state.py](../../scamshield/state.py) | 입력·State·Yes/No와 확률·reason/response 검증 계약 |
| [interfaces.py](../../scamshield/interfaces.py) | Detector/Analyst Protocol, 명시적인 offline 대역 |
| [jev.py](../../scamshield/jev.py) | TypeSafe HTTP 호출, Choice 확률을 내부 판정으로 변환 |
| [gemini.py](../../scamshield/gemini.py) | Yes일 때만 모델 설정·구조화 분석 1회 호출 |
| [graph.py](../../scamshield/graph.py) | 대화 누적, 판단 저장, Yes/No 분기, 분석 저장, checkpoint·오류 경계 |
| [cli.py](../../scamshield/cli.py) | 완성 텍스트 입력, 실행 순서·판정·확률·분석·안내 출력 |
| [export_graph.py](../../scamshield/export_graph.py) | 컴파일된 그래프의 Mermaid·PNG 출력 |

## 수명과 범위

같은 CallPipeline 인스턴스에서 thread_id=callId로 InMemorySaver를 공유한다. 전체 텍스트는 누적하고 판단·분석은 매 turn 비운 뒤 최신 값으로 교체한다. No는 LLM 호출 없이 종료하며 이전 분석을 남기지 않는다. 상태의 영구 저장과 동시 입력 처리는 없다.

기존 phase/조회 State, Suspect/Verify 역할, Mock case_lookup·tool_execution·재판단 loop와 관련 코드를 제거했다. 기존 데모 기록은 역사 자료이며 현재 동작 설명이 아니다. 실제 STT·웹 서버·도구 조회는 아직 없다. 실행 방법은 [README](../../README.md)에 있다.

## 검증

API 없는 Graph·Jev HTTP·Gemini SDK·CLI 검사는 [tests](../../tests/test_graph.py)에 연결된 테스트 모음으로 확인한다. 실제 Jev·Gemini 연결은 별도의 예제 통화로 확인하며 결과는 [work](../../openspec/changes/jev-gemini-two-agent/work.md)에 구분한다. 외부 모델 연결 성공과 탐지 성능 평가는 별개다.
