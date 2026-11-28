# 실시간 통화 분석의 기능상 위험 검토

조사 시점: 2026-11-28. 대상: `main`의 `ef21f02`에서 분기한 `fix/analysis-failure-handling`의 통화·Supervisor 코드.

상태: 코드 검토와 API 없는 재현을 완료했다. 실제 장애 발생률이나 실제 모델의 탐지 정확도를 측정한 결과는 아니다. 후속 사용자 방향은 [통화 계약](../design/state-and-graph.md)에 구현 전 방향으로 기록했다. 이 문서의 나머지 개선안은 제안이며 현재 실행 동작을 바꾸지 않는다. 첫 개선 작업은 [분석 실패 대응 change](../../openspec/changes/analysis-failure-handling/proposal.md)에서 이어간다.

## 검토 목적과 방법

시간·메모리 복잡도보다, 위험 판단·대화 기억·라우팅·조회 근거가 의도한 보호 기능을 방해하는지 확인했다.

- 기준: [통화 계약](../design/state-and-graph.md), [Supervisor 계약](../design/supervisor-and-chat.md), 두 기존 change의 [통화 요구](../../openspec/changes/jev-state-agents/spec.md)와 [Supervisor 요구](../../openspec/changes/jev-supervisor-url/spec.md).
- 실제 코드와 테스트를 대조했다. 대역 감지기로 Yes/No를 지정하고 대역 분석기로 결과·예외를 주입했다. 이는 오류 경로가 가능한지 확인하는 방법이며 모델이 해당 입력에서 실제로 그 응답을 낸다는 증거는 아니다.
- 기존 핵심 테스트 117개가 통과했다. 정책대로 동작하는 테스트의 통과와 보호 기능의 충분성은 별도로 평가했다.
- API 키를 읽거나 실제 모델·사이트를 호출하지 않았다. 코드·기존 작업 파일을 수정하지 않고 재현했다. 이번 후속 작업은 문서 추가다.

## 핵심 위험 요약

| ID | 문제 | 사용자에게 생길 수 있는 영향 | 확인 성격 | 권장 순서 |
|---|---|---|---|---|
| R1 | 상태별 분석 실패를 건너뛰고 정상으로 계산 | 판단하지 못한 요구를 안전하다고 받아들임 | 대역 재현, 현재 실패 정책의 한계 | 첫 개선 |
| R2 | F3·F5만 감지되면 분석 보류 | 원격제어 앱 설치 등 강한 요구도 정상으로 표시 | 대역 재현, 확정 정책 재논의 필요 | 후속 |
| R3 | history와 state의 일치 검증 없음 | 맥락 없는 판단·존재하지 않는 대사 참조 | 대역 재현, 저장 계약 보완 필요 | 후속 |
| R4 | risky 상태는 이후 분석에서 제외 | 새 계좌·새 요구에 대한 조회와 안내가 오래된 채 남음 | 대역 재현, 확정 정책 재논의 필요 | 후속 |
| R5 | 새 행동 감지에만 재평가를 의존 | 나중에 밝혀진 맥락으로 이전 불확실한 판단을 재검토하지 못함 | 제어 흐름 확인, 실제 미탐률 미측정 | 후속 |
| R6 | URL 혼합 채팅의 call 누락 허용 | 송금 요구를 분석하지 않고 처리 완료 | 대역 라우팅 응답으로 재현, 계약과 구현의 차이 | 우선 수정 후보 |
| R7 | 조회 후 모델 실패로 위험 근거 유실·조회 값 출처 미검증 | 확보한 위험을 놓치거나 잘못 추출한 값으로 위험 판정 | 두 경우 모두 대역 재현 | 근거 보존은 R1과 연결 |
| R8 | uncertain이 시간만으로 소멸 | 미해결 요구가 새로운 정상 근거 없이 정상으로 바뀜 | 코드·기존 테스트 확인, 확정 정책 재논의 필요 | 후속 |

## R1 — 분석 실패가 정상으로 보이는 경로

