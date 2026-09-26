# AGENTS.md

Project-specific guidance for coding agents working in `PersonalWorthTracker`.

## Current State

- This repository contains an implemented MVP Python CLI for local-first monthly tracker workbook updates.
- Product requirements, architecture notes, data contracts, and domain language live under `.agent/System/`.
- The current workflow is CSV-first Nordea statement processing with PDF fallback, dry-run review artifacts, reviewed-decision import, Category Memory learning on commit, and commit-to-copy workbook updates.
- Real financial inputs, generated outputs, local category memory, and local agent tooling must stay out of Git.

## Repository Discovery

Before implementing changes:

- Read this file.
- Read `.agent/README.md`.
- Read `.agent/Tasks/context.md`.
- Inspect project configuration files if they exist.
- Use `rg` or `rg --files` for codebase navigation.

## Project Structure

```text
PersonalWorthTracker/
├── AGENTS.md
├── README.md
├── .agent/
│   ├── README.md
│   ├── Tasks/
│   │   └── context.md
│   ├── issues/
│   │   ├── kanban.md
│   │   └── YYYY-MM-DD-issue-NNN-short-title.md
│   ├── System/
│   └── issues/
├── docs/
├── src/
├── tests/
├── scripts/
└── config/
```

## Local Issue Tracking

Use `.agent/issues/` as the local issue tracker when work is not tracked in an external issue tracker. This is the canonical place for `to-issues` output and agent-ready kanban tracking.

Expected layout:

```text
.agent/issues/
├── kanban.md
├── YYYY-MM-DD-prd-short-title.md
└── YYYY-MM-DD-issue-NNN-short-title.md
```

`kanban.md` should track `Ready For Agent`, `Blocked`, `In Progress`, and `Done`.

Issue files should use frontmatter with `type: issue`, `id`, `title`, `status`, `slice_type`, `labels`, `parent`, `blocked_by`, and `created`. Use `slice_type: AFK` for independently implementable tracer-bullet slices and `slice_type: HITL` when human input is required.

When using `to-issues`, publish approved slices in dependency order, keep `.agent/issues/kanban.md` updated in the same change, and use issue body sections `Parent`, `What To Build`, `Acceptance Criteria`, and `Blocked By`.

## Implementation Guidance

- Keep changes scoped and reversible.
- Prefer project conventions once they exist.
- Do not add dependencies, frameworks, services, telemetry, or generated assets without a clear requirement.
- Treat `.agents/` and `skills-lock.json` as local-only agent tooling unless the owner explicitly decides otherwise.
- Preserve user work and avoid unrelated edits.
- Update `.agent/Tasks/context.md` after significant decisions, implementation, or validation.

## Testing and Validation

- Add or update tests when changing behavior.
- Run the most relevant available checks before handoff.
- If no checks exist yet, state that clearly in the final handoff.

## Documentation

- Keep durable decisions in `.agent/Tasks/context.md` or the relevant `.agent/System/` document.
- Keep user-facing setup and usage notes in `README.md`.
- Avoid temporary process notes in user-facing documentation.

## Agent skills

### Issue tracker

GitHub Issues in `EricleungDK/personalwealthtracker` via `gh`; `.agent/issues/` is historical only. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five labels (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: glossary at `.agent/System/domain_language.md`, ADRs under `docs/adr/`. See `docs/agents/domain.md`.
