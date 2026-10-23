# ScamShield

한국어 통화의 보이스피싱 위험을 탐지하고, 통화 상태에 따라 사용자 대응과 외부 검증을 수행하는 졸업프로젝트다. 목적과 합의된 MVP 범위는 [프로젝트 컨텍스트](docs/project-context.md)에 있다.

현재 [CLI 통화 데모](scamshield/cli.py)를 구현했다. LangGraph·InMemorySaver가 통화별 대화와 조회 결과를 유지하고 Fake Jev·Mock 사건번호 조회로 검증 후 경고 흐름을 보여준다. Suspect 안내와 Verify Tool Calling은 같은 Gemini 모델을 역할별로 한 번씩 호출한다. API 없는 검사와 실제 Gemini 세 발화 데모를 완료했다. 상세 기준은 [MVP 전체 스펙](docs/design/state-and-graph.md), 실행 근거와 후속 사항은 [작업 기록](openspec/changes/first-demo/work.md)에 있다.

## 작업 시작

[AGENTS.md](AGENTS.md) → [docs/index.md](docs/index.md) → [공통 작업 흐름](docs/harness/workflow.md) 순서로 시작한다. 필요한 주제 문서와 진행 중인 작업은 각 인덱스에서 찾는다.

변경별 요구·설계·작업 진행·검증은 [OpenSpec 인덱스](openspec/index.md)에서 관련 change를 찾아 확인한다.

Codex와 Claude Code는 같은 AGENTS·문서·스킬 원본을 사용한다.

| 도구 | 작업 안내 | 스킬 진입점 | 직접 호출 |
|---|---|---|---|
| Codex | [AGENTS.md](AGENTS.md) | `.agents/skills/` | `$scamshield-work-cycle`, `$scamshield-docs-sync`, `$scamshield-github-templates`, `$scamshield-create-issue` |
| Claude Code | [CLAUDE.md](CLAUDE.md)에서 AGENTS를 import | `.claude/skills/`의 원본 폴더 링크 | `/scamshield-work-cycle`, `/scamshield-docs-sync`, `/scamshield-github-templates`, `/scamshield-create-issue` |

