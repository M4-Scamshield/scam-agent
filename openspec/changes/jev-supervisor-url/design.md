# 적용 설계

## 기존 구조와 변경

기존 CallPipeline은 자체 상태 저장 없이 입력 state를 읽고 결과 state를 돌려준다. 이를 `agents/call_agent.py`로 이동하고, 상위 `agents/supervisor.py`에서 필요할 때 호출한다. 공통 계약은 [Supervisor·채팅 설계](../../../docs/design/supervisor-and-chat.md)에 둔다. 기존 통화 알고리즘과 점수는 [State·Graph](../../../docs/design/state-and-graph.md)를 유지한다.

## 코드와 의존성

`supervisor.py` → `call_agent.py` / `url_agent.py`. `call_agent.py` → `jev_agent.py` / `analysis_agent.py`. `analysis_agent.py`와 `url_agent.py`는 공통 [Claude 전송](../../../scamshield/llm.py)을 사용해 URL 역할이 통화 분석 역할을 상속하지 않게 한다. 공통 state·tools·tactics는 패키지 상위에 유지한다. `graph.py`는 BE의 기존 import를 유지하는 공개 진입점이다.

Jev HTTP 어댑터에 공통 choice 평가 함수를 두고 Supervisor 질문 2개와 기존 F1~F6 질문 6개가 공유한다. STT 처리 시 Supervisor 1회와 기존 상태 감지 1회가 각각 실행된다. URL agent는 Haiku 도구 요청→Mock 결과 반환→추가 도구 없는 마무리의 최대 2회 호출이다. 판정은 도구 결과로 고정한다.

## 선택과 한계

구조 표시 후속 요청에 따라 exporter는 상위와 하위 통화 그래프를 각각 컴파일해 `Graph.extend(prefix="call_agent")`로 연결한다. 하위 경계 START/END를 제거하고 기존 call_agent의 입출력 조건부 간선을 하위 입구·출구로 옮긴다. `judge_states`에는 `analysis_agent (Haiku)` 표시를 붙인다. 시각화 전용 처리로 런타임 라우팅은 유지하며 접은 출력은 `--compact`로 제공한다.

채팅을 소비 후 삭제하면 감사·재시도 맥락이 사라진다. 원문은 서버에 남기고 ID별 처리 영수증과 통화 내 URL 캐시를 state로 왕복한다. URL 전용 입력과 STT가 함께 있으면 통화 경로를 먼저 실행한 뒤 URL 경로를 실행한다. 두 경로의 결과는 통화 점수에 임의로 합산하지 않는다.

서버 저장 이전 재시도·동시 요청의 정확히 한 번 실행은 보장하지 않는다. 서버가 방 단위 직렬화·원자적 저장·요청 중복 제거를 구현해야 한다. 실제 모델 연결과 URL 평판 서비스는 후속이다.

[proposal](proposal.md), [spec](spec.md), [work](work.md)
