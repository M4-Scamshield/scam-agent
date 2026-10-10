# ScamShield

한국어 통화의 보이스피싱 위험을 탐지하고, 통화 상태에 따라 사용자 대응과 외부 검증을 수행하는 졸업프로젝트다. 목적과 합의된 MVP 범위는 [프로젝트 컨텍스트](docs/project-context.md)에 있다.

현재 저장소에는 에이전트 작업 환경과 문서 관리 도구만 있다. 서비스 코드, 상세 설계, 외부 API 연결과 실행 데모는 아직 없다.

## 작업 시작

[AGENTS.md](AGENTS.md) → [docs/index.md](docs/index.md) → [공통 작업 흐름](docs/harness/workflow.md) 순서로 시작한다. 필요한 주제 문서와 진행 중인 작업은 각 인덱스에서 찾는다.

변경별 요구·설계·작업 진행·검증은 [OpenSpec 인덱스](openspec/index.md)에서 관련 change를 찾아 확인한다.

저장소 스킬은 `.agents/skills/`에 있다. 작업 흐름에는 `$scamshield-work-cycle`, 관련 문서의 갱신에는 `$scamshield-docs-sync`를 사용할 수 있다. 스킬이 목록에 나타나지 않는 환경에서는 [AGENTS.md의 스킬 링크](AGENTS.md)로 파일을 직접 읽고 같은 절차를 적용한다.

## 문서 검사

Python 3.9 이상에서 추가 패키지 없이 실행한다.

```sh
python3 .agents/skills/scamshield-docs-sync/scripts/check_docs.py
```

검사 대상은 docs·openspec·안내 문서·스킬의 로컬 링크, 문서 인덱스 누락, 하위 인덱스의 상위 연결과 change의 다섯 필수 파일이다. 외부 URL, 제목 앵커, 문서 내용과 코드의 의미상 일치는 자동 검사하지 않는다. 내용 정합성은 [문서 동기화 스킬](.agents/skills/scamshield-docs-sync/SKILL.md)로 확인한다.

서비스 실행·빌드·테스트 명령은 실제 실행 환경을 구성할 때 추가한다.
