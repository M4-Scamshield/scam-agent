# 입력과 실행 흐름

현재 기준은 [State·Graph 계약](state-and-graph.md)이다. 2AS와 기존 Fake Jev·Mock 조회 데모의 기록은 [2AS work](../../openspec/changes/jev-gemini-two-agent/work.md)와 [과거 실행 기록](../../openspec/changes/first-demo/work.md)으로 보존한다.

## 요청 하나의 흐름

1. BE `agent-bridge`(또는 CLI)가 이전 대화 `history`, 이번 새 줄 `new_lines`, 이전 출력 `state`, 시각 `now`로 `CallPipeline.analyze`를 부른다.
2. Jev가 최근 4줄과 새 줄로 F1~F6이 새 줄에 나타났는지 감지한다.
3. 켜진 상태 중 부를 상태만 Haiku가 전체 대화로 판단한다. F3·F5만 켜진 동안은 보류한다.
4. 상태 판단으로 통화 상태·점수·안내를 만들고 다음 요청에 넘길 `state`를 돌려준다.

## 실행 확인

CLI는 대화와 `state`를 직접 들고 요청을 이어 보내며, 시각은 `time.time()`이다. 화자 표시가 없는 입력은 `[상대]` 말로 본다. `--offline --auto`의 준비된 세 문장은 일상 대화 → 기관 사칭·범죄 연루 → 안전계좌 송금 요구다. offline 대역은 키워드 규칙과 고정 판단(F1·F2 `risky`, 나머지 `uncertain`)으로 정상 → 주의 → 위험을 보여 준다. 실제 Jev·Haiku 출력은 모델이 정하므로 대역과 같다고 가정하지 않는다.

직접 텍스트 한 건은 `--text`로 넣는다. 기본 CLI의 Enter 입력과 `--auto`는 세 요청 뒤 끝나는 데모다. 명령·키 설정은 [README](../../README.md), 현재 검증은 [jev-state-agents work](../../openspec/changes/jev-state-agents/work.md)를 따른다.
