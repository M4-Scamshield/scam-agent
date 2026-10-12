# 첫 데모 작업 목록

상태: 진행 중 — 공통 실행 설계 정리 완료, 구성요소별 내부 계약을 포함한 전체 스펙 초안 작성, 외부 계약 미정·서비스 구현 미착수. 체크는 설계·기록 작업의 완료이며 서비스 구현·실행 검증 완료를 뜻하지 않는다. 사용자 결정과 위임에 따른 에이전트 보완은 work에서 구분한다.

- [x] 현재 문서·실행 환경과 확정 방향을 확인한다.
- [x] 첫 Graph 실행의 State·Node·Agent·Tool 경계를 설계 문서로 남긴다.
- [x] [State·LangGraph 상세 설계 초안](../../../docs/design/state-and-graph.md)에 확정 전제와 Open Question을 구분한다. 근거: [work](work.md).
- [x] 이번 utterance와 누적 transcript를 분리하는 사용자 채택 범위를 반영한다. 후속 답변에서 입력 channel·기본 교체·소비 후 None 초기화를 채택했다. 후속 공통 보완으로 실패 뒤 새 turn을 선택했다. 코드 타입 선언·실행 검증은 미착수. 근거: [work](work.md).
- [x] Q2 Option A(통화 전체 Tool 검증 결과 누적)를 반영한다. 후속 답변에서 공통 5개 필드와 전체 목록 기본 교체를 채택했다. 도구별 상세 schema·재조회 세부 규칙은 미정. 근거: [work](work.md).
- [x] Q3 핵심 전이와 OBSERVE → VERIFY의 risk 진입 조건을 반영한다. 기준 수치는 Jev 스펙에서 정하고 공통 코드가 검증한다. 근거: [work](work.md).
- [x] Q4 Option A(turn당 Tool 최대 1회·Jev 재판단 1회·같은 turn 재검증 없음)를 반영한다. 후속 공통 보완에서 종료 안내·내부 오류 경계를 정리했다. 근거: [work](work.md).
- [x] Q5 Option A의 순차 처리와 Tool 대기 시간 제한 방향을 확정하고, 새 발화 판단·늦은 Tool 결과 반영 방식은 후속 개선으로 기록한다. 후속 공통 보완에서 기본 5초·가능한 취소·늦은 결과 폐기를 선택했다. 근거: [work](work.md).
- [x] Q7 Option A(Tool 선택과 실행을 독립 Graph Node로 분리)를 반영한다. 후속 공통 보완에서 tool_request로 전달·보관·소비를 정리했다. 근거: [work](work.md).
- [x] Q9 Option A(signals를 MVP State에서 제외)를 반영한다. 실제 Jev 출력 schema는 미정. 근거: [work](work.md).
- [x] Q10 Option A(response를 State·checkpoint에 저장하고 새 STT turn 시작 시 None으로 초기화)를 반영한다. 후속 공통 보완에서 VERIFY 안내·내부 출력 경계를 정리했다. 외부 API 계약은 후속 범위. 근거: [work](work.md).
- [x] Q8 Option A(Jev 출력 schema·허용 phase 전이의 코드 검증)를 반영한다. 검증 실패는 Q11의 오류 반환 정책을 적용하며 risk 범위와 기준 수치는 미정. 근거: [work](work.md).
- [x] Q11 Option A 중 Jev·Agent 호출/출력 검증 실패의 자동 재시도 없는 오류 반환을 반영한다. 후속 공통 보완으로 중간 재개 없이 새 발화로 새 turn을 시작하도록 정리했다. 근거: [work](work.md).
- [x] Q11의 Tool 실패 Option A(실행 오류/timeout을 실패 결과로 저장 후 Jev 재판단)를 반영한다. 실행 상태 ERROR/TIMEOUT은 Q2로 채택. 후속 공통 보완에서 code/message 실패 형식·설정 가능한 timeout 기본 5초·늦은 결과 폐기를 선택했다. 도구별 세부 오류는 후속 범위. 근거: [work](work.md).
- [x] Q12의 첫 통화 기본값(phase=OBSERVE, 대화/검증 결과 빈 목록, response=None, 최초 성공 판단 전 risk 값 없음)을 반영한다. 후속 공통 보완에서 None 표현을 선택했다. 근거: [work](work.md).
- [x] Q13 Option A(sync checkpoint 저장)를 반영한다. Graph 호출 코드와 동작 검증은 구현 단계에서 확인한다. 근거: [work](work.md).
- [x] Q14 Option A(프로세스 생존 동안 State·checkpoint 보관, 새 통화마다 고유 callId)를 반영한다. 실제 구현·실행 검증은 미착수. 근거: [work](work.md).
- [x] Q6 Option A(final 발화·중복 없는 데모 입력 전제)를 반영한다. 실패 뒤 새 입력 정책은 공통 보완에서 정리했다. 실제 STT 재전송은 연결 스펙의 역할이다. 근거: [work](work.md).
- [x] Q1의 Graph utterance 입력·transcript 새 전체 목록 기본 교체·소비 후 utterance=None을 반영한다. 후속 공통 보완으로 실패 뒤 새 turn을 선택했다. 코드 타입 선언·실행 검증은 미착수. 근거: [work](work.md).
- [x] Q2의 검증 결과 공통 형식(tool·input·status·result·is_mock)과 실행 상태 OK/ERROR/TIMEOUT을 반영한다. 후속 답변에서 목록 merge도 채택했다. 공통 실패 상세는 후속 보완의 code/message 형식. 도구별 상세 schema는 후속 범위. 근거: [work](work.md).
- [x] Q2 목록 merge A안(기존 결과 + [새 결과] 전체 목록 기본 교체, append reducer 없음)을 반영한다. 실행 재개 대신 새 turn 정책을 후속 보완했다. 재조회는 Tool 스펙에서 정함. 근거: [work](work.md).
- [x] 사용자 위임에 따라 남은 공통 실행 경계(요청 전달/소비·검증 시도 표시·종료/오류 출력·실패 뒤 새 turn·timeout 기본값)를 정리하고 공통 설계의 역할·완료 조건·후속 스펙을 명시한다. 개별 사용자 승인과 에이전트 보완 선택을 구분한다. 근거: [work](work.md).
- [x] 같은 문서에 Jev·Agent·Mock Tool 내부 계약, 입력/응답, 데모 인수조건을 통합해 MVP 전체 스펙 초안을 작성한다. 실제 외부 연결과 구현 검증은 미완료. 근거: [work](work.md).
- [ ] 전체 스펙 안에서 실제 Jev API/risk·Agent 모델/설정·외부 연결에 필요한 미정 계약을 확정한다.
- [x] Python 버전·의존성·lock 파일을 구성하고 lock 정합성을 확인한다. 근거: [work](work.md).
- [ ] 새 환경의 의존성 설치와 서비스 실행을 검증한다.
- [ ] State·Graph·Fake Jev·Mock Tool을 구현한다.
- [ ] 두 LangChain Agent와 Tool Calling을 연결한다.
- [ ] 첫 데모·통화 분리·검증 후 재판단을 테스트한다.
- [ ] 실제 구현 범위·실행 명령·검증 결과를 문서와 [work](work.md)에 반영한다.
