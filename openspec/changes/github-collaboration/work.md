# 협업 설정 진행과 검증

2026-10-12: aTopsMigrator의 GitHub 협업 템플릿 스킬을 참고해 ScamShield 전용 폼·PR 양식·공유 스킬을 작성했다. 원본은 Downloads/aTopsMigrator/.codex/skills/github-collaboration-templates/SKILL.md다. 서비스 설계·Python 설정·IDE 변경과 구분해 기능별 커밋으로 남긴다.

이슈/PR 생성·push·서비스 테스트는 실행하지 않는다. GitHub UI 동작은 로컬 구조 검사로 확인한 것으로 주장하지 않는다.

검증: skill-creator quick_validate.py 통과(.venv Python 사용), Issue Forms YAML 구조·자유 이슈 설정·UI metadata·Claude symlink·PR 표 열 수 확인 PASS. 작업 트리 문서 검사 PASS(문서 23개·로컬 링크 219개), git diff --check 통과. 커밋할 파일만 추출한 상태의 문서 검사 PASS(문서 16개·로컬 링크 128개), 스킬 검사 통과, 서비스 스펙/Python/IDE 제외 검사도 통과했다. 서비스 스펙·Python/IDE 설정은 staging에서 제외하며 로컬 커밋 후 실제 파일 목록으로 범위를 확인한다. GitHub 게시·push는 실행하지 않는다. 관련 [설계](design.md)·[작업](tasks.md)와 [공통 안내](../../../docs/harness/index.md)를 따른다.

## 2026-10-12 — 사용자 요청으로 이슈·PR 제목 형식 통일

사용자가 기존 이슈/PR의 [데모] 접두사 대신 feat/fix 형식을 원했다. 기존 양식에는 [데모] 제목 규칙이 없었으며 당시 작성자가 붙인 표현이었다. `type: 변경 내용`을 기준으로 feat/fix/docs/chore/refactor를 안내하고 범위 설명은 본문에 두도록 [README](../../../README.md)·[PR 양식](../../../.github/PULL_REQUEST_TEMPLATE.md)을 맞췄다. 버그 폼의 기본 제목은 `fix: `, 기능·설계 변경 폼은 `feat: `다. 다른 종류는 작성자가 수정할 수 있다.

사용자 요청에 따라 기존 git 인증으로 REST API를 사용해 [이슈 #1](https://github.com/M4-Scamshield/scam-agent/issues/1)을 `feat: 대화 기록을 유지하며 사건번호 확인과 경고까지 실행하기`, [PR #2](https://github.com/M4-Scamshield/scam-agent/pull/2)를 `feat: 통화별 대화 유지와 사건번호 확인·경고 흐름 구현`으로 수정했다. 반환된 제목/URL 일치를 확인했고 본문·label·상태는 변경하지 않았다. 인증 값을 출력하거나 저장하지 않았다.

검증: `.venv/bin/python`과 PyYAML로 두 Issue Forms의 YAML 구조/기본 제목·자유 이슈 활성 유지 **PASS**. `python3 .agents/skills/scamshield-docs-sync/scripts/check_docs.py` **PASS**, `git diff --check` **PASS**. PR 본문의 기존 표 열 수/섹션을 유지했고 제목 안내 주석만 추가했다. 서비스 코드·테스트·실제 Gemini 호출은 이번 제목/양식 수정에 해당하지 않아 수행하지 않았다. 같은 PR 브랜치에 협업 양식/기록을 별도 커밋으로 반영하며 main에 적용되는 시점은 PR merge 이후다.
