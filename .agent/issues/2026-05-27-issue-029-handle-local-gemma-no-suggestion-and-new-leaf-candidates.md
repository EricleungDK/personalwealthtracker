---
type: issue
id: ISSUE-029
title: Handle Local Gemma No-Suggestion And New-Leaf Candidates
status: done
slice_type: AFK
labels:
  - done
parent: 2026-05-27-prd-local-gemma-review-suggestions.md
blocked_by: []
created: 2026-05-27
---

# Handle Local Gemma No-Suggestion And New-Leaf Candidates

## Parent

[PRD: Local Gemma Review Suggestions](./2026-05-27-prd-local-gemma-review-suggestions.md)

## What To Build

Complete the structured Local LLM Suggestion contract by handling `no_suggestion` and LLM New Leaf Candidate responses. These outcomes should help the operator review rows without creating new editable columns, without updating the Category Registry automatically, and without learning Category Memory from model output.

## Acceptance Criteria

- [x] The provider response contract accepts `category`, `no_suggestion`, and `new_leaf_candidate` statuses.
- [x] `no_suggestion` leaves the transaction review-required and does not invent a category.
- [x] `no_suggestion` is visible in existing suggestion context such as `method`, `confidence`, `reason`, report, or audit output.
- [x] An LLM New Leaf Candidate does not populate `manual_category`, `new_parent_category`, or `new_leaf_category`.
- [x] An LLM New Leaf Candidate does not update the YAML Category Registry.
- [x] An LLM New Leaf Candidate is visible through existing suggestion context so the operator can manually fill the reviewed new-leaf fields.
- [x] LLM New Leaf Candidate text is treated as a hint and is not accepted as a workbook write target.
- [x] Category Memory import ignores unconfirmed model suggestions and learns only after the operator confirms a valid manual or reviewed new-leaf decision with `learn_to_memory=yes`.
- [x] Tests cover `no_suggestion`, new leaf candidate display, no automatic registry update, no automatic learning, and review workbook compatibility.

## Blocked By

- [ISSUE-027: Suggest Existing Leaf Categories With Local Gemma](./2026-05-27-issue-027-suggest-existing-leaf-categories-with-local-gemma.md)
