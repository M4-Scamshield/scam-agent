# OpenSpec 변경 문서 안내

현재 요청과 관련된 변경을 이 문서에서 찾고, `openspec/changes/<change-name>/`의 문서와 실제 파일을 함께 확인한다. 전체 문서 탐색은 [docs/index.md](../docs/index.md), 공통 작업 방법은 [workflow](../docs/harness/workflow.md)를 따른다.

## 변경을 읽고 이어가는 순서

새 작업은 관련 아키텍처·상세 설계로 전체 기준을 확인한 뒤 이 인덱스에서 관련 change를 찾는다. change가 있으면 proposal·spec·design으로 목적·요구·방법을 확인하고, tasks·work로 기존 진행과 검증 근거를 파악한다.

기존 작업을 재개할 때는 해당 change의 tasks·work에서 완료 범위·검증·남은 문제·다음 행동을 먼저 확인한다. 이어서 proposal·spec·design과 연결된 아키텍처·상세 설계를 읽어 범위와 기준을 확인한 뒤 작업을 이어간다. 체크 표시만으로 구현 완료나 테스트 통과를 판단하지 않는다.

| 파일 | 역할 |
|---|---|
| `proposal.md` | 변경의 문제·목표·범위·완료 조건 |
| `spec.md` | 변경이 만족해야 할 요구사항과 검증 가능한 동작 |
| `design.md` | 기존 구조에서 무엇을 어떻게 변경할지, 대안·제약·미정 사항 |
| `tasks.md` | 수행할 작업과 완료 상태. 완료 근거는 work에 연결 |
| `work.md` | 실제 진행·실행한 검증·결과·한계·다음 행동 |

계약·동작·구조가 바뀌거나 여러 단계에 걸치는 작업은 위 다섯 파일로 change를 구성한다. 동일 범위의 후속 요청은 기존 change를 이어간다. 단순 조회나 작은 표현 수정마다 새 change를 만들지는 않는다. 새 change는 이 인덱스에 문서 링크·상태·범위를 등록한다.

공통 설계의 기준은 `docs/design/`, 현재 구현 설명은 `docs/architecture/`에 둔다. change 문서는 해당 변경의 요구와 적용 방법·진행을 담고 상위 문서로 연결한다. 변경이 반영되면 관련 기준 문서를 갱신하고, 본문의 관련 문서 항목에서 해당 change와 검증 기록으로 연결한다.

## Jev 상태 감지·상태별 LLM 대응 — 진행 중(설계 제안)

