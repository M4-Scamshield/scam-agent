# Jev 상태 감지와 상태별 LLM 판단·대응

상태: 2026-11-16 팀장과 협의해 이 구조로 전환하기로 함, 2026-11-22 agent 구현으로 2AS 계약을 대체했다([State·Graph](../../../docs/design/state-and-graph.md)). 작업 이슈: [#13](https://github.com/M4-Scamshield/scam-agent/issues/13).

## 문제와 목표

- 지금 구조의 문제
  - Jev가 보이스피싱 여부를 Yes/No 하나로만 판단한다.
  - Yes이면 Gemini가 일반적인 대응을 한 번 내놓는다.
  - 그래서 대응이 대화 맥락과 상관없는 전역 문구가 되기 쉽다. 예: "공공기관은 앱 설치를 요구하지 않습니다"
- 2026-11-15 사용자 요청
  - KorCCVi 분석에서 나온 대화 특징 6가지(F1~F6)를 Jev가 감지하는 상태로 만든다.
  - 켜진 상태별로 LLM이 지금 대화를 보고 최종 판단과 대응을 한다. 예: "기관은 이걸 요구하지 않는다" 또는 "이 정도는 요구할 수 있다"
- 2026-11-16 팀장 협의
  - 상태별 LLM은 Claude API 에이전트로 쓴다. 현재 대응 LLM은 Gemini다.
  - 판단 결과마다 점수를 매겨 통화 단위로 합산한다. 점수 값은 정하지 않았다.
- 근거: [KorCCVi 수법 분석](../../../docs/analysis/korccvi-scam-tactics.md)

## 범위와 제외 범위

- 포함
  - 상태 정의와 Jev 질문 기준
  - 라우팅과 재호출 규칙
  - 상태별 LLM 입력·출력 계약과 절대선
  - Jev에 질문 여러 개를 보내는 실제 호출 확인
  - KorCCVi 라벨로 상태 감지 성능 평가
  - 상태별 에이전트 구현과 API 없는 테스트
- 제외
  - 백엔드(BE) 응답 계약 변경 구현. BE 팀과 합의한 뒤 별도로 진행한다.
  - 실제 tool API 연결(사기계좌·URL 조회 등). 이번에는 모의 구현까지만 한다.
  - UI

## 완료 조건

- Jev가 한 요청으로 F1~F6 상태별 Yes/No와 확률을 반환하는 것을 실제 호출로 확인한다.
- 상태가 새로 켜질 때만 해당 상태의 LLM을 부르고, 절대선 상태는 LLM이 "정상 범위"로 내리지 못한다. 이를 API 없는 테스트로 확인한다.
- KorCCVi 사기 통화에서 상태별 재현율과 감지 시점을 잰다. 정상 통화에서는 상태별 오탐을 잰다.

## 관련 상위 설계와 change 문서

[현재 계약](../../../docs/design/state-and-graph.md), [KorCCVi 분석](../../../docs/analysis/korccvi-scam-tactics.md), [korccvi-scam-tactics change](../korccvi-scam-tactics/proposal.md). 이번 [요구](spec.md), [설계](design.md), [작업](tasks.md), [기록](work.md)
