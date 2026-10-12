# 협업 설정 진행과 검증

2026-10-12: aTopsMigrator의 GitHub 협업 템플릿 스킬을 참고해 ScamShield 전용 폼·PR 양식·공유 스킬을 작성했다. 원본은 Downloads/aTopsMigrator/.codex/skills/github-collaboration-templates/SKILL.md다. 서비스 설계·Python 설정·IDE 변경과 구분해 기능별 커밋으로 남긴다.

이슈/PR 생성·push·서비스 테스트는 실행하지 않는다. GitHub UI 동작은 로컬 구조 검사로 확인한 것으로 주장하지 않는다.

검증: skill-creator quick_validate.py 통과(.venv Python 사용), Issue Forms YAML 구조·자유 이슈 설정·UI metadata·Claude symlink·PR 표 열 수 확인 PASS. 작업 트리 문서 검사 PASS(문서 23개·로컬 링크 219개), git diff --check 통과. 커밋할 파일만 추출한 상태의 문서 검사 PASS(문서 16개·로컬 링크 128개), 스킬 검사 통과, 서비스 스펙/Python/IDE 제외 검사도 통과했다. 서비스 스펙·Python/IDE 설정은 staging에서 제외하며 로컬 커밋 후 실제 파일 목록으로 범위를 확인한다. GitHub 게시·push는 실행하지 않는다. 관련 [설계](design.md)·[작업](tasks.md)와 [공통 안내](../../../docs/harness/index.md)를 따른다.