[통화 그래프](../../scamshield/agents/call_agent.py)의 `judge_states`는 비치명적 분석 예외를 로그에 남기고 해당 상태를 건너뛴다. `finalize`는 성공한 판단에 risky나 점수가 남은 uncertain이 없으면 정상으로 계산한다. 이전 판단이 없는 첫 요청에서 F1만 Yes이고 분석이 실패하면 `status=정상`, `score=0`, `state_analyses=[]`가 된다.

실패 상태와 근거는 재시도 대기 항목으로 저장하지 않는다. 다음 요청에서 F1이 No이면 분석을 다시 부르지 않는다. 서버가 성공 응답을 저장하면 이 실패는 요청 전체의 재시도 대상도 되지 않는다. 기존 위험 판단이 있으면 그 판단은 남으므로 모든 실패가 정상으로 바뀌는 것은 아니다.

### 실패 원인은 타임아웃만이 아니다

| 원인 | 현재 코드 | 현재 처리 | 실측 여부 |
|---|---|---|---|
| 응답 대기·연결 단계의 timeout | `AnalystError(TIMEOUT)` | 해당 상태 생략 | 예외 주입으로 확인, 실제 빈도 미측정 |
| 연결 실패 | `CONNECTION_FAILED` | 해당 상태 생략 | 예외 처리 코드·기존 테스트 확인 |
| 서버 오류·요청 한도 초과 | `HTTP_500`, `HTTP_429` 등 | 해당 상태 생략 | 예외 처리 코드·기존 테스트 확인 |
| JSON 해석 실패·필수 필드 누락 | `INVALID_OUTPUT` | 해당 상태 생략 | 대역 응답·기존 테스트 확인 |
| 인증·권한 오류, 잘못된 모델·요청 | `AUTH_FAILED`, `REQUEST_REJECTED` | `PipelineError`로 요청 전체 실패 | 정상으로 반환하는 위 경로와 다름 |
| Jev 실패·잘못된 출력 | `jev/CALL_FAILED`, `jev/INVALID_OUTPUT` | 요청 전체 실패 | Haiku 상태별 생략과 다름 |

근거: [공통 Claude 전송](../../scamshield/llm.py), [응답 파싱](../../scamshield/agents/analysis_agent.py), [오류 테스트](../../tests/test_haiku.py), [그래프 실패 테스트](../../tests/test_graph.py).

### 타임아웃이 발생할 수 있는 이유

현재 [HaikuClient](../../scamshield/llm.py)는 Anthropic SDK에 `timeout=12.0`, `max_retries=0`을 설정한다. 도구 왕복 시 모델을 최대 두 번 부르며, 이 값이 통화 분석 전체의 12초 마감을 뜻하지는 않는다. Jev에는 별도로 [10초 timeout](../../scamshield/agents/jev_agent.py)이 있다.

타임아웃은 클라이언트가 설정한 대기 한도 안에 네트워크 작업을 끝내지 못한 경우다. 네트워크 지연, 제공자 측 처리 지연, 입력·출력 처리량 등이 원인 후보지만 이번에 원인을 실측하지 않았다. 전체 대화를 매 상태 분석에 보내고 상태별 요청을 동시에 실행하므로, 대화 길이·활성 상태 수와 지연·오류의 관계도 관측할 대상이다. 429는 요청 한도 오류이며 timeout과 구분해야 한다.

따라서 12초가 짧아서 실제 장애가 발생했다고 단정하거나 timeout만 늘려 해결됐다고 판단하지 않는다. 우선 요청 단계·오류 코드·시도 횟수·소요 시간과 입력 크기를 원문 없이 기록하고 원인을 구분해야 한다. API 키·인증 헤더·대화 원문은 진단 로그에 넣지 않는다.

### 최소 재현

저장소 루트에서 아래 Python을 실행한다. 기존 테스트의 대역을 재사용하며 API는 호출하지 않는다. Windows에서는 `.venv/Scripts/python.exe -X utf8`를 사용할 수 있다.

