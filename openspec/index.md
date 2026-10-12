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

## GitHub 협업 설정 — 완료

이슈 폼·기본 PR 양식과 공유 스킬을 추가한다. 외부 이슈/PR 생성이나 push 없이 기능별 로컬 커밋으로 기록한다.

- [proposal](changes/github-collaboration/proposal.md): 목적·범위.
- [spec](changes/github-collaboration/spec.md): 양식·권한·검증 요구.
- [design](changes/github-collaboration/design.md): 참고 원칙과 저장소 적용.
- [tasks](changes/github-collaboration/tasks.md): 완료 범위.
- [work](changes/github-collaboration/work.md): 실제 검증과 남은 사항.