2026-11-15 사용자 요청으로 시작했다. KorCCVi에서 나온 대화 특징 F1~F6을 Jev가 상태로 감지하고, 켜진 상태별로 LLM이 대화 맥락을 보고 최종 판단과 대응을 한다. 2026-11-16 팀장과 이 구조로 전환하기로 협의했고 작업 이슈 [#13](https://github.com/M4-Scamshield/scam-agent/issues/13)을 등록했다. 상태별 LLM은 Claude API 에이전트로 쓴다. 같은 날 voice_phishing 임시 유지(나중에 제거), Claude 범위, BE 형식 유지, 임시 점수, F1·F3 Mock tool을 정했다. Jev에 상태 질문 7개를 한 요청으로 보내는 소량 실호출(20통화, 실패 0)로 형식을 확인했고, F5·F6 정의를 넓힌 v2와 묶음 오류·경계 정의를 고친 v3까지 같은 20통화로 상태별 미탐·오탐 원인을 확인했다. v3에서 spec 정의 기준 Jev 미탐은 F4 1건이다. 2026-11-17 새 표본(seed 1)에서 F1·F4·F6은 유지됐고, F5는 녹취 핑계로 제3자를 막는 행동을 No 문구가 빼 버려 재현이 3/7로 떨어졌다. 이를 고친 v4에서 F5는 6/7이 됐고 정상 통화 F5 오탐은 0이다. 2026-11-18 F4 평가 정답을 spec에 맞게 좁혀(N6은 돈 요구가 있는 통화만, N5는 혐의 추궁만) 재채점했고, v4 F4 재현은 seed 0 5/6, seed 1 9/10이다. 같은 날 개발용 200통화(사기 120, 정상 80)에서 재현은 F1 64%~F6 98%였고, 정상 통화 50/80에서 상태가 켜졌다. 그중 43통화는 F3·F6만 켜졌다. 대사 단위 확인(2026-11-19)에서 이 F3·F6는 상담원의 번호·사이트·장소 안내와 기관 소개로 켜졌다. 버전별 변경 이유와 결과는 [변경 이력](../docs/analysis/jev-state-question-versions.md)에 있다. 서비스 코드 변경과 평가 하네스는 아직이며 현재 2AS 계약을 대체하지 않는다.

- [proposal](changes/jev-state-agents/proposal.md): 목적·범위·완료 조건.
- [spec](changes/jev-state-agents/spec.md): 상태 정의·라우팅·LLM 계약·절대선.
- [design](changes/jev-state-agents/design.md): 흐름·State 안·대안·미정 사항.
- [tasks](changes/jev-state-agents/tasks.md): 진행과 남은 작업.
- [work](changes/jev-state-agents/work.md): 경위·데이터 근거·다음 행동.

## KorCCVi 사기 수법 분석 — 분석 범위 완료

2026-11-15 사용자 요청으로 KorCCVi 사기 706통화를 화자 표시 대본으로 만들었다. LLM 라벨러가 유형과 R1~R9·NEW 수법을 달았고, 유형별로 집계했다. 서비스 코드는 바꾸지 않았다. 2026-11-16 R·N을 행동 특징 F1~F6으로 다시 묶은 집계를 추가했다. 사람 검수, 정상 통화 비교, R 목록 개정은 후속이다. 결과는 [분석 문서](../docs/analysis/korccvi-scam-tactics.md)에 있다.

- [proposal](changes/korccvi-scam-tactics/proposal.md): 목적·범위·완료 조건.
- [spec](changes/korccvi-scam-tactics/spec.md): 대본·라벨·집계 계약.
- [design](changes/korccvi-scam-tactics/design.md): 데이터 흐름·라벨러 선택.
- [tasks](changes/korccvi-scam-tactics/tasks.md): 완료 범위와 후속.
- [work](changes/korccvi-scam-tactics/work.md): 실행 근거·원문 검사·다음 행동.

## 면접 사칭 통화 합성 데이터 — 완료·새 대본 재평가 완료

2026-11-07 사용자 요청에 따라 지원자와 피싱범의 1대1 면접 사기 통화 100건을 작성했고, 후속 요청으로 비교용 정상 면접 100건과 실제 Plan1 평가를 추가했다. 각각 50~100문장·7,451문장이며 20개 주제·100개 직무와 경력 사례를 사용한다. 200건 실제 Jev 평가에서 TP 100·TN 100·FP 0·FN 0·실패 0을 확인했다. [사기 안내](../datasets/interview_phishing/README.md), [정상·혼합 평가 안내](../datasets/interview_normal/README.md), [분석과 결과](../docs/analysis/interview-phishing-dataset.md)에 형식·합성 문답 공유·평가 한계가 있다. 발표 PPTX·실제 음성·다자 통화·실측 일반화 성능은 미확인이다.

2026-11-14 후속 요청으로 [새 면접 대본 100건](../datasets/interview_holdout/README.md)(사기·정상 각 50건·8~12발화)을 기존 문답 복사 없이 작성하고 같은 Plan1으로 평가했다. TP 50·TN 48·FP 2·FN 0·실패 0, 정확도 98%다. 실행 전 해시를 동결하고 결과 확인 뒤 대본·정답·프롬프트를 조정하지 않았다. [새 평가 분석](../docs/analysis/interview-holdout-eval.md)에 기존 100% 감사·오탐 사례·짧은 대본과 단일 작성자라는 한계가 있다.

- [proposal](changes/interview-phishing-dataset/proposal.md): 요청·범위·완료 조건.
- [spec](changes/interview-phishing-dataset/spec.md): 수량·문장·화자·평가 입력 요구.
- [design](changes/interview-phishing-dataset/design.md): 사례 조합·문답 순서·정답 분리.
- [tasks](changes/interview-phishing-dataset/tasks.md): 실제 완료 범위.
- [work](changes/interview-phishing-dataset/work.md): 생성·검사·한계와 다음 행동.

## Jev·Gemini 2AS — 인터페이스 범위 완료

2026-10-23 사용자 요청으로 기존 phase/조회 구조를 Jev Yes/No·확률 → Yes일 때 Gemini 분석·대응 구조로 전환했다. 2026-10-27 API 없는 테스트 50개·실제 Jev Yes/No 연결·문서 검사·컴파일된 그래프 출력을 확인했다. Gemini 실제 생성은 504/503으로 성공 미확인이며 후속 확인 사항이다. 실제 STT·조회 도구는 이번 범위 밖이다.

- [proposal](changes/jev-gemini-two-agent/proposal.md): 사용자 요청·범위·완료 조건.
- [spec](changes/jev-gemini-two-agent/spec.md): Yes/No·확률·분석 저장·실패 조건.
- [design](changes/jev-gemini-two-agent/design.md): 인터페이스·실제 API·정리 방법.
- [tasks](changes/jev-gemini-two-agent/tasks.md): 실제 완료 범위와 남은 검증.
- [work](changes/jev-gemini-two-agent/work.md): 실행 근거·한계·다음 행동.

## 첫 데모 — 당시 범위 완료·현재 구조로 대체

현재 계약은 [2AS State·Graph](../docs/design/state-and-graph.md)다. 아래 Fake/Mock 설명과 검증 수치는 이전 데모의 기록이다.

구현 이슈: [#1 — 대화 기록을 유지하며 사건번호 확인과 경고까지 실행하기](https://github.com/M4-Scamshield/scam-agent/issues/1).

first-demo의 이번 데모 범위를 완료했다. [MVP 전체 스펙](../docs/design/state-and-graph.md)을 기준으로 CLI·State·LangGraph/InMemorySaver·Fake Jev·독립 Mock 조회·역할별 Gemini 연결을 구현하고 API 없는 시나리오/상태/한도·SDK 변환 검사와 실제 Gemini 안내/사건번호 Tool Calling·최종 WARN을 확인했다. Fake/Mock·전송 대역 검사와 실제 모델 호출 근거는 구분해 남겼다. 복구/동시 요청/Tool timeout·실제 Jev/기관 조회/STT와 후속 Agent 실행 런타임 전환 TODO는 이번 범위에서 제외한다. 사용자 요청에 따라 기능별 커밋을 push하고 [PR #2](https://github.com/M4-Scamshield/scam-agent/pull/2)를 main 대상으로 생성했다. 리뷰·merge는 후속 단계다.

리뷰 P2의 사건번호 일부 선택 통과를 수정했다. 전체 번호 정확히 일치 검사·Tool 미실행 회귀 검사를 포함해 API 없는 테스트 31개와 CLI를 확인했으며, 이번 수정에서는 실제 Gemini를 재호출하지 않았다. 상세 근거는 [work](changes/first-demo/work.md)에 있다.

문서 정합성 감사로 현재 CLI/Fake/Mock의 범위·후속 양쪽 화자 STT·미구현 Tool timeout/오류 분류와 과거 설계 기록의 구분을 보완했다. 데모 완료 상태와 후속 TODO는 유지하며 [현재 구성](../docs/architecture/overview.md)·[스펙](../docs/design/state-and-graph.md)·[tasks/work](changes/first-demo/work.md)에 반영했다.

| 변경 문서 | 포함한 내용 |
|---|---|
| [proposal](changes/first-demo/proposal.md) | 첫 통화 데모의 목표·범위·완료 조건 |
| [spec](changes/first-demo/spec.md) | 상태 누적·두 Agent·검증 후 재판단 요구 |
| [design](changes/first-demo/design.md) | 공통 실행 설계의 데모 적용·후속 상세 스펙·구현 검증 방향 |
| [tasks](changes/first-demo/tasks.md) | 단계별 구현·검증 진행 |
| [work](changes/first-demo/work.md) | 실제 진행·환경·검증·다음 행동 |

## GitHub 협업 설정 — 완료

이슈 폼·기본 PR 양식과 공유 스킬을 추가했고 초기 구성은 외부 게시/push 없이 로컬 커밋으로 기록했다. 후속 사용자 요청으로 feat/fix 등의 제목 형식을 폼·PR/README 안내에 반영하고 기존 이슈 #1·PR #2의 제목을 `feat:`로 맞췄다. 제목 변경과 초기 템플릿 구성의 실행 범위는 [work](changes/github-collaboration/work.md)에서 구분한다.

- [proposal](changes/github-collaboration/proposal.md): 목적·범위.
- [spec](changes/github-collaboration/spec.md): 양식·권한·검증 요구.
- [design](changes/github-collaboration/design.md): 참고 원칙과 저장소 적용.
- [tasks](changes/github-collaboration/tasks.md): 완료 범위.
- [work](changes/github-collaboration/work.md): 실제 검증과 남은 사항.
