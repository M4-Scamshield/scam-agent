# 첫 통화 데모의 State와 실행 흐름

상태: 데모 시나리오·검증 계획. 공통 실행 규칙은 [ScamShield MVP 전체 스펙](state-and-graph.md)에서 정리 완료했다. 구성요소별 내부 계약은 같은 전체 스펙에 통합했으며 외부 연결 계약·구현·실행 검증은 후속 작업이다. 최초 초안의 가정 대신 해당 공통 설계의 사용자 결정과 위임에 따른 보완 선택을 적용한다.

## 목적과 범위

전체 한국어 대화를 통화별로 유지하고 OBSERVE → SUSPECT → VERIFY → 검증 결과 저장 → Jev 재판단 → WARN을 실행한다. 첫 검증은 Fake Jev와 Mock 조회 데이터로 수행한다. 이 단계의 통과를 실제 탐지 정확도나 공공기관 조회 성공으로 해석하지 않는다.

## State와 입력

ScamState의 도메인 필드는 `transcript`, `phase`, `risk`, `verification_results`, `response`이며 실행 값은 `utterance`, `tool_request`, `verification_attempted`다. Q9 Option A에 따라 `signals`는 MVP State에서 제외한다. Q10 Option A에 따라 response는 State·checkpoint에 저장하고 update_context가 새 STT turn 시작 시 None으로 초기화한다. Q12에 따라 첫 통화는 phase=OBSERVE·대화/검증 결과 빈 목록·response=None으로 시작하고 risk는 최초 성공 판단 전 값 없음이다. 공통 보완에서 미평가 risk=None과 실행 필드 초기화/소비를 정리했다. 코드 타입 선언은 구현 단계에서 작성한다. transcript와 verification_results는 Q1/Q2의 전체 목록 기본 교체 방식으로 누적한다. 새 발화와 누적 Transcript를 구분하고 전체 대화를 유지한다. 필드별 책임과 결정할 항목은 [상세 설계](state-and-graph.md)에 있다.

Graph의 호출 설정은 `thread_id = callId`이며 InMemorySaver를 사용한다. Q13에 따라 sync로 checkpoint 저장을 끝낸 뒤 다음 step을 진행한다. 프로세스 재시작 복구는 범위 밖이다. Q14에 따라 통화 종료 후에도 State·checkpoint를 프로세스 생존 동안 보관하고 새 통화마다 고유 callId를 사용한다. 종료 이벤트 기반 삭제·자동 cleanup은 현재 추가하지 않는다. 검증 결과는 통화 전체 누적(Q2 Option A)으로 결정했다. 같은 통화에서는 순차 실행하고 Tool 대기에 시간 제한을 둔다(Q5). 도구별 결과 상세 schema·재조회는 Tool 스펙에서 정한다. 공통 설계는 VERIFY 종료 안내·설정 가능한 timeout 기본 5초·가능한 취소와 늦은 완료 결과 폐기를 정리했다. Tool 오류·timeout은 검증하지 못한 결과로 저장해 Jev가 재판단한다(Q11). Tool 대기 중 다음 발화를 먼저 판단하고 늦은 결과를 반영하는 방식은 후속 개선으로 연기했다.

외부 입력의 출발 경계는 `{callId, utterance}`다. Q6에 따라 데모 입력은 완성된 final utterance가 중복 없이 한 번씩 전달된다는 전제이며 발화 ID 기반 중복 제거는 추가하지 않는다. Q1에 따라 새 발화를 Graph 입력 channel utterance로 전달하고 update_context가 기존 transcript + [새 발화]의 전체 목록으로 교체한 뒤 utterance=None으로 비운다. Jev·Agent는 갱신된 전체 대화와 현재 State를 읽는다. 실제 STT 연동 시 재전송 처리는 후속 입력 계약에서 다룬다. 내부 정상 결과는 `{callId, risk, phase, response, verification_results}`이고 실행 오류는 별도 error 결과다. 외부 API envelope는 후속 입력·응답 연결 스펙에서 정한다. 실시간 중간 risk 전송은 별도 STT·프론트 연결 단계의 주제다.

## Node와 Edge

Node별 책임·읽기/쓰기와 Graph 그림의 기준은 [ScamShield MVP 전체 스펙](state-and-graph.md)이다. update_context → Jev 판단 → phase별 실행으로 진행하며 검증 결과를 저장한 뒤 Jev가 다시 판단한다.

최초 판단과 검증 후 재판단은 같은 Detection 책임을 사용하고 호출 직전 phase를 읽는다. Q8에 따라 detect_with_jev가 Jev 출력 schema와 허용 phase 전이를 검사한 뒤 State에 반영한다. Jev·Agent 호출·출력 검증 실패는 자동 재시도 없이 오류를 반환한다(Q11). Tool 오류·timeout은 실패 결과를 누적한 뒤 Jev가 재판단하며(Q11) 공통 실패 형식·timeout 뒤 처리·다음 새 turn의 실행 규칙은 공통 설계를 따른다. risk 범위·기준 수치는 Jev 스펙에서 정한다. 조건부 Edge와 Warning은 deterministic code다. 핵심 네 전이와 OBSERVE → VERIFY risk 진입 조건을 채택했고, risk 척도·기준 수치는 Jev 스펙에서 정하며 미평가 risk는 None이다. suspect_agent·warn은 이번 안내를 response에 기록한다(Q10).

