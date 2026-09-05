---
type: issue
id: ISSUE-040
title: Publish Package Docs And Synthetic Examples
status: done
slice_type: AFK
labels:
  - done
parent: 2026-06-07-prd-local-wealth-tracker-agent-public-package.md
blocked_by: []
created: 2026-06-07
---

# Publish Package Docs And Synthetic Examples

## Parent

[PRD: Local Wealth-Tracker Agent Public Package](./2026-06-07-prd-local-wealth-tracker-agent-public-package.md)

## What To Build

Prepare the public-package user and developer documentation around the completed local workflow. The docs should teach installation, setup, synthetic examples, trusted statement imports, unknown-format import review, monthly planning, learning, copied-workbook commit, optional local model integration, public/private boundaries, and v1 non-goals.

## Acceptance Criteria

- [x] User-facing docs explain install, setup/init, template workbook use, statement import, review, monthly planning, learning, and commit-to-copy workflows.
- [x] Synthetic examples let users exercise the workflow without real financial data.
- [x] Developer docs explain the public/private boundary, template workbook version contract, Trusted Statement Adapter contract, Statement Import Assistant contract, and Importer Profile storage.
- [x] Docs state that arbitrary finance workflow support means extensible adapters plus model-assisted review flows, not guaranteed trusted parsing of every financial document.
- [x] Docs state v1 non-goals: desktop app, SaaS, required remote LLMs, autonomous finance decisions, direct original-workbook edits, arbitrary formula/layout editing, live FX, bank APIs, scheduler, cloud sync, and public shipping of private data.
- [x] Documentation tests or validation checks cover current command names, sample paths, and synthetic example references.

## Blocked By

None - can start immediately.
