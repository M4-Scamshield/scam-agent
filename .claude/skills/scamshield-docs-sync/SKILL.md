---
name: scamshield-docs-sync
description: Synchronize ScamShield source-of-truth documents, topic indexes, and work handoff records after documentation, contract, behavior, or task-status changes; also use for an explicit documentation consistency audit.
---

# ScamShield Docs Sync (Claude Code)

이 스킬의 권위 있는 지침과 검사 스크립트는 `.agents/skills/scamshield-docs-sync/`에서 관리한다. 저장소의 단일 출처 원칙에 따라 여기서는 본문을 복제하지 않고 원본을 그대로 적용한다.

## 적용 방법

1. [.agents/skills/scamshield-docs-sync/SKILL.md](../../../.agents/skills/scamshield-docs-sync/SKILL.md)를 읽고 변경 식별 → 문서 갱신 → 검증/보고 절차를 따른다.
2. 저장소 루트에서 문서 검사를 실행한다:

   ```sh
   python3 .agents/skills/scamshield-docs-sync/scripts/check_docs.py
   ```

3. 네비게이션 오류를 수정해 다시 실행하고, 내용 정합성은 변경 사실과 본문을 직접 대조해 확인한다.

요약: 문서·계약·동작·진행 상태가 바뀐 뒤 기준 문서·인덱스·작업 기록의 링크와 내용을 맞춘다.
