# Project Context

Last updated: 2026-10-01

A short snapshot of where the project stands. Keep it small: settled decisions go to `../System/decisions.md`, and task tracking lives in GitHub Issues.

## State

- A Python CLI (`wealth-tracker`), managed with uv, Python 3.12.
- Main flow: `wealth-tracker monthly`. It parses the newest Nordea CSV, decides each row's authority (Trust Policy plus a two-model local Consensus), writes one Exception Sheet per month, commits the month atomically into the tracker in place after a backup (ADR 0007), and learns Category Memory on commit.
- Also shipped: public-package tooling (`setup`, `template-workbook`, `import-statement`, `importer-profile`), proxy split transfers, the YAML category registry and leaf row insertion.
- The last feature batch was GitHub #2-#20, merged in PR #15 on 2026-09-26.

## Where Things Live

| Need | Location |
|------|----------|
| Current decisions and why | `.agent/System/decisions.md` |
| Design decisions (ADRs) | `docs/adr/` |
| Terms | `.agent/System/domain_language.md` |
| Modules and flow | `.agent/System/architecture.md` |
| File formats | `.agent/System/data_contracts.md` |
| Privacy rules | `.agent/System/security_privacy.md` |
| Operator how-to | `docs/monthly_workflow.md`, `docs/cli_reference.md` |
| README demo | `scripts/record_demo.py` (real synthetic run; needs ffmpeg + two local Ollama models), pure parts in `scripts/demo_timeline.py`, outputs + record in `docs/assets/` |
| Open work | GitHub Issues (`gh issue list`) |
| History | git log, GitHub Issues |

## Open Questions

- Investment statement evidence is blocked until a redacted sample statement and a workbook mapping are available. This also needs the USD→DKK rate config shape and the report/audit fields.
- Crypto and digital assets need a dedicated valuation source first.
- Hosted judgment (ADR 0005) waits for a future opt-in adapter.

## Non-Goals

- Personal finance ledger semantics, generic multi-bank ingestion, live FX, and direct writes to formula rows or section totals.
