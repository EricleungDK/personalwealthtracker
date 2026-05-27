---
type: issue
id: ISSUE-028
title: Apply Local Gemma To Low-Confidence Review Rows
status: blocked
slice_type: AFK
labels:
  - blocked
parent: 2026-05-27-prd-local-gemma-review-suggestions.md
blocked_by:
  - ISSUE-027
created: 2026-05-27
---

# Apply Local Gemma To Low-Confidence Review Rows

## Parent

[PRD: Local Gemma Review Suggestions](./2026-05-27-prd-local-gemma-review-suggestions.md)

## What To Build

Extend Local LLM Mode beyond unmatched transactions so it also assists low-confidence deterministic suggestions that already require review. High-confidence deterministic matches, Monthly Review Decisions, Category Memory matches, and deterministic proxy split allocations must remain authoritative and must not be replaced by model output.

## Acceptance Criteria

- [ ] Local Gemma runs on deterministic rule or recurring suggestions only when they are already `review_required=true`.
- [ ] Local Gemma still runs on unmatched transactions.
- [ ] High-confidence deterministic matches are not sent to the local model and remain unchanged.
- [ ] Monthly Review Decisions are not replaced by model output.
- [ ] Category Memory matches are not replaced by model output.
- [ ] Proxy split allocation lines are not replaced by model output.
- [ ] Low-confidence rows remain review-only even when the model suggests an existing leaf category.
- [ ] The original low-confidence deterministic method/reason remains traceable in report or audit output when a model suggestion is applied.
- [ ] Tests cover low-confidence rule, low-confidence recurring, high-confidence rule, Monthly Review Decision, Category Memory, and proxy split precedence cases.

## Blocked By

- [ISSUE-027: Suggest Existing Leaf Categories With Local Gemma](./2026-05-27-issue-027-suggest-existing-leaf-categories-with-local-gemma.md)
