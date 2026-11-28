# ScamShield 상태별 판단 State·Graph 계약

상태: 2026-11-28 분석 재시도·진행 상태·근거 선택을 agent에 구현했다. 이번 실제 모델·BE·프론트 연결은 검증하지 않았다. [현재 검증·한계](../../openspec/changes/analysis-failure-handling/work.md)와 이전 [상태별 판단 구현](../../openspec/changes/jev-state-agents/work.md), 과거 [2AS 기록](../../openspec/changes/jev-gemini-two-agent/work.md)을 구분한다.

## 목적과 범위

새 통화 줄에서 Jev가 행동 F1~F6을 감지하고 선택된 상태마다 Haiku가 전체 대화로 최종 판단한다. 실패한 감지·분석은 최대 3회 추가 재시도하며, 진행 상태와 위험도를 별도로 반환한다. 실제 근거 발화를 선택·검증하고 직접 요구와 보조 맥락을 구분한다. 상태 정의는 [기존 spec](../../openspec/changes/jev-state-agents/spec.md)에 있다. 화자·STT·원문 저장과 실제 화면 연결은 호출 서버·프론트 책임이다.

## 실행 구조

전체 대화·원래 번호 검증 → Jev 감지와 재시도 → 상태별 Haiku·근거 검증과 재시도 → 위험도·완료 여부·실패 정보를 반환한다. 감지가 실패하면 분석 단계로 가지 않고 최종 실패를 반환한다.

입구는 [graph.py](../../scamshield/graph.py)의 CallPipeline.analyze(history, new_lines, state, now, on_progress=...)다. on_progress는 선택적인 키워드 인자다. 구현은 [call_agent.py](../../scamshield/agents/call_agent.py)에 있다. [Supervisor](supervisor-and-chat.md)도 같은 통화 분석과 진행 콜백을 사용한다. checkpointer나 요청 사이의 프로세스 저장소는 없다. 원문과 최신 state를 서버가 원자적으로 저장하고 같은 방의 요청을 직렬화해야 한다. 오래된 state를 재전송한 경우의 분산 중복 제거는 서버 책임이다.

build_pipeline(offline=False)는 두 API 키가 필요하다. 키가 없으면 config 오류이며 offline으로 자동 대체하지 않는다.

## 입력과 출력

- history: 이번 요청 전 전체 대화. 원래 seq가 있는 NewLine 또는 {seq, text}를 권장한다. 문자열 이력도 허용하지만 이전 state의 line_refs로 번호를 복원한다. 대괄호 안은 화자이며 사용자 입력 표시는 앱 입력이다.
- new_lines: 새 줄 {seq, text}, 1줄 이상. 알려진 전체 seq는 양의 정수이며 중복 없이 증가해야 한다.
- state: 이전 출력 state. None은 새 통화다.
- now: 유한한 초 단위 시각. 점수 감쇠에 사용한다.
- on_progress: 선택적인 동기 콜백. AnalysisProgress를 받으며 빠르게 반환해야 한다. 실제 HTTP/SSE/WebSocket 전송은 호출 서버가 구현한다.

[context.py](../../scamshield/context.py)의 line_refs는 원문 대신 SHA-256과 원래 seq만 보관한다. 이력의 길이·내용·번호가 이전 state와 다르면 입력 오류다. 과거 문자열 이력과 대응 state가 모두 없어 번호를 알 수 없으면 배열 위치를 seq로 추측하지 않는다. 그 줄이 근거로 선택되면 INVALID_EVIDENCE다. 마이그레이션 시 원래 seq가 있는 이력을 전달해야 한다.

AnalysisOutcome([state.py](../../scamshield/state.py)):

