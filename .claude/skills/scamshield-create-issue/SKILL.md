---
name: scamshield-create-issue
description: ScamShield의 작업 메모를 일정한 한국어 GitHub 이슈로 작성하거나 등록한다. 이슈 초안 작성, 이슈 생성, 이슈 등록, GitHub에 이슈 올려줘, 작업 목록을 이슈로 정리해줘 요청에 사용한다. 이슈 템플릿 자체 수정과 PR 작성은 scamshield-github-templates를 사용한다.
---

# ScamShield 이슈 생성 (Claude Code)

이 스킬의 권위 있는 지침과 예시는 `.agents/skills/scamshield-create-issue/`에서 관리한다. 저장소의 단일 출처 원칙에 따라 여기서는 본문을 복제하지 않고 원본을 그대로 적용한다.

## 적용 방법

1. [.agents/skills/scamshield-create-issue/SKILL.md](../../../.agents/skills/scamshield-create-issue/SKILL.md)를 읽고 제목 형식과 네 구역(문제와 목표 → 변경 범위와 제약 → 완료 조건 → 관련 스펙과 작업 기록) 작성 기준을 따른다.
2. 참고 초안은 [references/verify-agent.md](../../../.agents/skills/scamshield-create-issue/references/verify-agent.md)에 있다.
3. 등록 요청 시 원본의 "실제 GitHub 등록" 절차(대상 저장소 확정, `gh issue create --body-file`, URL 확인)를 따른다.

요약: 작업 메모를 일정한 한국어 GitHub 이슈 초안으로 정리하고, 요청 시 저장소에 등록한다.
