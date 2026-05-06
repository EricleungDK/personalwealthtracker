# PersonalWorthTracker Context

Last updated: 2026-05-06

## Project State

- Phase: MVP 1 implementation scaffold.
- Framework: Python local CLI.
- Package manager: uv with `pyproject.toml`.
- Product requirements: Defined from `personal_wealth_tracker_project_case_background.md`.
- Implementation status: Nordea PDF-first MVP scaffold implemented and dry-run validated.

## Active Tasks

| Task ID | Status | Owner | Notes |
|---------|--------|-------|-------|
| SETUP-001 | COMPLETE | Codex | Created baseline folder structure and starter guidance files. |
| MVP1-001 | COMPLETE | Codex | Implemented local Nordea PDF parsing, deterministic categorization, safe workbook planning/writing, reports, and tests. |

## Active Delegations

| Sub-Agent | Task ID | Status | Started | Expected Completion |
|-----------|---------|--------|---------|---------------------|

## Decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-05-06 | Use the workspace baseline folder structure. | User requested folder construction based on the workspace `AGENTS.md` template before project details are defined. |
| 2026-05-06 | Build MVP 1 as a Python CLI using uv. | Keeps the workflow local, testable, and easy to extend later. |
| 2026-05-06 | Use Nordea PDF account statements as the first ingestion source. | User provided `bank-statement.pdf`; inspection showed a Nordea `Kontoudskrift` with embedded text and DKK booked amounts. |
| 2026-05-06 | Treat DKK as the MVP tracker currency. | User selected DKK despite the current workbook label showing `in EUR`; docs record the mismatch. |
| 2026-05-06 | Ignore real statements, workbooks, reports, backups, and generated financial data. | The project handles sensitive personal finance data and must not commit local inputs or outputs. |
| 2026-05-06 | Pin local development to Python 3.12. | The project requires Python 3.11+ and the workspace now has Python 3.12.13 plus uv installed. |

## Open Questions

- A redacted Nordea PDF fixture is still needed for end-to-end parser tests.
- The workbook label currently says `in EUR`; it should be corrected or explicitly accepted as a stale label before regular use.
- Category rules need to be expanded from real transaction review after the first dry-run.

## Activity Log

- 2026-05-06: Created baseline project folders and starter files.
- 2026-05-06: Added MVP 1 implementation plan based on Nordea PDF input and DKK workbook policy.
- 2026-05-06: Implemented MVP 1 scaffold, installed Python 3.12 and uv, ran tests, and validated dry-run parsing of the local Nordea PDF.
- 2026-05-06: Created and pushed initial commit `0c0992a feat: initialize wealth tracker automation` to `origin/main`.
- 2026-05-06: Created EOD summary in `docs/Daily_blogpost/2026-05-06.md`.
