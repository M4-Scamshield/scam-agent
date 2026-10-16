---
name: scamshield-github-templates
description: Maintain ScamShield GitHub issue forms and the pull request template, or draft an individual PR using the repository template. For drafting or publishing individual issues, use scamshield-create-issue.
---

# GitHub Collaboration Templates

Use this skill when a repository needs GitHub issue templates, a PR template, or both. It also supports drafting individual PRs using the repository template. Route individual issue drafting and publication to [scamshield-create-issue](../scamshield-create-issue/SKILL.md), which owns the consistent issue-writing workflow.

## First inspect the repository

Read existing `.github/` files, contribution guidance, development instructions, and the build or test commands. Preserve established labels, issue types, approval rules, and documentation workflows. Do not configure a label unless it already exists or the user asks to create it.

Choose only the templates that fit the repository. A small project commonly needs a bug report and a change proposal; do not add a broad template catalog without a concrete use.

## Issue templates

Prefer GitHub YAML Issue Forms in `.github/ISSUE_TEMPLATE/` when structured input improves triage. Each form needs `name`, `description`, and `body`.

For a bug form, collect observed behavior, expected behavior, reproducible steps, environment, and optional diagnostic evidence. Include a duplicate-issue check and a reminder not to submit secrets or customer data.

For a feature or change form, collect the problem or goal, desired outcome, scope and compatibility constraints, observable acceptance criteria, and a change-specification link when the repository uses one.

Make only triage-critical information mandatory. Keep free-form issues enabled unless the user wants submissions restricted to forms.

## One PR template for people and AI

Create one default `.github/PULL_REQUEST_TEMPLATE.md`. It must work for human authors and AI-authored changes in the same body.

Put the human-oriented summary first: a plain-language description of what changed, why, and its user or operational effect; related issue and change-specification links; and a short review starting point with important files, reading order, and behavior to inspect.

Follow it with evidence-oriented sections: a requirement-to-change-to-evidence table; a verification table with exact command or check, outcome, and reason when unrun; and documentation, configuration, database, security, compatibility, and remaining-risk notes.

Add a short comment at the top explaining the two reading modes. Authors must not claim unverified tests, unimplemented behavior, or inferred causes as facts.

Use multiple PR templates only if the user explicitly needs different PR workflows. Do not split the AI and human views into separate templates by default.

## Repository-specific checks

Reflect the repository's real process in the templates: architecture documentation updates, change-specification status, test commands, and sensitive-data rules. Do not copy a generic checklist that asks for artifacts the project does not use.

Validate that YAML forms are structurally valid, referenced paths exist, and Markdown tables have matching column counts. Review the final templates as a contributor would: the first screen should explain the change, while the evidence should make reviewable claims traceable.


## ScamShield integration and drafts

Read [AGENTS.md](../../../AGENTS.md) and relevant [OpenSpec records](../../../openspec/index.md) for actual scope and completion. Use the [bug form](../../../.github/ISSUE_TEMPLATE/bug_report.yml), [change form](../../../.github/ISSUE_TEMPLATE/change_proposal.yml), or [PR template](../../../.github/PULL_REQUEST_TEMPLATE.md) as appropriate. Write in Korean unless requested otherwise. Keep MVP design, implemented behavior, Fake/Mock results, and real external verification distinct. For documentation-only work, report the documentation check without claiming service tests.

Lead individual issue/PR drafts with the concrete problem and resulting behavior. Scale the body to the change and omit irrelevant sections. Link existing issues/change records; use Closes only for an issue the PR actually completes.

Templates or drafts do not authorize publishing, pushing, or merging. Follow the user's requested actions and existing session authorization without adding duplicate approvals. When publication is requested, verify repository/base/head and matching existing items first. Use exact multiline text via a temporary file and gh --body-file. Report the returned URL; do not blindly repeat creation when the outcome is uncertain.

Apply [documentation synchronization](../scamshield-docs-sync/SKILL.md) when guidance or work records change. Share the same skill through the repository's .claude/skills symlink.
