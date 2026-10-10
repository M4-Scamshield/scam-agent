# 저장소 작업 안내

## 이 파일의 목적과 적용 방법

이 파일은 에이전트가 작업 단계마다 무엇을 확인하고, 수행하고, 남겨야 하는지 안내한다. 설계·구현·수정 작업은 아래의 **구현 전 → 구현 중 → 구현 후** 순서로 진행한다. 기존 작업을 재개할 때는 먼저 완료 범위를 확인하고 남은 작업에 적용한다.

요청과 관련된 문서만 읽고, 작업에 해당하는 검증과 기록을 수행한다. 단순 질문·조회에는 변경·검증·새 change 작성을 요구하지 않는다. 설계·문서 작업도 같은 단계를 따르되 코드 구현과 서비스 테스트는 해당할 때만 수행한다. 세부 절차와 기록 크기의 기준은 [공통 작업 흐름](docs/harness/workflow.md)에 있다.

## 구현 전 — 기준과 작업 범위를 확인한다

[scamshield-work-cycle](.agents/skills/scamshield-work-cycle/SKILL.md)을 적용하고, [docs/index.md](docs/index.md)에서 요청에 필요한 문서 진입점을 찾는다. 이어서 새 작업인지 기존 작업의 재개인지에 따라 읽는다.

- **새 작업:** 관련 [아키텍처](docs/architecture/index.md)와 [상세 설계](docs/design/index.md)를 먼저 읽어 시스템 구성·현재 구현 범위·구조·계약을 이해한다. 그다음 [OpenSpec 인덱스](openspec/index.md)에서 관련 change를 찾아 proposal·spec·design의 요구와 방법, tasks·work의 진행과 검증 근거를 확인한다.
- **작업 재개:** OpenSpec 인덱스에서 해당 change를 찾아 tasks·work의 완료 범위·남은 문제·다음 행동을 먼저 확인한다. 이어서 proposal·spec·design과 연결된 아키텍처·설계를 읽어 변경 범위와 기준을 확인한다.

선택의 이유가 필요하면 [설계 결정](docs/decisions/index.md), 조사·실험 근거가 필요하면 [분석](docs/analysis/index.md)을 읽는다. 관련 설계가 아직 없으면 [프로젝트 컨텍스트](docs/project-context.md)의 확정 방향과 미정 사항을 출발점으로 삼는다.

실제 코드·설정을 확인해 문서와 현재 상태를 비교한다. 설계에 적혀 있다는 이유로 구현 완료라고 판단하지 않는다. 변경을 시작하기 전에 이번 작업의 범위·영향·완료 조건을 정한다.

## 구현 중 — 범위 안에서 변경하고 진행을 남긴다

기존 구조를 활용해 요청과 MVP 범위에 필요한 변경을 수행한다. 확정 설계와 충돌하는 큰 변경이 필요하면 문제·대안·trade-off를 제안으로 남기고, 사용자 채택 전에 기존 설계를 대체하지 않는다.

기존 change의 후속 작업이면 해당 기록을 이어간다. 여러 단계에 걸치거나 계약·구조·동작이 바뀌는 새 작업은 openspec/changes에 change를 만들고 openspec/index.md에 등록한다. 작은 수정마다 새 change를 만들지는 않는다. 관련 change가 있으면 진행·문제·다음 행동을 tasks·work에 남긴다.

설계나 계약이 달라지면 [문서 관리](docs/harness/document-conventions.md)에 따라 해당 기준 문서와 change의 요구·방법을 함께 맞춘다. 공통 설계는 docs에, 이번 변경의 요구·적용 방법·진행은 change에 작성하고 직접 연결한다. 양식이 필요하면 [Harness 인덱스](docs/harness/index.md)에서 찾는다.

## 구현 후 — 검증하고 문서를 맞춘 뒤 인계한다

[README](README.md)와 공통 작업 흐름의 명령을 확인하고 변경에 맞는 테스트·빌드·문서 검사를 실행한다. 실패가 발견되면 작업 범위 안에서 수정하고 관련 검증을 다시 수행한다. 실제 실행 결과와 실행하지 못한 항목·이유를 구분해 남긴다.

[scamshield-docs-sync](.agents/skills/scamshield-docs-sync/SKILL.md)를 적용해 변경된 기준 문서·관련 인덱스·본문과 change의 링크를 맞춘다. 스킬의 문서 검사를 실행하고 본문도 실제 변경과 일치하는지 확인한다.

관련 change의 tasks·work와 openspec/index.md에 실제 완료 범위·검증 근거·남은 사항·다음 행동을 반영한다. 검증하지 않은 기능을 완료로 표시하지 않는다. 사용자에게 변경 결과와 주요 검증·남은 사항을 보고하고, 다음 에이전트가 기록을 읽어 이어갈 수 있는 상태로 마무리한다.
