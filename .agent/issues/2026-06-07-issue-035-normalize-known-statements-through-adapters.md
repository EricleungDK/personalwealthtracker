---
type: issue
id: ISSUE-035
title: Normalize Known Statements Through Adapters
status: done
slice_type: AFK
labels:
  - done
parent: 2026-06-07-prd-local-wealth-tracker-agent-public-package.md
blocked_by: []
created: 2026-06-07
---

# Normalize Known Statements Through Adapters

## Parent

[PRD: Local Wealth-Tracker Agent Public Package](./2026-06-07-prd-local-wealth-tracker-agent-public-package.md)

## What To Build

Introduce a Trusted Statement Adapter contract for deterministic parsers of known formats and route existing Nordea CSV/PDF parsing through that contract. Public examples should use synthetic statements and produce normalized transaction artifacts that monthly planning can consume consistently.

## Acceptance Criteria

- [x] A Trusted Statement Adapter interface defines normalized transaction fields, provenance, parser identity, and reporting-period validation.
- [x] Existing Nordea CSV/PDF parsing is available through the adapter routing path.
- [x] Synthetic known-format statement fixtures exercise the adapter path without private data.
- [x] Known-format imports produce normalized transactions with date, amount, currency, description, direction, source, and stable transaction ID fields.
- [x] Adapter failures, unsupported currencies, duplicate rows, and out-of-period transactions appear in import diagnostics.
- [x] Tests cover adapter routing, normalized artifacts, diagnostics, and compatibility with existing monthly planning behavior.

## Blocked By

None - can start immediately.