```python
import runpy

from scamshield.llm import AnalystError

helpers = runpy.run_path("tests/test_graph.py")
analyst = helpers["FakeAnalyst"](F1=AnalystError("TIMEOUT"))
call = helpers["Call"](helpers["FakeDetector"]({"F1"}, set()), analyst)
first = call.say("[p1] Transfer money.", now=0)
second = call.say("[p2] OK.", now=1)
print(first.status, first.score, first.state_analyses)
print(second.status, len(analyst.requests))
# 정상 0 []
# 정상 1  (후속 요청에서 재시도하지 않음)
```

### 첫 개선에서 논의할 조치

- 위험 판단과 분석 완료 여부를 구분한다. 실패 때문에 정상으로 확인됐다는 인상을 주지 않으며, 실패 자체만으로 사기를 확정하지도 않는다.
- 이전 위험 판단과 도구가 이미 확보한 위험 근거는 후속 모델 실패에도 유지한다.
- 실패한 상태·근거·오류 코드·시도 기록을 보관하고, 같은 행동이 재등장하지 않아도 재평가할 수 있게 한다.
- timeout·연결·429·5xx, 출력 형식 오류, 인증·요청 설정 오류의 복구 방법을 구분한다. 모든 오류의 무조건 재시도는 피한다.
- 후속 사용자 방향: 재시도 중 화면은 `분석 중`, 최대 3회 재시도 후에도 실패하면 `분석 실패`다. 횟수의 해석과 미정인 실행 주체·간격·총 대기·출력 계약은 [후속 설계](../../openspec/changes/analysis-failure-handling/design.md)에 기록한다. 현재 코드는 아직 재시도하지 않는다.
- 별도 안내 후보: 감지한 요구에 맞춰 “송금 요구를 확인 중입니다. 확인될 때까지 송금을 잠시 보류해 주세요.” 같은 임시 안내를 검토한다. 사용자에게 채택된 정확한 문구나 현재 UI 구현이 아니다.

## 전체 대화 분석과 근거 발화 선택

사용자는 후속 대화에서 전체 기존 대화를 바탕으로 분석하고, 새 발화 전체를 근거로 기록하지 말고 필터링해야 한다고 명시했다. 현재 코드의 동작은 다음 세 범위로 나뉜다.

| 범위 | 현재 동작 | 한계 |
|---|---|---|
| 후보 감지 | Jev가 이전 4줄과 새 줄에서 F1~F6 행동의 존재를 판단 | 전체 대화 재검토가 아니며 개별 근거 번호를 반환하지 않음 |
| 최종 판단 | 선택된 상태의 Haiku가 전체 대화·이전 판단·통화 맥락을 읽음 | 후보에서 누락된 상태는 호출되지 않을 수 있음 |
| 최종 근거 기록 | risky가 된 상태의 요청에 포함된 새 줄 seq 전체를 기록 | 실제 문제가 된 발화만 선택한 목록이 아님 |

대역 Jev가 F1 Yes, 대역 Haiku가 risky를 반환하도록 하고 아래 세 발화를 한 묶음으로 전달했다.

| seq | 발화 예시 | 개선 시 구분할 역할 |
|---|---|---|
| 101 | “검찰 수사관입니다.” | 송금 요구를 해석하는 보조 맥락 후보 |
| 102 | “네.” | 전체 대화에는 유지하되 자동으로 송금 요구 근거로 삼지 않음 |
| 103 | “이 계좌로 돈을 보내세요.” | 직접 요구 근거 후보 |

실행은 영어 동등 문장의 `NewLine(seq=101..103)`으로 했다. 관찰 결과는 `evidence_seqs=[101,102,103]`, Haiku 요청의 `detected_lines=[1,2,3]`이었다. 모델이 근거를 고른 결과가 아니라 그래프가 묶음 전체를 기록한 것이다. 원래 seq와 대화상 줄 위치도 서로 다르다.

개선 방향은 전체 대화를 분석 입력으로 유지하고 최종 판단에 사용한 직접 요구·보조 맥락 발화만 별도로 선택하는 것이다. 원문에 존재하는 번호인지 검증하고, 그 발화가 실제로 이유를 뒷받침하는지·화자·인용·부정 표현을 확인해야 한다. 단순 응답을 분석 입력에서 전부 삭제하거나 새 줄 전체를 최종 근거로 자동 복사하는 것은 피한다.

