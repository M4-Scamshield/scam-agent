---
name: scamshield-docs-sync
description: Synchronize ScamShield source-of-truth documents, topic indexes, and work handoff records after documentation, contract, behavior, or task-status changes; also use for an explicit documentation consistency audit.
---

# ScamShield Docs Sync

Keep the affected documents mutually consistent without copying full contracts or rewriting unrelated pages. This is an agent workflow, not a background watcher. The helper script checks navigation only; it cannot establish semantic agreement with code.

## Establish what changed

Read the [document entrypoint](../../../docs/index.md) and canonical [document conventions](../../../docs/harness/document-conventions.md). Inspect the current request, relevant files, and work record. Use `git diff` and `git status` where useful; a new repository may have no HEAD and only untracked files.

Identify each changed fact: user-approved direction, proposed design, actual implementation, experiment result, verification outcome, or task status. Preserve those distinctions. Do not label a proposal adopted, an unrun check passed, or a mock response real external verification.

## Update affected documents

1. Find the canonical home in the conventions table. Update the detailed fact there once, and use short summaries and relative links elsewhere.
2. Check directly related architecture, design, decisions, analysis, and work records for contradictions. Update those affected by the change; do not rewrite all folders on every task.
3. For an added, renamed, moved, or removed document, update its local index and inbound links. For a new subtopic index, connect it from the parent index. Keep detailed topic listings in local indexes; update docs/index.md when document categories or their entrypoints change.
   Keep direct links between related source documents and change records current: proposal/spec/design link to governing designs, tasks link to work evidence, and source documents link to relevant changes.
4. For the relevant OpenSpec change, keep proposal/spec/design aligned with the scope and actual approach, tasks aligned with completed work, and work aligned with observed evidence, unresolved items, and next action. Update [openspec/index.md](../../../openspec/index.md) when its change status or document registration needs adjustment.

Use the [templates](../../../docs/harness/templates.md) only when a new record serves the current task. If an established design conflicts with code, report the observed gap and resolve which side needs correction within the user's authorized scope; do not silently approve the divergence.

## Verify and report

Run from the repository root:

```sh
python3 .agents/skills/scamshield-docs-sync/scripts/check_docs.py
```

The checker uses only Python's standard library, reads files without modifying them, and returns a nonzero exit status for missing local link targets, index coverage errors, or missing required change documents. It ignores fenced examples, external URLs, and heading anchors. It checks Markdown links and reference-link definitions in AGENTS.md, README.md, docs, openspec, and repository skills; its syntax support is intentionally limited to ordinary Markdown navigation links. OpenSpec change documents are registered directly in openspec/index.md; docs retain their local topic indexes.

Fix reported navigation errors and rerun. Separately read the changed facts and related prose for semantic agreement. Report which documents were synchronized, the check result, and any unresolved factual or design conflict. A passing script alone is not proof of semantic synchronization.