Q7 Option A에 따라 verify_agent Node가 Tool과 인자를 선택하고 독립 tool_execution Node가 실행·결과 저장을 맡은 뒤 Jev 재판단으로 이어진다. Node 사이 전달은 State의 tool_request={tool,input}와 소비 후 None을 사용한다. 도구별 상세 schema는 Tool 스펙에서 정한다. 별도의 Evidence Extraction Node나 Supervisor는 없다. 대화 누적의 기준은 부모 State의 전체 Transcript다.

Q4 Option A를 채택해 한 발화에서 Tool 호출 최대 1회와 Jev 재판단 1회만 수행한다. 재판단이 다시 VERIFY여도 같은 turn에서는 추가 검증하지 않고 END한다. 검증 후 다시 VERIFY와 요청 없음은 안내 후 종료한다. 여러/잘못된 요청은 실행 오류다. 검증 시도 boolean으로 추가 실행을 막으며 실패/timeout 처리는 공통 설계를 따른다.

## Agent와 검증 도구

Suspect Agent는 전체 State를 읽고 짧은 확인 행동을 생성한다. 외부 Tool은 없다. Verify Agent는 전체 State와 기존 검증 결과를 읽고 필요한 조회를 선택한다. 두 역할은 분리된 LangChain Agent로 구성한다.

Q2에 따라 검증 결과의 공통 형식은 tool·input·status·result·is_mock으로 채택했다. status=OK는 실행 완료이며 안전 판정이 아니다. NOT_FOUND 같은 조회 내용은 result에, 오류·시간 초과는 ERROR/TIMEOUT 상태로 담는다. 세부 의미와 예시는 [State·Graph 설계 Q2](state-and-graph.md#q2-verification_results는-전체-누적일까-최근-검증-batch일까)를 따른다. tool_execution이 기존 결과 + [새 결과]의 새 전체 목록을 기본 교체로 저장하고 append reducer는 사용하지 않는다. Mock case_lookup의 상세 내부 schema는 전체 스펙에 기록했으며 실제 조회 계약은 미정이다. Fake·Mock의 한계를 실제 기관 검증 결과와 구분하며, Mock 테이블에 없는 값만으로 실제 기관 미등록·불일치를 주장하지 않는다.

Fake Jev는 첫 데모의 정해진 결과를 재현하기 위한 구현이다. 위험도 숫자는 데모 fixture이며 실제 threshold가 아니다. 실제 Jev 연결은 전체 Transcript·이전 phase·검증 결과를 받고 risk·phase를 반환하는 계약이 확인된 뒤 수행한다.

## 검증할 동작

- 세 발화 이후 WARN 도달과 실제 조회 인자의 확인.
- 같은 callId의 Transcript 누적과 서로 다른 callId의 상태 분리.
- 정상 turn에서 새 발화를 한 번 추가하고 utterance=None으로 소비 완료, 검증 후 재판단에서 재append하지 않음.
- 첫 통화 기본값과 최초 성공 Jev 판단 전 risk 값 없음, 기존 통화의 phase·risk·검증 결과가 새 입력의 초기값으로 덮어써지지 않음.
- OBSERVE에서 Agent·Tool을 호출하지 않고 response가 비어 있음.
- 검증 결과를 저장한 뒤 전체 Transcript와 VERIFY phase로 다시 판단함. 결과의 공통 5개 필드·OK/ERROR/TIMEOUT 상태·Mock 여부와 조회 내용이 구분되어 보존됨. 기존 목록 뒤에 새 결과가 한 번 추가되고 Jev 재판단에서 다시 추가하지 않음.
- 정상 검증 또는 판단 불가를 일괄 WARN으로 바꾸지 않음.
- 최초 판단·검증 후 재판단에서 Jev 출력 schema와 허용 전이를 검사함. WARN 하향 같은 위반 결과를 정상 routing에 적용하지 않음. 호출·출력 검증 실패에서 자동 재시도 없이 오류 반환을 확인함. Tool 오류/timeout 결과 저장 후 Jev 1회 재판단·Tool 재호출 없음을 확인함. timeout의 실패 결과 한 번 저장·늦은 결과 폐기, 실패 뒤 마지막 저장 State를 유지하며 새 입력이 ENTRY부터 실행되는지 확인함.
- SUSPECT·WARN·VERIFY 종료에서 이번 안내가 저장되고 새 turn에서 이전 안내·요청·검증 시도 값이 초기화됨. 요청 실행 뒤 tool_request=None이며 여러/잘못된 요청을 실행하지 않음.

## 미확정 사항과 관련 문서

LLM Provider·모델과 실제 Jev API는 후속 구성요소 스펙에서 정한다. HTTP·WebSocket 및 Streaming STT 연결은 첫 Graph 검증 이후의 주제다. 내부 실행 경계는 공통 설계를 따르며 외부 STT/프론트 API 계약과 구현 완료를 뜻하지 않는다.

- [프로젝트 컨텍스트](../project-context.md)
- [State·Graph 공통 실행 설계](state-and-graph.md)
- [아키텍처 인덱스](../architecture/index.md)
- [첫 데모 change](../../openspec/changes/first-demo/proposal.md)
- [구현·검증 기록](../../openspec/changes/first-demo/work.md)
- [LangGraph Checkpointer](https://docs.langchain.com/oss/python/langgraph/persistence)
- [LangChain Agent](https://docs.langchain.com/oss/python/langchain/agents)
