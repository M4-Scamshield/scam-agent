# 2AS 전환 요구사항

기준은 [State·Graph 계약](../../../docs/design/state-and-graph.md)이다. 이번 사용자 요청은 기존 phase/조회/재판단 구조를 대체한다.

- `run_turn(call_id, utterance)`로 완성된 STT 텍스트 한 건을 받아 통화 전체 대화에 추가한다.
- Jev Choice의 Yes/No 선택을 그대로 사용하며 별도 임계값을 만들지 않는다. 확률은 선택된 답의 confidence가 아닌 `probabilities.Yes`다.
- 판정·확률을 저장한 후 Yes만 Gemini로 분기한다. Gemini는 근거 요약 `reason`과 대응 `response`를 저장한다.
- No에는 analysis가 None이며 Gemini 설정·호출이 없어야 한다.
- 새 turn의 판단·분석을 비우고 새 callId는 대화를 공유하지 않는다.
- 실패/잘못된 출력은 오류로 반환한다. No 또는 offline 결과로 대체하거나 자동 재시도하지 않는다.
- 기존 역할·Mock Tool·옛 State 필드는 제거하고 테스트를 새 계약으로 교체한다.
- 그래프 그림은 컴파일된 LangGraph에서 추출한다. 실제 STT 수신과 도구 실행은 구현 완료로 표시하지 않는다.

진행과 검증 근거는 [tasks](tasks.md)·[work](work.md)에 남긴다.
