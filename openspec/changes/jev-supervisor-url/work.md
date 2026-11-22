# 진행과 검증 기록

## 2026-11-23 범위와 진행

브랜치: `feat/jev-supervisor-url-routing` (`main`의 c0c2000에서 생성).

사용자 요청에 따라 STT·채팅의 Jev Supervisor와 Mock URL Tool Calling을 추가하고, 역할별 `agents/*_agent.py`와 `supervisor.py`로 정리한다. 공통 설계는 [Supervisor 계약](../../../docs/design/supervisor-and-chat.md), 변경 적용은 [design](design.md)을 따른다. 기존 BE 진입점 [graph.py](../../../scamshield/graph.py)는 유지한다.

작업 시작 시 `experiments/plan.md` 수정과 데이터·결과·과거 change·`scripts/`·`tests/test_plan1_dataset.py` 등 미추적 파일이 있었다. 이번 변경과 구분해 보존한다.

## 검증 진행

첫 테스트 수집은 기존 가상환경에 anthropic이 없어 실패했다. `.venv/Scripts/python.exe -m uv sync --locked --python .venv/Scripts/python.exe`로 잠금 파일 의존성을 설치했다. 실제 모델·URL 네트워크 조회는 실행하지 않았다.

## 실제 완료와 검증

`agents/`에 `supervisor.py`, `call_agent.py`, `analysis_agent.py`, `url_agent.py`, `jev_agent.py`, `interfaces.py`를 정리했다. 공통 Claude 전송은 `llm.py`로 분리했다. 기존 graph import는 공개 facade로 유지하며, CLI의 `--supervisor`·`--chat`과 그래프 exporter의 `--supervisor`를 추가했다. README·아키텍처·State 계약·입력 흐름·컨텍스트와 이동한 코드의 과거 문서 링크를 맞췄다.

PR 대상 파일만 staging하고 `git checkout-index --all --prefix=<temporary-directory>/`로 복제한 스냅샷에서 전체 검사를 실행했다. 작업 시작 전부터 있던 미추적 실험·데이터·문서·테스트는 스냅샷과 PR에 포함하지 않았다. 실행 인터프리터는 기존 `.venv`의 Python 3.14.3(프로젝트 요구 >=3.12)이다.

| 명령·확인 | 실제 결과 | 한계 |
|---|---|---|
| `python -m pytest -q` (PR 스냅샷) | 124 passed, 48.22초 | API 없는 기존 81개 + 신규 43개 |
| `python -X utf8 .agents/skills/scamshield-docs-sync/scripts/check_docs.py` (PR 스냅샷) | PASS: 문서 54개·로컬 링크 692개 | 본문 의미는 별도 검토 |
| `python -m uv lock --check --offline --python <existing-python>` (PR 스냅샷) | 성공, 잠금 파일과 의존성 일치 | 실제 Provider 연결 검사 아님 |
| `python -X utf8 -m scamshield --offline --text "지금 송금하세요." --chat "https://example.com/"` | call/url 모두 실행, 통화 위험 40·URL unknown·is_mock=true | offline 고정 대역 |
| `python -X utf8 -m scamshield.export_graph --supervisor` | 실제 컴파일 그래프의 Mermaid·PNG 생성, 이미지 육안 확인 | Mermaid.ink에 그래프 구조만 전송, 모델 호출 없음 |
| `git diff --cached --check` | 통과 | Git의 CRLF 알림은 공백 오류가 아님 |

새 검사는 완료 메시지 재전송과 인스턴스 재생성, 일반 채팅, 혼합 STT/URL, URL 캐시, 일부 URL 실패 후 재시도·통화 중복 방지, ID 충돌, 잘못된 라우팅, 모델의 미호출·다른 도구/URL 호출, Mock 미조회와 안전 판정의 구분, 인증 오류를 확인했다.

원래 작업 트리 전체의 문서 검사는 기존 미추적 `synthetic-call-dataset.md`와 두 change의 인덱스 미등록 11건이 남는다. 이번 변경의 잘못된 링크는 수정했으며, 이전 작업 파일을 임의 등록·커밋하지 않고 PR 스냅샷 검사를 통과시켰다.

## 남은 사항과 다음 행동

1. BE가 새 Supervisor API를 호출하도록 연결하고 방 단위 메시지 ID/seq·history·state를 원자적으로 저장한다. 동시 요청은 직렬화 또는 버전 검사한다.
2. 실제 Jev Supervisor와 Haiku URL Tool Calling을 별도 검증한다. URL 검색은 사용자 지시대로 Mock을 유지한다.
3. URL 위험 결과의 BE/UI 표시 정책은 별도 합의한다. 현재는 통화 점수와 합산하지 않는다.
4. 이전 로컬 데이터/실험 작업은 해당 change에서 별도로 이어간다.

[tasks](tasks.md), [spec](spec.md), [통화 계약](../../../docs/design/state-and-graph.md)
