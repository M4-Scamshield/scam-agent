# 데모데이용 첫 통화 흐름

상태: 데모 구현·API 없는 CLI/핵심 검사·실제 Gemini 세 발화 실행 완료. 기준은 [MVP 전체 스펙](state-and-graph.md)이며 실제 검증 근거는 [work](../../openspec/changes/first-demo/work.md)에 있다.

## 시나리오

| 발화·결과 | 기대 판단·실행 |
|---|---|
| “안녕하세요. 서울중앙지검입니다.” | Fake Jev → OBSERVE 0.1, 안내 없이 종료 |
| “고객님 계좌가 범죄에 연루되었습니다.” | Fake Jev → SUSPECT 0.5, Suspect 안내 생성 |
| “사건번호는 2026-12345입니다.” | Fake Jev → VERIFY 0.7, Verify의 실제 Tool Calling으로 case_lookup 선택 |
| 해당 번호의 Mock OK + NOT_FOUND 결과 저장 | 동일 transcript + 누적 결과로 Fake Jev 재판단 → WARN 0.9, 고정 경고 |

Fake는 호출 횟수로 판단하지 않고 정해진 대화 맥락과 해당 번호의 검증 결과를 읽는다. 위 risk와 VERIFY >= 0.6은 데모 전용이며 실제 모델 기준이 아니다. Mock 결과를 실제 기관 조회/사기 확정으로 표시하지 않는다.

## 구성·입출력

같은 callId는 동일 InMemorySaver/thread로 State를 유지한다. CLI가 turn 완료를 기다린 뒤 다음 발화를 보내며 Node 순서·phase/risk·Tool 요청/결과·response를 출력한다. 원문 발화와 검증 결과는 전체 목록 기본 교체로 누적한다.

Gemini Developer API의 gemini-3.8-flash를 두 역할이 공유한다. Suspect는 Tool 없이 안내 1회, Verify는 Tool Calling 1회다. SDK 연결과 실제 모델 두 역할 호출을 확인했다. 계정의 무료 한도나 지속적인 성공은 검증하지 않았다. Agent 대역·SDK 전송 대역 검사와 실제 Tool Calling 실행 근거는 구분한다.

현재 상대방 발화는 하드코딩된 세 문장 또는 직접 입력이며 상대방 AI·STT는 없다. CLI는 세 차례 입력 후 종료하고 Graph는 같은 정상 callId의 추가 turn을 처리할 수 있다. 실제 Gemini와 Fake/Mock의 역할·조회 조건·직접 실행 방법은 [README](../../README.md)에서 확인한다.

Tool 요청은 {tool,input}으로 State에 전달한다. 독립 tool_execution이 즉시 반환 Mock case_lookup을 한 번 실행·저장하고 요청을 비운다. turn당 실제 Tool 최대 1회·결과 후 Jev 재판단 1회를 유지한다. 결과 공통 형식과 초기값·Node별 쓰기 책임은 [전체 스펙](state-and-graph.md)을 따른다.

실행 오류는 해당 통화 시나리오를 중단하고 새 callId로 처음부터 재시작한다. 실패 통화의 State/checkpoint는 관찰용으로 유지하며 같은 callId로 계속 처리하거나 중간 재개하지 않는다. 기본 오류 반환과 유효하지 않은 출력 거부는 유지한다.

## 첫 완료 조건

- CLI 세 발화에서 OBSERVE → SUSPECT → VERIFY → 검증 결과 저장 → WARN.
- 같은 통화의 transcript 3개·결과 1개 유지와 새 callId의 분리.
- 실제 모델의 Suspect 안내·Verify Tool 선택/인자와 선택·실행 Node 분리.
- 호출 횟수 대신 해당 조회 결과를 반영한 Jev 재판단.
- 실제 Tool 1회·결과 후 Jev 재판단 1회와 중복 없는 누적.
- 출력으로 Node 흐름·phase/risk·Tool/안내를 확인할 수 있음.

실제 Gemini 성공 실행 이후 사건번호 일부 선택을 INVALID_OUTPUT으로 거부하도록 리뷰 수정을 적용했다. 수정 후 API 없는 테스트 31개·CLI WARN을 확인했으며 실제 모델은 재호출하지 않았다. 상세 실행 시점과 근거는 [work](../../openspec/changes/first-demo/work.md)에 있다.

## 후속 범위

실제 Jev·공공기관 조회·추가 Tool·STT/프론트 연결·동시 입력/수신 큐·실패한 통화의 재개·timeout 취소/늦은 완료 검증·다양한 오류 fixture는 첫 완료 조건에서 제외한다. 기존 공통 ERROR/TIMEOUT 형식은 보존하며 외부 연동 시 구체화한다.

관련 기준은 [프로젝트 컨텍스트](../project-context.md), [요구](../../openspec/changes/first-demo/spec.md), [작업](../../openspec/changes/first-demo/tasks.md), [검증 기록](../../openspec/changes/first-demo/work.md)에 있다. 실행 명령은 [README](../../README.md), 현재 구성은 [아키텍처](../architecture/overview.md)에서 확인한다.