| 필드 | 의미 |
|---|---|
| analysis_status | 최종 completed 또는 failed. 진행 중은 콜백으로 전달 |
| failures | stage·state·code·attempts·seqs. 원래 실패 구간과 시도 횟수 |
| status | 완료 시 위험·주의·정상. 실패가 남으면 risky가 있을 때만 위험을 유지하고 그 밖은 None |
| score | 상태별 점수 합(최대 100). 실패가 남고 risky가 없으면 None |
| message | 가장 최근 risky의 안내, 비어 있으면 고정 안내. 위험이 아니면 None |
| reason | 최근 risky 또는 점수가 남은 uncertain 중 우선순위가 높은 상태의 이유 |
| evidence_seqs | 선택·검증된 직접 행동 근거의 원래 seq. 새 줄 전체를 복사하지 않음 |
| context_seqs | 판단에 필요한 신분·목적 등 보조 맥락의 원래 seq |
| states | 이번 Jev 상태별 verdict·P(Yes). 감지 실패면 빈 dict |
| state_analyses | 이번에 성공한 상태별 보정 전후 판단·도구 결과·선택 근거 |
| state | handled·call_context·seen·held·line_refs·failures. 다음 요청용 JSON |

## Jev 상태 감지

[jev_agent.py](../../scamshield/agents/jev_agent.py)는 시도마다 POST /v1/systemone을 한 번 호출한다. 이전 4줄과 새 줄을 보내고 새 대사에서 행동이 있는지 감지한다. 전송 timeout은 10초이며 통화 그래프가 실패한 감지를 최대 3회 추가 재시도한다. 최종 실패를 전부 No로 바꾸지 않는다. 키·주소·모델 환경변수는 TYPESAFE_API_KEY·TYPESAFE_BASE_URL·TYPESAFE_DEFAULT_MODEL이다.

상위 Supervisor 라우팅의 Jev 요청은 별개이며 이번 자동 재시도 대상이 아니다. 후보 감지 누락·맥락 변화 시 재평가 정책도 이번에 변경하지 않았다.

## 라우팅

- Yes인 상태 중 이전 판단이 risky가 아닌 상태를 부른다. risky는 다시 부르지 않고 uncertain·within_normal은 다시 Yes이면 부른다.
- F1·F2·F4·F6이 아직 감지되지 않았다면 F3·F5는 held로 보류한다. 핵심 상태가 처음 감지되면 보류 항목도 함께 부른다.
- 상태들은 동시에 실행하며 결과는 F1 → F3 → F2 → F5 → F4 → F6 순서로 정리한다. 각 상태의 실패는 그 상태만 재시도한다.

보류·risky 고정·점수 정책은 기존 계약을 유지했다. 따라서 completed는 이번 실행과 재시도가 종료됐다는 뜻이며 보류 정책의 탐지 품질까지 보장하지 않는다.

## 상태별 Haiku 판단

[analysis_agent.py](../../scamshield/agents/analysis_agent.py)는 [공통 전송](../../scamshield/llm.py)의 Haiku 모델·effort low·timeout 12초·SDK max_retries=0을 사용한다. 재시도는 통화 그래프가 맡아 SDK와 중첩하지 않는다. 매 시도에 전체 대화·감지 후보·이전 판단·통화 맥락의 같은 복사본을 전달한다.

출력은 판단·절대선·이유·안내·actions·call_context와 evidence_lines·context_lines다. 줄 번호는 대화상 1부터의 위치이며 서버 seq로 변환한다. risky에는 직접 근거가 하나 이상 필요하다. 0·음수·bool·문자열·범위 밖 번호와 원래 seq를 모르는 줄은 거부한다.

단순 맞장구의 고정 목록은 코드에서도 직접 근거에서 제거하되 전체 대화에는 유지한다. 제거 후 risky의 직접 근거가 비면 재시도한다. 프롬프트는 인용·남의 사례·부정 표현을 실제 요구와 구분하도록 한다. 보조 맥락은 직접 근거와 분리하고 중복을 제거한다. 이 필터와 번호 검증만으로 모든 의미상 정확성을 보장하지 않으며 실제 품질 평가는 후속이다.

- 보정: F1·F2·F3·F5의 absolute_line과 도구 flagged는 risky로 반영한다.
- 도구: F1 계좌, F3 URL·앱·전화번호의 고정 목록 Mock이다. 해당 상태에 허용된 도구와 실제 원문에서 찾은 조회 값만 실행한다. 값·원문 대신 근거 줄 번호를 결과에 남긴다. not_found는 안전 근거가 아니다.
- 한 분석 시도에 모델 호출은 도구 왕복 포함 최대 2회다. 검증된 flagged 근거가 있으면 마무리 모델의 timeout·인증·파싱·근거 오류에도 위험과 해당 근거를 유지한다.
- call_context는 성공한 결과의 비어 있지 않은 값으로 갱신한다.

