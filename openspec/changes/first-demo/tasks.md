# 첫 데모 작업 목록

상태: 완료 — 이번 데모 구현·API 없는 검사·실제 Gemini 안내/Tool Calling·최종 WARN을 확인했다. 아래 과거 설계 체크는 당시 문서 반영의 근거이며 현재 구현 완료와 구분한다. 실행 근거는 [work](work.md)에 있다. 미체크 항목은 후속 범위다.

## 설계·준비의 진행 이력

아래 항목은 구현 전의 문서 반영 기록이다. 당시 미정/미착수였던 데모 내부 계약·코드는 아래 구현 항목에서 완료했으며, 과거 timeout/실패 뒤 새 turn 선택은 데모 범위 축소로 대체했다.

- [x] 현재 문서·실행 환경과 확정 방향을 확인한다.
- [x] 첫 Graph 실행의 State·Node·Agent·Tool 경계를 설계 문서로 남긴다.
- [x] [State·LangGraph 상세 설계 초안](../../../docs/design/state-and-graph.md)에 확정 전제와 Open Question을 구분한다. 근거: [work](work.md).
- [x] 이번 utterance와 누적 transcript를 분리하는 사용자 채택 범위를 반영한다. 후속 답변에서 입력 channel·기본 교체·소비 후 None 초기화를 채택했다. 후속 공통 보완으로 실패 뒤 새 turn을 선택했다. 당시 코드 타입 선언·실행 검증은 미착수였다. 근거: [work](work.md).
- [x] Q2 Option A(통화 전체 Tool 검증 결과 누적)를 반영한다. 후속 답변에서 공통 5개 필드와 전체 목록 기본 교체를 채택했다. 당시 도구별 상세 schema·재조회 세부 규칙은 미정이었다. 근거: [work](work.md).
- [x] Q3 핵심 전이와 OBSERVE → VERIFY의 risk 진입 조건을 반영한다. 기준 수치는 Jev 스펙에서 정하고 공통 코드가 검증한다. 근거: [work](work.md).
- [x] Q4 Option A(turn당 Tool 최대 1회·Jev 재판단 1회·같은 turn 재검증 없음)를 반영한다. 후속 공통 보완에서 종료 안내·내부 오류 경계를 정리했다. 근거: [work](work.md).
- [x] Q5 Option A의 순차 처리와 Tool 대기 시간 제한 방향을 확정하고, 새 발화 판단·늦은 Tool 결과 반영 방식은 후속 개선으로 기록한다. 후속 공통 보완에서 기본 5초·가능한 취소·늦은 결과 폐기를 선택했다. 근거: [work](work.md).
- [x] Q7 Option A(Tool 선택과 실행을 독립 Graph Node로 분리)를 반영한다. 후속 공통 보완에서 tool_request로 전달·보관·소비를 정리했다. 근거: [work](work.md).
- [x] Q9 Option A(signals를 MVP State에서 제외)를 반영한다. 실제 Jev 출력 schema는 미정. 근거: [work](work.md).
- [x] Q10 Option A(response를 State·checkpoint에 저장하고 새 STT turn 시작 시 None으로 초기화)를 반영한다. 후속 공통 보완에서 VERIFY 안내·내부 출력 경계를 정리했다. 외부 API 계약은 후속 범위. 근거: [work](work.md).
- [x] Q8 Option A(Jev 출력 schema·허용 phase 전이의 코드 검증)를 반영한다. 검증 실패는 Q11의 오류 반환 정책을 적용하며 당시 risk 범위와 기준 수치는 미정이었다. 근거: [work](work.md).
- [x] Q11 Option A 중 Jev·Agent 호출/출력 검증 실패의 자동 재시도 없는 오류 반환을 반영한다. 후속 공통 보완으로 중간 재개 없이 새 발화로 새 turn을 시작하도록 정리했다. 근거: [work](work.md).
- [x] Q11의 Tool 실패 Option A(실행 오류/timeout을 실패 결과로 저장 후 Jev 재판단)를 반영한다. 실행 상태 ERROR/TIMEOUT은 Q2로 채택. 후속 공통 보완에서 code/message 실패 형식·설정 가능한 timeout 기본 5초·늦은 결과 폐기를 선택했다. 도구별 세부 오류는 후속 범위. 근거: [work](work.md).
- [x] Q12의 첫 통화 기본값(phase=OBSERVE, 대화/검증 결과 빈 목록, response=None, 최초 성공 판단 전 risk 값 없음)을 반영한다. 후속 공통 보완에서 None 표현을 선택했다. 근거: [work](work.md).
- [x] Q13 Option A(sync checkpoint 저장)를 반영한다. 당시 Graph 호출 코드와 동작 검증은 후속 구현 단계로 남겼다. 근거: [work](work.md).
- [x] Q14 Option A(프로세스 생존 동안 State·checkpoint 보관, 새 통화마다 고유 callId)를 반영한다. 당시 실제 구현·실행 검증은 미착수였다. 근거: [work](work.md).
- [x] Q6 Option A(final 발화·중복 없는 데모 입력 전제)를 반영한다. 실패 뒤 새 입력 정책은 공통 보완에서 정리했다. 실제 STT 재전송은 연결 스펙의 역할이다. 근거: [work](work.md).
- [x] Q1의 Graph utterance 입력·transcript 새 전체 목록 기본 교체·소비 후 utterance=None을 반영한다. 후속 공통 보완으로 실패 뒤 새 turn을 선택했다. 당시 코드 타입 선언·실행 검증은 미착수였다. 근거: [work](work.md).
- [x] Q2의 검증 결과 공통 형식(tool·input·status·result·is_mock)과 실행 상태 OK/ERROR/TIMEOUT을 반영한다. 후속 답변에서 목록 merge도 채택했다. 공통 실패 상세는 후속 보완의 code/message 형식. 도구별 상세 schema는 후속 범위. 근거: [work](work.md).
- [x] Q2 목록 merge A안(기존 결과 + [새 결과] 전체 목록 기본 교체, append reducer 없음)을 반영한다. 실행 재개 대신 새 turn 정책을 후속 보완했다. 재조회는 Tool 스펙에서 정함. 근거: [work](work.md).
- [x] 사용자 위임에 따라 남은 공통 실행 경계(요청 전달/소비·검증 시도 표시·종료/오류 출력·실패 뒤 새 turn·timeout 기본값)를 정리하고 공통 설계의 역할·완료 조건·후속 스펙을 명시한다. 개별 사용자 승인과 에이전트 보완 선택을 구분한다. 근거: [work](work.md).
- [x] 같은 문서에 Jev·Agent·Mock Tool 내부 계약, 입력/응답, 데모 인수조건을 통합해 MVP 전체 스펙 초안을 작성한다. 당시 외부 연결과 구현 검증은 미완료였다. 근거: [work](work.md).
- [x] 데모 리뷰를 반영해 Fake risk/판단 규칙·CLI·공유 모델 호출 계약을 정하고 복구/동시 입력/timeout 검증을 첫 범위에서 제외한다. 근거: [work](work.md).
- [x] 구현/제외/전체 흐름의 세 구역으로 [첫 데모 구현 이슈 #1](https://github.com/M4-Scamshield/scam-agent/issues/1)을 생성한다. 근거: [work](work.md).

## 데모 구현·검증 완료
- [x] 로컬 키로 해당 Gemini 모델의 안내/Tool Calling과 세 발화 CLI 성공을 확인한다. 계정의 무료 한도 조사와 구분한다. 근거: [work](work.md).
- [x] 사용자 터미널의 실제 Suspect 호출 실패 보고를 반영해 키를 숨기는 API 오류 진단을 보완한다. 도구 실행의 ConnectError를 확인했고 네트워크 허용 후 성공했다. 사용자 최초 실패의 당시 원인은 확정하지 않는다. 근거: [work](work.md).
- [x] Python 버전·의존성·lock 파일을 구성하고 lock 정합성을 확인한다. 근거: [work](work.md).
- [x] 기존 Python 3.12 환경에 Gemini 의존성을 설치하고 lock·동기화·데모 실행을 검증한다. 새 머신 설치 검증과 구분한다. 근거: [work](work.md).
- [x] State·Graph·Fake Jev·Mock Tool을 구현한다. 근거: [work](work.md).
- [x] 데모용 역할별 LLM 1회 호출과 Verify Tool Calling을 연결한다. SDK 전송 대역으로 요청/응답 변환을 검증했고 Agent 런타임 구현·실제 API 호출과 구분한다. 근거: [work](work.md).
- [x] API 없는 CLI 세 발화·상태 누적/통화 분리·Tool 선택/실행 분리·결과 반영·turn당 Tool 최대 1회와 결과 후 재판단 1회를 확인한다. 근거: [work](work.md).
- [x] 실제 Gemini로 Suspect 안내·Verify Tool 선택/인자·CLI WARN을 확인한다. 같은 통화 대화 3개·Mock 결과 1개를 확인했다. 근거: [work](work.md).
- [x] 실제 구현 범위·실행 명령·검증 결과를 문서와 [work](work.md)에 반영한다.
- [x] 리뷰 P2의 사건번호 부분 문자열 통과를 수정하고 `2026`/`12345` 요청의 INVALID_OUTPUT·Tool 미실행·결과 미저장을 API 없는 회귀 검사로 확인한다. 근거: [work](work.md).
- [x] 스펙부터 현재 구현까지 문서 정합성을 검토하고 CLI/Fake/Mock·화자 STT·오류/timeout 범위·실행 시점별 근거를 맞춘다. 근거: [work](work.md).
- [x] 사용자 요청에 따라 Graph·Gemini·CLI·문서를 기능별 로컬 커밋으로 기록한다. 당시 커밋 요청에는 push·PR을 포함하지 않았다. 근거: [work](work.md).
- [x] 후속 사용자 요청에 따라 현재 브랜치를 push하고 PR 스킬/양식으로 [PR #2](https://github.com/M4-Scamshield/scam-agent/pull/2)를 생성한다. 근거: [work](work.md).

2026-10-12 리뷰 반영으로 과거 체크 항목의 실패 뒤 새 turn·timeout 기본값 등은 현재 스펙의 단순화된 데모 범위로 대체했다. 과거 체크는 당시 문서 반영 근거이며 후속 기능의 구현 완료를 뜻하지 않는다.

## 후속 TODO — Agent 실행 구조

- [ ] 데모 이후 Suspect/Verify를 Agent 실행 객체·런타임으로 구현하고 Node의 직접 LLM 호출을 Agent 실행 호출로 전환한다. 구체적인 실행/Tool 책임과 검증은 [설계 TODO](../../../docs/design/state-and-graph.md#todo--데모-이후-agent-실행-구조로-전환)를 따른다. 현재 데모의 필수 완료 조건은 아니다.

## 후속 TODO — 실제 연결

- [ ] 실제 Jev·기관 조회의 외부 계약과 인증/risk/실행 오류·Tool timeout을 필요에 맞춰 구체화한다.
- [ ] 상대방과 사용자 양쪽 STT·화자 구분·같은 통화 누적을 위한 발화/State 입력 계약을 설계하고 연결한다. 현재 문자열 transcript의 구현 완료와 구분한다.
