# 에이전트 작업 환경

여러 세션과 개발 에이전트가 같은 읽기 경로·작업 방식·문서 갱신 기준을 공유하도록 구성했다. 전체 진입점은 [문서 지도](../index.md)다.

`harness/`는 개발 에이전트가 어떻게 일하고 문서를 관리하는지 설명하는 공통 안내다. 서비스 자체의 설계는 design에, 변경별 요구·설계·진행·검증 기록은 [OpenSpec](../../openspec/index.md)에 둔다. 구현 전·중·후의 기본 절차와 재개 방법은 [공통 작업 흐름](workflow.md)에 모으고, [AGENTS.md](../../AGENTS.md)는 문서 지도와 절차의 진입점으로 둔다.

## 문서 목록

| 문서 | 포함한 내용 |
|---|---|
| [공통 작업 흐름](workflow.md) | 구현 전·중·후 절차와 작업 재개·기록 크기·검증 명령 |
| [문서 관리](document-conventions.md) | 문서별 책임, 기준 문서, 상태 구분, 인덱스와 동기화 범위 |
| [기록 양식](templates.md) | 필요한 경우에만 사용하는 설계·결정·분석·작업 기록 형식 |

## 스킬 연결

- [scamshield-work-cycle](../../.agents/skills/scamshield-work-cycle/SKILL.md): 새 작업은 설계 기준부터, 작업 재개는 진행·인계 기록부터 확인하는 공통 흐름을 적용한다.
- [scamshield-docs-sync](../../.agents/skills/scamshield-docs-sync/SKILL.md): 변경 사실을 기준 문서·작업 기록·인덱스에 반영하고 문서 검사를 실행한다.

스킬은 저장소의 `.agents/skills/`에 두었다. [OpenAI 공식 스킬 문서](https://learn.chatgpt.com/docs/build-skills)의 저장소 스킬 탐색 경로를 따른다. 루트 파일은 [공식 안내](https://learn.chatgpt.com/docs/agent-configuration/agents-md)에서 사용하는 이름인 `AGENTS.md`로 작성했다.

Claude Code는 [CLAUDE.md](../../CLAUDE.md)에서 AGENTS를 import하고, `.claude/skills/`의 상대 심볼릭 링크로 같은 스킬 원본을 사용한다. 호출 명령은 Codex의 `$이름`, Claude Code의 `/이름`이며, 도구별 사용법은 [README](../../README.md)에 있다. Claude 연결은 [공식 import 안내](https://code.claude.com/docs/en/memory#share-one-file-with-other-coding-tools)와 [공식 스킬 안내](https://code.claude.com/docs/en/skills#where-skills-live)를 따른다.

## 참고한 구조와 적용 범위

2026-10-10 로컬 `Downloads/aTopsMigrator`의 AGENTS.md, docs/index.md, 주제별 인덱스, architecture/overview.md, document-map.md, openspec/index.md와 저장소 스킬을 읽었다.

그 저장소의 주제별 읽기 경로, 현재 구현·설계·분석·과거 기록의 구분, 변경과 검증 근거의 연결을 참고했다. 확인한 로컬 스킬은 GitHub 협업 템플릿용이며 문서 동기화 전용 스킬은 없었다. 이 저장소의 두 스킬은 요청에 맞게 새로 작성했다. 참고 저장소를 OpenAI가 작성했다는 출처는 이번 조사에서 확인하지 않았다.

ScamShield의 변경별 문서는 사용자 요청에 따라 참고 저장소처럼 `openspec/changes/`에 구성했다. 공통 작업 방법은 이 harness에 유지한다. 이번에는 문서 형식을 적용했으며 별도 OpenSpec CLI, GitHub 자동화, 개발 에이전트 병렬 실행 설정은 구성하지 않았다. 서비스 내부의 Suspect·Verify Agent와 이 개발용 스킬은 역할이 다르다.


## 2026-10-12 — AI 설정 커밋 정리

AI 문서 구조, 작업 재개/문서 동기화 스킬, Codex·Claude 공유 연결은 기존 기능별 커밋으로 기록되어 있다. 이번 정리는 OpenSpec 공통 인덱스를 버전에 포함하고 분석·아키텍처 인덱스의 존재하지 않는 agent-harness 기록 링크를 제거한다. 서비스 스펙/first-demo 기록·Python 설정·IDE 파일은 이번 AI 설정 커밋 범위와 구분한다. 작업 트리의 문서 검사 PASS(문서 18개·로컬 링크 181개)와 git diff --check 통과를 확인했다. 커밋할 파일만 추출한 상태의 문서 검사도 PASS(문서 11개·로컬 링크 90개)로 확인했다. 서비스 테스트는 설정/문서 변경 범위이므로 실행하지 않는다.
