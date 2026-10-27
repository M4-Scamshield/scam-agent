# 2AS 진행과 검증 기록

## 범위와 작업 트리

2026-10-23 `feat/jev-gemini-two-agent`를 만들고 구조 변경을 시작했다. 사용자가 중단 후 2026-10-27 재개를 요청했다. 시작 시 AGENTS·workflow·project-context·design/index·openspec/index 및 Verify/스트리밍 설계의 기존 미커밋 변경이 있었다. 이를 보존하며 새 작업을 분리했다. 커밋·push·PR은 이번 요청에 포함하지 않는다.

## 구현

[State](../../../scamshield/state.py)·[Graph](../../../scamshield/graph.py)·[인터페이스](../../../scamshield/interfaces.py)를 2AS로 전환하고 [Jev HTTP](../../../scamshield/jev.py)·[Gemini 구조화 분석](../../../scamshield/gemini.py)·[CLI](../../../scamshield/cli.py)를 연결했다. 옛 `roles.py`, `tools.py`는 삭제했다. 현재 계약은 [설계](../../../docs/design/state-and-graph.md)를 따른다.

## 확인한 근거

- 2026-10-27 `.venv/Scripts/python.exe -m pytest -q`: **50 passed**. Python 3.14의 Google SDK deprecated 타입과 sandbox의 pytest cache 쓰기 제한 경고 2건. 동작 검사는 통과했다.
- `.venv/Scripts/python.exe -m scamshield --offline --auto`: No → Yes → Yes, Yes 경로의 분석 저장을 확인했다. 이는 명시적인 대역이며 실제 API 결과가 아니다.
- 실제 CLI No 예제: “오늘 저녁에 같이 밥 먹을까요?” → Jev `No`, P(Yes)=0.0, analysis=None. callId `46cc911d-6006-4ea7-af76-8a64d1b5ac52`, exit 0. `.env`는 uv의 `--env-file`로 전달했고 키는 출력하지 않았다.

## 실제 Yes와 Gemini 호출

실제 실행 명령은 다음 형태로 로컬 `.env`를 명시했다. 예제는 인명·실제 계좌가 없는 합성 통화다.

```powershell
.venv/Scripts/python.exe -m uv run --cache-dir .venv/uv-cache --locked --no-sync --python .venv/Scripts/python.exe --env-file .env python -X utf8 -m scamshield --text "서울중앙지검입니다. 고객님 계좌가 범죄에 연루되었습니다. 수사를 위해 지금 안전계좌로 전액 송금하세요. 다른 사람에게는 알리지 마세요."
```

- 첫 실행 callId `2a0f1bd8-f3b2-4514-8c39-f52dfa53e3d7`: Jev **Yes, P(Yes)=1.0** 이후 Gemini **HTTP 504 DEADLINE_EXCEEDED**, exit 1.
- 같은 예제를 수동으로 한 번 더 실행한 callId `8461396d-d383-4a40-bd34-7ccfb3d4114c`: Jev **Yes, P(Yes)=1.0** 이후 Gemini **HTTP 503 UNAVAILABLE**, exit 1.

두 실행 모두 자동 재시도는 없고 오류를 정상 결과/No로 바꾸지 않았다. 실제 Gemini 요청까지 연결됐지만 reason/response의 실제 생성 성공은 확인하지 못했다. API 없는 SDK 전송 대역 검사와 실제 성공을 혼동하지 않는다. 모델·프롬프트·키를 임의로 바꾸거나 추가 호출을 반복하지 않았다.

## 문서·그래프·환경 확인

- [README](../../../README.md), [계약](../../../docs/design/state-and-graph.md), [흐름](../../../docs/design/mvp-flow.md), [아키텍처](../../../docs/architecture/overview.md)·인덱스를 새 구조에 맞췄다. 과거 first-demo는 역사 기록으로 표시하고 제거 코드 링크를 당시 커밋으로 연결했다. 기존 Verify/스트리밍 초안은 보존하며 현 구조 미적용을 표시했다.
- `.venv/Scripts/python.exe -X utf8 -m scamshield.export_graph`: **PASS**. 컴파일된 Graph에서 [PNG](../../../docs/architecture/scamshield-langgraph.png)·[Mermaid](../../../docs/architecture/scamshield-langgraph.mmd)를 생성했다. PNG를 직접 열어 update_context → detect_with_jev, Yes → respond_with_llm → END, No → END를 확인했다. API 키·통화 데이터는 그래프 생성에 사용하지 않았다.
- `.venv/Scripts/python.exe .agents/skills/scamshield-docs-sync/scripts/check_docs.py`: **PASS**, 문서 36개·로컬 링크 422개. 내용도 현재 코드와 대조했다.
- `git diff --check`: **PASS**. LF/CRLF 전환 안내는 있었지만 공백 오류는 없었다.
- `.venv/Scripts/python.exe -m uv lock --check --offline --python .venv/Scripts/python.exe --cache-dir .venv/uv-cache`: **PASS**, 55 packages. pyproject/uv.lock에 의존성을 추가하지 않았다.
- `git check-ignore .env .venv .pytest_cache`: **PASS**. 키 값과 로컬 환경은 추적 대상에 넣지 않았다.

초기 환경에 uv/테스트 의존성이 없어 저장소 `.venv`를 만들고 잠긴 패키지를 설치했다. Python 별칭·uv 기본 캐시·패키지 다운로드·API/그래프 네트워크의 접근 제한이 있었고 필요한 명령은 권한 허용 후 실행했다. lock 검사는 설치된 로컬 Python을 명시해 성공했다.

## 남은 사항과 다음 행동

이번 인터페이스 범위는 구현·API 없는 검사·Jev 실연결·구조도·문서 동기화까지 완료했다. Gemini 실생성 성공은 외부 API 응답이 복구된 뒤 위 명령으로 별도 확인한다. STT 서비스·화자·partial·서버 연결, 탐지 성능/확률 보정/안내 품질 평가, 조회 도구·영구 기록은 구현하거나 검증하지 않았다.

2026-10-27 후속 사용자 요청으로 이번 2AS 변경을 커밋·push 대상으로 분리했다. 기존 Verify/스트리밍 초안과 작업 지침 수정은 로컬에 보존한다. 공유 문서에서는 이번 구조 변경 부분만 stage하고 기존 초안 링크는 그 초안이 게시될 때까지 로컬에만 남긴다. 커밋과 원격 전송 결과는 Git 이력에서 확인한다.

게시 대상도 별도로 검증했다. `git checkout-index --all --prefix=.venv/commit-review-2as/`로 index의 파일만 추출하고 해당 스냅샷의 check_docs.py를 실행한 결과 **PASS: 문서 29개·로컬 링크 367개**다. 기존 초안이 없는 원격 브랜치에서도 문서 링크가 성립함을 확인했다. 코드·테스트는 직전 50개 검사 통과 이후 변경하지 않았다. `git diff --cached --check`도 통과했다.
