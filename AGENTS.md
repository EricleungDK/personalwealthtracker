# AGENTS.md

Project-specific guidance for coding agents working in `personalwealthtracker` (Python package `personal-wealth-tracker`, CLI `wealth-tracker`).

## Current State

- This repository contains an implemented MVP Python CLI for local-first monthly tracker workbook updates.
- Product requirements, architecture notes, data contracts, and domain language live under `.agent/System/`.
- The main workflow is `wealth-tracker monthly`: newest Nordea CSV → categorization → two-model local Consensus → per-row Trust Policy authority → one Exception Sheet per month → atomic commit to a copied workbook, with Category Memory learned on commit. PDF input and the per-month flags command remain. See `docs/monthly_workflow.md`, `docs/cli_reference.md`, and ADRs in `docs/adr/`.
- Real financial inputs, generated outputs, local category memory, and local agent tooling must stay out of Git.

## Repository Discovery

Before implementing changes:

- Read this file.
- Read `.agent/README.md`.
- Read `.agent/Tasks/context.md` (short state snapshot) and `.agent/System/decisions.md` (current decisions).
- Inspect project configuration files if they exist.
- Use `rg` or `rg --files` for codebase navigation.

## Project Structure

```text
personalwealthtracker/
├── AGENTS.md
├── README.md
├── .agent/
│   ├── README.md
│   ├── Tasks/
│   │   └── context.md
│   ├── System/
│   └── issues/          # historical local issues 001-040, read-only
├── docs/                # operator docs, adr/, agents/, superpowers/specs/
├── src/personal_wealth_tracker/
├── tests/
├── scripts/
└── config/
```

## Issue Tracking

GitHub Issues in `EricleungDK/personalwealthtracker` is canonical (since 2026-09-25); see `docs/agents/issue-tracker.md`. `.agent/issues/` (local issues 001-040 and `kanban.md`) is historical and read-only; do not add new local issues.

## Implementation Guidance

- Keep changes scoped and reversible.
- Prefer project conventions once they exist.
- Do not add dependencies, frameworks, services, telemetry, or generated assets without a clear requirement.
- Treat `.agents/` and `skills-lock.json` as local-only agent tooling unless the owner explicitly decides otherwise.
- Preserve user work and avoid unrelated edits.
- Keep `.agent/Tasks/context.md` a short snapshot; add durable decisions to `.agent/System/decisions.md`. No activity log — git and GitHub Issues hold history.

## Testing and Validation

- Add or update tests when changing behavior.
- Run the most relevant checks before handoff (`uv run pytest`; tests use synthetic/redacted fixtures only).

## Documentation

- Keep durable decisions in `.agent/System/decisions.md` (big ones as ADRs in `docs/adr/`).
- Keep user-facing setup and usage notes in `README.md`.
- Avoid temporary process notes in user-facing documentation.

## Agent skills

### Issue tracker

GitHub Issues via `gh`; see Issue Tracking above.

### Triage labels

Default five labels (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: glossary at `.agent/System/domain_language.md`, ADRs under `docs/adr/`. See `docs/agents/domain.md`.