Claude Code의 작업 안내는 `CLAUDE.md`의 `@AGENTS.md` import로 연결하고, 스킬은 `.agents/skills/`의 원본을 공유한다. 기존 스킬의 상대 심볼릭 링크와 새 스킬의 연결 상태는 작업 기록에서 구분한다. 사용 방식의 근거는 [공식 import 안내](https://code.claude.com/docs/en/memory#share-one-file-with-other-coding-tools)와 [공식 스킬 안내](https://code.claude.com/docs/en/skills#where-skills-live)에 있다. Claude Code 세션에서 `/context`로 작업 안내의 로드를 확인하고 `/` 메뉴에서 스킬을 확인할 수 있다. 스킬이 목록에 나타나지 않으면 AGENTS 또는 CLAUDE의 링크로 원본 지침을 직접 읽고 적용한다.

## Python 개발 환경

Python 3.12와 uv를 사용한다. 의존성은 pyproject.toml과 uv.lock으로 관리하고 .python-version은 기본 Python 버전을 지정한다.

```sh
uv sync --locked
uv lock --check --offline
```

.venv, IDE 개인 설정(.idea), 실행 캐시와 .env는 Git에서 제외한다.

## CLI 데모 실행

API 없이 전체 흐름부터 확인하려면 다음 명령을 사용한다. `--offline`은 Agent 대역을 쓰며 Gemini 호출 검증에 해당하지 않는다.

```sh
uv run --locked python -m scamshield --offline --auto
```

실제 Gemini 실행은 실행할 셸에 `GEMINI_API_KEY` 환경변수를 설정한 뒤 진행한다. 키를 코드·문서·채팅에 적지 않는다. `.env`를 자동으로 읽지 않으며 키가 없으면 오류로 종료한다. 기본 모델은 `gemini-3.8-flash`이고 `GEMINI_MODEL` 환경변수로 변경할 수 있다. 계정의 모델 접근·한도는 실제 호출로 확인해야 한다.

로컬 파일로 설정하려면 [.env.example](.env.example)을 `.env`로 복사하고 키를 채운 뒤 uv에 파일을 명시한다. `.env`는 Git에서 제외되어 있다. 기본 캐시 경로의 권한 오류가 나면 아래처럼 임시 캐시 경로를 사용한다.

```sh
uv --cache-dir /private/tmp/scamshield-uv-cache run --locked --env-file .env python -m scamshield --auto
```

Gemini 호출 실패 시 HTTP 코드·상태와 API 오류 요약을 출력한다. 키와 요청 전체는 출력하지 않는다. 출력은 실패 원인을 확인하기 위한 것이며 실제 인증 성공을 뜻하지 않는다.

```sh
uv run --locked python -m scamshield
```

각 입력에서 Enter를 누르면 준비된 발화를 사용한다. 직접 입력하려면 `--auto`를 빼고 실행한다. `.env` 파일을 사용하는 직접 입력 명령은 다음과 같다.

```sh
uv --cache-dir /private/tmp/scamshield-uv-cache run --locked --env-file .env python -m scamshield
```

CLI는 세 번 입력한 뒤 종료한다. 이 제한은 데모 CLI의 시나리오에만 있으며 CallDemo/Graph의 통화별 입력 횟수 제한은 아니다. 세 발화 자동 실행은 다음 명령을 사용한다.

```sh
uv run --locked python -m scamshield --auto
```

| 준비된 발화 | 기대 실행 |
|---|---|
| 안녕하세요. 서울중앙지검입니다. | OBSERVE 0.1 |
| 고객님 계좌가 범죄에 연루되었습니다. | SUSPECT 0.5 → 확인 행동 안내 |
| 사건번호는 2026-12345입니다. | VERIFY 0.7 → Tool 선택 → 독립 Mock 실행 → 재판단 WARN 0.9 → 고정 경고 |

## Jev API 키 설정

2026-10-23 [TypeSafe 공식 Quick start](https://docs.typesafe.ai/introduction/quickstart)와 [SDK 환경변수](https://docs.typesafe.ai/sdk/python/api/constants)를 확인했다. [TypeSafe 콘솔의 API Keys](https://console.typesafe.ai/keys)에서 로그인 후 키를 발급하고, Git에서 제외된 로컬 `.env`의 `TYPESAFE_API_KEY=` 오른쪽에 키만 입력한다. `Bearer ` 접두사는 넣지 않는다. 기존 `.env`의 Gemini 설정은 유지한다.

```dotenv
TYPESAFE_API_KEY=
TYPESAFE_BASE_URL=https://api.typesafe.ai
TYPESAFE_DEFAULT_MODEL=jev-latest
```

위 이름은 공식 SDK가 읽는 환경변수다. 실제 HTTP 호출은 `POST https://api.typesafe.ai/v1/systemone`에 `Authorization: Bearer <키>`를 전달한다([공식 API 문서](https://docs.typesafe.ai/api/system-one)). `.env`를 실행 환경에 전달하려면 기존과 같이 `uv run --locked --env-file .env ...`를 사용한다. 키는 채팅·소스·문서에 적지 않는다.

이번 설정은 키 등록 준비이며 SDK 설치·실제 Jev 호출·인증 검증은 포함하지 않는다. 현재 CLI는 계속 Fake Jev를 사용하므로 환경변수만 채워도 실제 Jev로 전환되지는 않는다.

## 현재 데모의 역할과 한계

| 부분 | 현재 구현 |
|---|---|
| 상대방 발화 | [DEMO_UTTERANCES](scamshield/state.py)의 하드코딩된 세 문장 또는 직접 입력. 상대방 AI·실제 통화·STT는 없음 |
| 위험 판단 | [Fake Jev](scamshield/jev.py)의 데모 문구/조회 결과 기반 규칙 |
| 확인 행동 안내 | 실제 Gemini가 대화와 State를 읽어 생성 |
| 조회 요청 선택 | 실제 Gemini Tool Calling으로 대화의 사건번호와 case_lookup을 선택 |
| 조회 실행 | [Mock case_lookup](scamshield/tools.py). `2026-00001`만 FOUND, 나머지는 NOT_FOUND |
| 최종 경고 | Fake Jev가 WARN을 판단하면 고정 문구 출력 |

현재 Fake Jev의 VERIFY 진입은 정해진 의심 맥락과 `2026-12345`에 맞춰져 있다. `2026-00001`을 입력하는 것만으로는 조회 단계에 진입하지 않는다. 사건번호 일부를 선택한 요청은 실행 전에 거부한다. 자유로운 통화 내용에 대한 실제 탐지 성능을 확인하는 데모는 아니다.

실제 통화 연결에서는 상대방과 사용자 양쪽 발화를 STT로 받고 화자를 구분해 같은 통화에 누적해야 한다. 현재 transcript는 화자 정보 없는 문자열 목록이며 STT 입력 계약과 Agent 실행 런타임 전환은 [후속 범위](docs/design/state-and-graph.md#남은-준비와-후속-범위)다.

Node 순서·phase/risk·Tool 요청/결과·안내와 대화/조회 누적 개수를 출력한다. 새 실행마다 고유 callId를 생성하고 같은 시나리오에서는 같은 thread를 사용한다. InMemorySaver의 상태는 프로세스 생존 동안 유지하며 프로세스를 종료하면 사라진다. 실행 오류가 나면 시나리오를 중단하고 명령을 다시 실행해 새 통화로 시작한다. 자동 재시도·Agent 실행 런타임·실제 탐지/기관 조회·STT/프론트·운영 복구/동시 처리는 구현 범위에 포함하지 않는다.

## 코드 검증

```sh
uv run --locked pytest -q
```

모든 테스트는 API 없이 실행한다. 핵심 Graph 시나리오·통화별 상태 유지/분리·Tool 선택/실행 분리·결과 반영·turn당 Tool 최대 1회와 결과 후 재판단 1회를 확인한다. Gemini 응답 대역과 실제 SDK의 전송 대역 검사는 실제 모델 호출 검증과 구분한다.

최신 코드 검증은 API 없는 31개 검사다. 실제 Gemini 성공 기록은 사건번호 부분 문자열 수정 이전 실행이며, 해당 수정 후에는 API 없는 회귀 검사와 CLI를 확인했다. 실행 시점별 근거는 [work](openspec/changes/first-demo/work.md)에 구분해 남겼다.

## 문서 검사

Python 3.9 이상에서 추가 패키지 없이 실행한다.

```sh
python3 .agents/skills/scamshield-docs-sync/scripts/check_docs.py
```

검사 대상은 docs·openspec·안내 문서·스킬의 로컬 링크, 문서 인덱스 누락, 하위 인덱스의 상위 연결과 change의 다섯 필수 파일이다. CLAUDE.md가 있으면 그 안의 Markdown 링크도 검사한다. 외부 URL, 제목 앵커, Claude의 import 처리·스킬 자동 인식, 문서 내용과 코드의 의미상 일치는 자동 검사하지 않는다. 내용 정합성은 [문서 동기화 스킬](.agents/skills/scamshield-docs-sync/SKILL.md)로 확인한다.

## 이슈·PR 작성

[버그 폼](.github/ISSUE_TEMPLATE/bug_report.yml)·[변경 제안 폼](.github/ISSUE_TEMPLATE/change_proposal.yml)과 [PR 양식](.github/PULL_REQUEST_TEMPLATE.md)을 사용한다. [협업 스킬](.agents/skills/scamshield-github-templates/SKILL.md)은 템플릿 유지와 PR 초안 작성을, [이슈 생성 스킬](.agents/skills/scamshield-create-issue/SKILL.md)은 작업 메모의 이슈 작성·요청받은 GitHub 등록을 지원한다.

기능 이슈는 `문제와 목표 → 변경 범위와 제약 → 완료 조건 → 관련 스펙과 작업 기록`의 같은 네 구역으로 작성한다. 예: `$scamshield-create-issue로 Verify Agent 이슈 초안 작성해줘`. 실제 등록을 원하면 `이슈 등록해줘`라고 요청한다. [Verify Agent 예시](.agents/skills/scamshield-create-issue/references/verify-agent.md)에 검사·사건번호·전화번호 조회와 시스템 프롬프트 작업을 정리했다.

이슈·PR 제목은 `type: 변경 내용` 형식을 사용한다. 기능은 `feat:`, 버그 수정은 `fix:`, 문서는 `docs:`, 환경/관리 작업은 `chore:`, 동작을 유지한 구조 변경은 `refactor:`로 쓴다. Issue Forms의 기본 제목은 기능 `feat:`, 버그 `fix:`이며 내용에 맞게 바꿀 수 있다. 데모처럼 구현 범위를 설명하는 내용은 본문에 적는다.