재시도할 때는 아직 최종 근거가 없을 수 있다. 따라서 최종 근거 선택과 재시도 입력 범위를 동일시하지 않는다. 실패 작업의 후보·기존 전체 대화·입력 버전을 보관하는 설계와, 이전 발화 seq를 보존하는 입력 계약이 필요하다. 상세 제안과 미정 사항은 [후속 설계](../../openspec/changes/analysis-failure-handling/design.md)에 있다.

## 나머지 위험의 관찰과 개선 제안

### R2 — 보류가 강한 위험의 확인까지 막음

대역 Jev가 F3만 Yes로 반환하고 대역 Haiku는 risky를 반환하도록 준비했다. 결과는 정상 0점, Haiku 호출 0회, `held.F3` 저장이었다. F3 절대선인 원격제어 앱 설치 여부를 분석할 기회가 없다. 근거: [route](../../scamshield/agents/call_agent.py), [절대선](../../scamshield/agents/analysis_agent.py), `test_f3_f5_are_held_until_a_core_state_turns_on`.

강한 행동의 즉시 분석 예외와 보류 표시를 제안한다. F3·F5 보류는 기존 채택 정책이므로 이 문서로 자동 변경하지 않는다.

### R3 — 대화 원문과 판단 상태의 복구가 분리됨

이전 대화 8줄 뒤의 F3을 보류하면 `detected_lines=[9]`가 저장된다. 다음 요청에서 history를 빈 목록으로 보내고 그 state와 F6 새 줄을 전달해도 입력이 받아들여진다. F3 분석 요청은 실제 대화 1줄에 대해 9번 대사를 참조했다. 근거: [입력 검증과 감지 대사 전달](../../scamshield/agents/call_agent.py), [AgentMemory](../../scamshield/state.py).

원문은 history로 전달되고 state에는 포함되지 않는다. 통화 ID·처리 순번·이력 버전 검증과 원문·state의 원자적 저장을 제안한다. 실제 BE의 저장·복구 경로가 안전한지는 별도 통합 검증이 필요하다.

### R4 — 경고 유지와 분석 갱신을 함께 막음

F1을 두 요청 연속 Yes로 반환했다. 첫 판단을 risky로 만든 뒤 두 번째 요청에서 계좌 A를 B로 바꿔도 분석 호출은 총 1회였고 첫 이유·근거 seq가 유지됐다. 근거: [risky 제외 조건](../../scamshield/agents/call_agent.py), `test_recall_rules_risky_never_uncertain_and_normal_again`.

위험 경고를 유지하면서도 새 계좌·앱·URL·요구 내용은 다시 조회하고 안내를 갱신하는 분리를 제안한다. risky 고정 자체의 폐지를 결정한 것은 아니다.

### R5 — 맥락 변화만으로 이전 판단을 재검토하지 않음

첫 요청에 F1 uncertain을 저장하고 다음 요청에 F6만 Yes로 반환하면 F6만 새로 분석하고 F1은 그대로 둔다. 감지기는 이전 4줄과 새 줄을 보며 Haiku의 전체 대화 검토는 선택된 상태에 한정된다. 근거: [detect_states와 route](../../scamshield/agents/call_agent.py).

목적·신분·대상 변화에 따른 관련 판단 재검토를 제안한다. F6 분석이 전체 맥락을 보고 위험을 잡을 수도 있으므로 이 관찰만으로 통화 전체의 실제 미탐을 확정하지 않는다.

### R6 — URL과 요구가 섞인 채팅의 분석 누락

`Send money now. https://example.com/` 메시지에 대역 Supervisor가 call=No, url=Yes를 반환하도록 했다. 첫 요청은 `routes=[url]`, `appended_lines=[]`, `call_done=true`였고 같은 ID 재전송은 `routes=[]`였다. URL이 있는 메시지는 `plain_chat`에 잡히지 않는다. 근거: [supervise·finalize](../../scamshield/agents/supervisor.py).

