# Claude Code 작업 진입점

공통 작업 기준은 [AGENTS.md](AGENTS.md)에 있다. 아래 import로 구현 전·중·후 안내를 불러오고, 같은 문서와 OpenSpec 기록을 사용한다.

@AGENTS.md

## 공유 스킬 사용

`.claude/skills/`의 각 스킬은 `.agents/skills/`의 원본 폴더로 연결되어 있다.

| 작업 | Claude Code 명령 | 원본 지침 |
|---|---|---|
| 설계·구현·수정 작업 시작 또는 재개 | `/scamshield-work-cycle` | [작업 스킬](.agents/skills/scamshield-work-cycle/SKILL.md) |
| 이슈/PR 템플릿 유지·PR 초안 작성 | `/scamshield-github-templates` | [협업 스킬](.agents/skills/scamshield-github-templates/SKILL.md) |
| 일정한 형식의 이슈 작성·요청받은 등록 | `/scamshield-create-issue` | [이슈 생성 스킬](.agents/skills/scamshield-create-issue/SKILL.md) |
| 문서·계약·동작·진행 변경 후 동기화 | `/scamshield-docs-sync` | [문서 동기화 스킬](.agents/skills/scamshield-docs-sync/SKILL.md) |

스킬이 목록에 나타나지 않으면 위 원본 지침을 직접 읽고 적용한다. 스킬 내용과 스크립트는 `.agents/skills/`에서 관리한다. 문서 검사 명령은 저장소 루트에서 실행한다.
