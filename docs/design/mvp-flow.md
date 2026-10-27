# 2AS 입력과 실행 흐름

현재 기준은 [2AS State·Graph 계약](state-and-graph.md)이다. 기존 Fake Jev·Mock 조회 데모는 [과거 실행 기록](../../openspec/changes/first-demo/work.md)으로 보존한다.

## 이번 turn의 흐름

1. 완성된 STT 문자열을 `CallPipeline.run_turn(call_id, utterance)`로 전달한다. 현재 CLI 텍스트 입력이 이 경계를 대신한다.
2. update_context가 대화를 누적하고 이번 판정·분석을 비운다.
3. Jev가 전체 대화를 읽고 Yes/No와 P(Yes)를 반환하면 State에 저장한다.
4. No는 analysis=None으로 종료한다. Yes는 Gemini가 대화·Jev 결과를 읽어 reason/response를 저장하고 종료한다.

다음 발화도 같은 callId로 전체 대화를 평가한다. 이전 Yes가 새 Yes를 강제하지 않는다. 실제 STT 수신·화자/partial·Kafka는 이번 범위 밖이다.

## 실행 확인

`--offline --auto`의 준비된 세 문장은 일상 대화 → 기관 사칭/범죄 연루 → 안전계좌 송금 요구다. offline 대역에서 No → Yes → Yes를 고정 규칙으로 보여준다. 실제 Jev의 선택·확률과 Gemini 출력은 모델이 결정하므로 fixture와 동일하다고 가정하지 않는다.

직접 텍스트 한 건은 `--text`로 전달한다. 기본 CLI의 Enter 입력과 `--auto`는 세 turn 뒤 종료하는 데모이며 Graph의 turn 한도가 아니다. 명령·키 설정은 [README](../../README.md), 현재 검증은 [2AS work](../../openspec/changes/jev-gemini-two-agent/work.md)를 따른다.