URL 안전 확인만 요청한 채팅과 송금·정보 요구가 섞인 채팅을 구분하고, 필요한 call 경로가 빠지면 완료 처리하지 않는 검증을 제안한다. 필요한 경로 누락을 오류로 올린다는 기존 Supervisor 계약과 차이가 있다.

### R7 — 위험 도구 결과의 유실과 조회 값 출처

`tests/test_haiku.py`의 대역으로 다음 두 경우를 확인했다.

1. 첫 응답에서 `check_account(11122233334444)`를 실행해 flagged를 얻은 뒤, 두 번째 응답에 `AnalystError(TIMEOUT)`을 주입했다. risky 결과 대신 예외가 전파됐다. 현재 flagged 보존은 두 번째 응답의 파싱 실패만 감싼다.
2. 계좌번호가 없는 대화에 대해 모델의 tool_use에 위 번호를 넣었다. 원문 포함 여부 검증 없이 flagged 조회 결과를 받아들였다. 모델이 실제로 이 환각을 일으켰다는 측정은 아니다.

근거: [HaikuAnalyst.judge](../../scamshield/agents/analysis_agent.py), [도구 실행](../../scamshield/tools.py). 도구 결과 보존은 R1 개선과 함께 다룰 후보이며, 추출 값의 원문 대조와 상태별 허용 도구 검증은 별도 후속으로 둔다. [URL 전용 agent](../../scamshield/agents/url_agent.py)는 요청 주소와 도구를 검증하므로 통화 agent와 구분한다.

### R8 — 시간 경과와 의심 해소가 같은 결과가 됨

F1 uncertain 20점은 180초 뒤 0점이 된다. 다른 risky·점수가 남은 uncertain이 없으면 정상이다. 새 요청에서만 계산하므로 무발화 중 자동 갱신하는 타이머도 없다. 근거: [state_points·finalize](../../scamshield/agents/call_agent.py), `test_uncertain_decays_by_half_each_minute_and_risky_stays`.

미해결 요구와 마지막 분석 시각을 따로 표현하고 시간 감쇠의 의미를 재논의할 것을 제안한다. 현재 채택된 점수 정책을 이번 문서 작업에서 대체하지 않는다.

## 통합 경계와 확인 한계

- URL 전용 agent의 위험 결과는 통화 점수와 별도로 반환된다. URL 위험이 화면 경고까지 이어지는지는 서버·UI 정책과 연결 검증이 필요하다.
- 인접한 로컬 `BE_ScamShield`의 `dev` 체크아웃은 과거 `run_turn` API와 제거된 모듈을 참조했다. `server.py`를 `runpy.run_path`로 읽고 offline builder만 호출했을 때 `ModuleNotFoundError: scamshield.interfaces`를 확인했다. 실행 중인 서버나 배포 환경을 검사한 결과는 아니며, 다른 브랜치의 구현 유무도 단정하지 않는다. 저장소 밖 파일은 이 문서의 로컬 링크 대상으로 만들지 않는다.
- 기존 검사는 `.venv/Scripts/python.exe -m pytest -q tests/test_graph.py tests/test_haiku.py tests/test_supervisor.py tests/test_jev.py tests/test_url_agent.py`로 117 passed였다. 대역 재현은 기존 테스트 이외의 일회성 Python 실행이며, 새 회귀 테스트를 추가한 것으로 기록하지 않는다.
- 실제 timeout 발생 빈도·제공자 지연·대화 길이별 지연·운영 재시도·장시간 통화·실제 STT의 정정·재전송은 미측정이다.

## 관련 문서

- [현재 아키텍처](../architecture/overview.md) · [통화 계약](../design/state-and-graph.md) · [Supervisor 계약](../design/supervisor-and-chat.md)
- [분석 실패 대응 목적](../../openspec/changes/analysis-failure-handling/proposal.md) · [요구 초안](../../openspec/changes/analysis-failure-handling/spec.md) · [설계 초안](../../openspec/changes/analysis-failure-handling/design.md) · [작업](../../openspec/changes/analysis-failure-handling/tasks.md) · [검증·인계](../../openspec/changes/analysis-failure-handling/work.md)
