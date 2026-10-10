---
name: scamshield-work-cycle
description: Start or resume ScamShield design, implementation, or fix work using its document indexes, relevant decisions, verification, and handoff records. Use for substantive repository work; simple read-only questions do not need a new work record.
---

# ScamShield Work Cycle

Use this repository's shared work path so a later session can continue from documents and evidence rather than conversation memory.

## Start or resume

1. Read the document entrypoint in [AGENTS.md](../../../AGENTS.md) and [docs/index.md](../../../docs/index.md), then the canonical before/during/after procedure in [workflow.md](../../../docs/harness/workflow.md). The workflow also covers resumption and record sizing.
2. Choose the reading order for the request. For new work, read relevant architecture and design documents before looking for a related change in [openspec/index.md](../../../openspec/index.md); then read its proposal/spec/design and tasks/work to understand scope and existing progress. For resumption, locate the existing change and read tasks/work first for completed scope, evidence, unresolved items, and next action; then read proposal/spec/design and the linked architecture and designs before continuing.
3. Follow only relevant topic indexes and direct document links for decisions and investigation evidence. If the needed design does not exist yet, use the confirmed directions and unresolved choices in the project context. In either reading order, check actual files alongside the governing documents. Design approval and implementation completion are separate facts.
4. Continue the existing change when its scope still matches. For a new substantive change, use the [templates](../../../docs/harness/templates.md) to create proposal.md, spec.md, design.md, tasks.md, and work.md under openspec/changes, and register all documents in openspec/index.md. Do not create a change for every minor edit.

## Do the authorized work

Use the [project context](../../../docs/project-context.md) for confirmed scope and unresolved choices. A new recommendation that changes a confirmed design stays a proposal until the user adopts it. Existing user authorization is sufficient for work already within scope.

Perform relevant available verification, and record observed outcomes and unrun checks accurately. Do not invent build or test commands before an executable project exists.

## Finish or hand off

When facts, documents, contracts, behavior, or work status changed, apply [scamshield-docs-sync](../scamshield-docs-sync/SKILL.md) to the affected documentation and indexes. Follow its synchronization steps even if the skill is not visible in the selector.

Keep the change's tasks, work, and openspec/index consistent: completed scope, evidence, remaining questions, and concrete next action. Report the outcome and material limits concisely. Do not turn planning-only work into an implementation claim.