## 재시도와 진행 상태

[recovery.py](../../scamshield/recovery.py)가 각 실패 작업을 최초 1회 + 추가 3회(최대 4회) 실행한다. 대기 간격은 0.5·1·2초다. timeout·연결·429·5xx·출력/근거 오류는 재시도한다. 인증·요청 거부·설정 오류와 알 수 없는 내부 오류는 즉시 최종 실패다. 성공한 다른 상태와 원문 누적은 반복하지 않는다.

진행 콜백은 시작·각 시도에 analyzing을 보내고 요청 종료 시 한 번만 completed/failed를 보낸다. 같은 호출의 콜백은 직렬화한다. 전달 실패는 민감한 예외 없이 기록하고 모델 재시도를 유발하지 않는다. UI는 analyzing을 분석 중, failed를 분석 실패로 연결해야 하며 기존 위험은 함께 유지한다.

소진된 실패는 state에 남는다. 후속 단순 응답으로 사라지거나 재시도 예산이 초기화되지 않는다. 새 구간의 같은 상태 분석이 전체 문맥을 보고 성공하면 그 상태의 실패를 해소한다. 이전 감지 실패 구간은 이후의 다른 구간 감지 성공만으로 해소하지 않는다. 원래 실패 요청의 수동 복구·결과 채택은 서버에서 원래 입력과 버전을 보존해 다뤄야 한다.

동기 재시도 중 새 발화는 호출 서버가 보관하고 다음 구간으로 처리해야 한다. 재시도 누적으로 기존 BE HTTP 55초 제한을 넘을 수 있으므로 실제 연결 시 HTTP·작업 임대 시간을 함께 조정해야 한다. timeout 12초는 분석 전체의 총 대기 마감이 아니다.

## 점수

| 판단 | F1·F2·F3 | F5 | F4·F6 |
|---|---:|---:|---:|
| risky | 40 | 25 | 10 |
| uncertain | 20 | 10 | 5 |
| within_normal | 0 | 0 | 0 |

상태마다 한 칸이며 risky는 고정이다. uncertain은 1분마다 절반으로 줄고 5 미만이면 0이다. 재판단하면 칸을 바꾸고 감소를 다시 잰다. 실패 시 공개 score의 None 규칙과 내부 성공 판단의 점수 보존을 구분한다.

## 오류

입력 불일치·초기 설정 오류는 기존 PipelineError다. 통화 감지·분석 오류는 정해진 코드만 failures로 반환하고 키·응답 본문·대화·인증 정보·예외 메시지는 노출하지 않는다. 실패 자체로 사기를 확정하거나 정상으로 확인하지 않는다.

## 검증과 후속 범위

현재 회귀 검증과 실제 실행 결과는 [분석 실패 대응 work](../../openspec/changes/analysis-failure-handling/work.md)에 있다. 실제 모델의 근거 선택 정확도·실제 지연·BE 이벤트·프론트 표시·재시도 후 서버 복구는 미검증이다. API 없는 성공을 실제 연결 성공으로 취급하지 않는다.

## 관련 문서

- [기능상 위험의 수정 전 재현](../analysis/runtime-risk-review.md) · [현재 아키텍처](../architecture/overview.md) · [입력 흐름](mvp-flow.md)
- [분석 실패 대응 목적](../../openspec/changes/analysis-failure-handling/proposal.md) · [요구](../../openspec/changes/analysis-failure-handling/spec.md) · [설계](../../openspec/changes/analysis-failure-handling/design.md) · [작업](../../openspec/changes/analysis-failure-handling/tasks.md) · [검증](../../openspec/changes/analysis-failure-handling/work.md)
- [이전 상태별 판단 change](../../openspec/changes/jev-state-agents/design.md) · [Supervisor 계약](supervisor-and-chat.md) · [Supervisor change](../../openspec/changes/jev-supervisor-url/design.md)
