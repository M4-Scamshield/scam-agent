# ScamShield

한국어 통화의 보이스피싱 위험을 탐지하고, 통화 상태에 따라 사용자 대응과 외부 검증을 수행하는 졸업프로젝트다. 목적과 합의된 MVP 범위는 [프로젝트 컨텍스트](docs/project-context.md)에 있다.

현재 저장소에는 에이전트 작업 환경과 문서 관리 도구만 있다. 서비스 코드, 상세 설계, 외부 API 연결과 실행 데모는 아직 없다.

## 작업 시작

[AGENTS.md](AGENTS.md) → [docs/index.md](docs/index.md) → [공통 작업 흐름](docs/harness/workflow.md) 순서로 시작한다. 필요한 주제 문서와 진행 중인 작업은 각 인덱스에서 찾는다.

변경별 요구·설계·작업 진행·검증은 [OpenSpec 인덱스](openspec/index.md)에서 관련 change를 찾아 확인한다.

Codex와 Claude Code는 같은 AGENTS·문서·스킬 원본을 사용한다.

| 도구 | 작업 안내 | 스킬 진입점 | 직접 호출 |
|---|---|---|---|
| Codex | [AGENTS.md](AGENTS.md) | `.agents/skills/` | `$scamshield-work-cycle`, `$scamshield-docs-sync`, `$scamshield-github-templates` |
| Claude Code | [CLAUDE.md](CLAUDE.md)에서 AGENTS를 import | `.claude/skills/`의 원본 폴더 링크 | `/scamshield-work-cycle`, `/scamshield-docs-sync`, `/scamshield-github-templates` |

Claude Code의 작업 안내는 `CLAUDE.md`의 `@AGENTS.md` import로 연결하고, 세 스킬은 `.agents/skills/`의 원본을 가리키는 상대 심볼릭 링크로 등록했다. 사용 방식의 근거는 [공식 import 안내](https://code.claude.com/docs/en/memory#share-one-file-with-other-coding-tools)와 [공식 스킬 안내](https://code.claude.com/docs/en/skills#where-skills-live)에 있다. Claude Code 세션에서 `/context`로 작업 안내의 로드를 확인하고 `/` 메뉴에서 스킬을 확인할 수 있다. 스킬이 목록에 나타나지 않으면 AGENTS 또는 CLAUDE의 링크로 원본 지침을 직접 읽고 적용한다.

## 문서 검사

Python 3.9 이상에서 추가 패키지 없이 실행한다.

```sh
python3 .agents/skills/scamshield-docs-sync/scripts/check_docs.py
```

검사 대상은 docs·openspec·안내 문서·스킬의 로컬 링크, 문서 인덱스 누락, 하위 인덱스의 상위 연결과 change의 다섯 필수 파일이다. CLAUDE.md가 있으면 그 안의 Markdown 링크도 검사한다. 외부 URL, 제목 앵커, Claude의 import 처리·스킬 자동 인식, 문서 내용과 코드의 의미상 일치는 자동 검사하지 않는다. 내용 정합성은 [문서 동기화 스킬](.agents/skills/scamshield-docs-sync/SKILL.md)로 확인한다.

서비스 실행·빌드·테스트 명령은 실제 실행 환경을 구성할 때 추가한다.


## 이슈·PR 작성

[버그 폼](.github/ISSUE_TEMPLATE/bug_report.yml)·[변경 제안 폼](.github/ISSUE_TEMPLATE/change_proposal.yml)과 [PR 양식](.github/PULL_REQUEST_TEMPLATE.md)을 사용한다. [협업 스킬](.agents/skills/scamshield-github-templates/SKILL.md)은 템플릿 유지와 요청받은 초안 작성을 지원한다. 변경 결과·관련 스펙·실제 검증 근거를 연결하며, 양식 추가만으로 실제 이슈/PR을 게시하지 않는다.
