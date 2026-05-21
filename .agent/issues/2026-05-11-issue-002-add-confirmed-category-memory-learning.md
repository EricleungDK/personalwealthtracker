---
type: issue
id: ISSUE-002
title: Add Confirmed Category Memory Learning
status: done
slice_type: AFK
labels:
  - done
parent: 2026-05-11-prd-monthly-tracker-workbook-updater-next-slices.md
blocked_by: []
created: 2026-05-11
---

# Add Confirmed Category Memory Learning

## Parent

[PRD: Monthly Tracker Workbook Updater Next Slices](./2026-05-11-prd-monthly-tracker-workbook-updater-next-slices.md)

## What To Build

Add private category memory that learns only from user-confirmed reviewed decisions. The learning workflow must be separate from monthly dry-run and commit mode: the user reviews an exported decision file, imports it through a learning command, then reruns dry-run before any workbook commit.

Category memory should live under ignored private generated data, separate from hand-written local rules. Future matching should use normalized merchant identity by default, with optional amount/date hints for recurring decisions.

## Acceptance Criteria

- [ ] Category memory is stored under ignored private generated data, not inside local hand-written rules.
- [ ] A reviewed decision import command exists separately from monthly dry-run and commit mode.
- [ ] The import command accepts confirmed category decisions and rejects incomplete or invalid rows with useful messages.
- [ ] Category memory learns only from confirmed review decisions.
- [ ] Category memory is never created from unconfirmed automatic matches.
- [ ] Learned mappings use normalized merchant identity rather than raw full descriptions.
- [ ] Recurring learned mappings can include optional amount tolerance and day-window hints.
- [ ] One confirmed review decision can become a deterministic future category match.
- [ ] Monthly commit mode does not import reviewed decisions in the same command.
- [ ] Tests cover import validation, matching behavior, recurring hints, persistence, and no learning from guesses.

## Blocked By

None - can start immediately.
