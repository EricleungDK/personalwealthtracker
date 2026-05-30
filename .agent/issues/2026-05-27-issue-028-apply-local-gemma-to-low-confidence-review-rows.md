---
type: issue
id: ISSUE-028
title: Apply Local Gemma To Low-Confidence Review Rows
status: done
slice_type: AFK
labels:
  - done
parent: 2026-05-27-prd-local-gemma-review-suggestions.md
blocked_by: []
created: 2026-05-27
---

# Apply Local Gemma To Low-Confidence Review Rows

## Parent

[PRD: Local Gemma Review Suggestions](./2026-05-27-prd-local-gemma-review-suggestions.md)

## What To Build

Extend Local LLM Mode beyond unmatched transactions so it also assists low-confidence deterministic suggestions that already require review. High-confidence deterministic matches, Monthly Review Decisions, Category Memory matches, and deterministic proxy split allocations must remain authoritative and must not be replaced by model output.

## Acceptance Criteria

- [x] Local Gemma runs on deterministic rule or recurring suggestions only when they are already `review_required=true`.
- [x] Local Gemma still runs on unmatched transactions.
- [x] High-confidence deterministic matches are not sent to the local model and remain unchanged.
- [x] Monthly Review Decisions are not replaced by model output.
- [x] Category Memory matches are not replaced by model output.
- [x] Proxy split allocation lines are not replaced by model output.
- [x] Low-confidence rows remain review-only even when the model suggests an existing leaf category.
- [x] The original low-confidence deterministic method/reason remains traceable in report or audit output when a model suggestion is applied.
- [x] Tests cover low-confidence rule, low-confidence recurring, high-confidence rule, Monthly Review Decision, Category Memory, and proxy split precedence cases.

## Blocked By

- [ISSUE-027: Suggest Existing Leaf Categories With Local Gemma](./2026-05-27-issue-027-suggest-existing-leaf-categories-with-local-gemma.md)
