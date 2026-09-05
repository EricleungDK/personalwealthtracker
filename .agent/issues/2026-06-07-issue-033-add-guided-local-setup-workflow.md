---
type: issue
id: ISSUE-033
title: Add Guided Local Setup Workflow
status: done
slice_type: AFK
labels:
  - done
parent: 2026-06-07-prd-local-wealth-tracker-agent-public-package.md
blocked_by: []
created: 2026-06-07
---

# Add Guided Local Setup Workflow

## Parent

[PRD: Local Wealth-Tracker Agent Public Package](./2026-06-07-prd-local-wealth-tracker-agent-public-package.md)

## What To Build

Add a guided setup or init command that creates a local tracker workspace from the public package. A new user should be able to create local directories, place a template workbook, write sample config/profile files, choose a Tracker Currency, and see where private profile data will live.

## Acceptance Criteria

- [x] A public CLI setup command creates the expected local directory structure.
- [x] Setup places or references the synthetic Template Excel Workbook without touching private paths.
- [x] Setup writes sample config/profile files that include Tracker Currency and profile path settings.
- [x] Existing workflows can run against the initialized local workspace using synthetic examples.
- [x] Re-running setup is safe and does not overwrite user-edited local files without an explicit opt-in.
- [x] Tests verify setup output, idempotency, sample config contents, and private path separation.

## Blocked By

None - can start immediately.

## Implementation Notes

- Added `src/personal_wealth_tracker/setup_workspace.py` with idempotent workspace initialization, generic config/profile generation, private data directories, synthetic Template Workbook creation, and a synthetic Nordea CSV example.
- Added `wealth-tracker setup` with `--workspace`, `--tracker-currency`, `--start-year`, and explicit `--force` overwrite.
- Added setup workflow tests covering output layout, idempotency, CLI reporting, sample config/profile contents, private path separation, and a synthetic dry run against the initialized workspace.
- Verified with `PYTHONPATH=src python3 -m pytest tests/test_setup_workspace.py tests/test_template_workbook.py tests/test_cli.py tests/test_documentation.py`.
