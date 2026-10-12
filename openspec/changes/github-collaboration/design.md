# 템플릿 적용 설계

aTopsMigrator의 .codex/skills/github-collaboration-templates/SKILL.md를 읽어 두 Issue Forms와 단일 PR 양식의 원칙을 참고했다. ScamShield의 Fake/Mock 구분·OpenSpec 기록·문서 검사를 반영한다.

원본은 .agents/skills/scamshield-github-templates에 두고 .claude/skills에서 상대 심볼릭 링크로 공유한다. 생성 스크립트나 GitHub 자동화를 추가하지 않는다. 입력 폼·본문은 .github에 둔다.

제목은 사용자가 선택한 feat/fix 등의 변경 종류를 앞에 적는다. 버그 폼은 `fix: `, 기능·설계 변경 폼은 `feat: `를 기본값으로 제공하며 다른 종류이면 작성자가 수정한다. PR 제목은 본문 템플릿이 자동 설정하지 않으므로 상단 주석과 README로 같은 기준을 안내한다. GitHub label은 추가하지 않는다.

[Harness](../../../docs/harness/index.md), [공유 지침](../../../CLAUDE.md), [요구](spec.md)와 [검증 기록](work.md)을 따른다.
