---
type: issue
id: ISSUE-037
title: Learn Local Importer Profiles
status: done
slice_type: AFK
labels:
  - done
parent: 2026-06-07-prd-local-wealth-tracker-agent-public-package.md
blocked_by: []
created: 2026-06-07
---

# Learn Local Importer Profiles

## Parent

[PRD: Local Wealth-Tracker Agent Public Package](./2026-06-07-prd-local-wealth-tracker-agent-public-package.md)

## What To Build

Allow a user-confirmed unknown-format import to create a private local Importer Profile. The profile should capture enough reviewed mapping information to recognize a similar future source, while remaining local by default and exportable only through an explicit user action.

## Acceptance Criteria

- [x] Confirmed import review decisions can create or update a local Importer Profile.
- [x] Importer Profiles store reviewed source identity, field mappings, validation assumptions, and category decision metadata without raw private statement dumps.
- [x] Importer Profiles live under ignored local profile paths by default.
- [x] Profile creation requires confirmed import review, not raw model suggestions alone.
- [x] A manual export command or workflow can export a chosen Importer Profile explicitly.
- [x] Tests cover profile creation, ignored storage paths, reset/update behavior, and explicit export.

## Blocked By

None - can start immediately.
