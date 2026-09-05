---
type: issue
id: ISSUE-031
title: Codify Public Package Boundary
status: done
slice_type: AFK
labels:
  - done
parent: 2026-06-07-prd-local-wealth-tracker-agent-public-package.md
blocked_by: []
created: 2026-06-07
---

# Codify Public Package Boundary

## Parent

[PRD: Local Wealth-Tracker Agent Public Package](./2026-06-07-prd-local-wealth-tracker-agent-public-package.md)

## What To Build

Define the reusable public package boundary for the Local Wealth-Tracker Agent and separate it from private local profile data. The project should expose a clear contract for what can ship publicly, what must remain ignored local state, and how real statements, generated outputs, local rules, Category Memory, Importer Profiles, proxy split rules, and profile paths are kept out of Git by default.

## Acceptance Criteria

- [x] Public package responsibilities are documented separately from private profile responsibilities.
- [x] Real statements, generated reports, copied workbooks, local rules, Category Memory, Importer Profiles, and proxy split rules have explicit local/private paths.
- [x] Git ignore rules and sample files demonstrate that private financial inputs and learned local state are not committed.
- [x] Existing private workflow behavior remains usable while the public package boundary is introduced.
- [x] Tests or validation checks prove sample public paths and ignored private paths behave as documented.
- [x] Documentation preserves the safety boundary that the product is a local wealth-tracker agent, not an autonomous finance authority.

## Blocked By

None - can start immediately.
