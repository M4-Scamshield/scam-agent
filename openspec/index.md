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

## 벡터 유사도 위험 점수와 Jev VERIFY 판단 — 진행 중

보이스피싱범 데이터셋의 pgvector 유사도와 누적 점수로 risk·OBSERVE/SUSPECT를 정하고, SUSPECT 이상에서 Jev가 VERIFY 맥락을 판단한다. 점수와 VERIFY 판단은 port/adapter로 교체할 수 있게 한다. 구현 이슈: [#3](https://github.com/M4-Scamshield/scam-agent/issues/3). 현재 스펙 작성 단계이며 구현 전이다. 설계 기준은 [risk-scoring](../docs/design/risk-scoring.md)이다.

| 변경 문서 | 포함한 내용 |
|---|---|
| [proposal](changes/vector-risk-scoring/proposal.md) | 문제·목표·범위·완료 조건 |
| [spec](changes/vector-risk-scoring/spec.md) | 점수·VERIFY 판단·Graph 분리 요구와 검증 조건 |
| [design](changes/vector-risk-scoring/design.md) | 기존 코드에서 바꿀 부분·모듈 배치·trade-off |
| [tasks](changes/vector-risk-scoring/tasks.md) | 스펙·구현 진행 |
| [work](changes/vector-risk-scoring/work.md) | 사용자 방향·제안·검증 기록 |

## 첫 데모 — 완료

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
