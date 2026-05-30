---
type: issue
id: ISSUE-027
title: Suggest Existing Leaf Categories With Local Gemma
status: done
slice_type: AFK
labels:
  - done
parent: 2026-05-27-prd-local-gemma-review-suggestions.md
blocked_by: []
created: 2026-05-27
---

# Suggest Existing Leaf Categories With Local Gemma

## Parent

[PRD: Local Gemma Review Suggestions](./2026-05-27-prd-local-gemma-review-suggestions.md)

## What To Build

Use the configured local Gemma provider to produce structured review-only suggestions for unmatched transactions. The model prompt should use minimized transaction context and the YAML leaf Allowed Category Set, and a valid existing-leaf response should populate the existing suggestion fields without adding primary review workbook columns.

## Acceptance Criteria

- [x] Local Gemma is invoked for unmatched transactions only in this slice.
- [x] Prompt context includes Merchant Identity, amount, date, direction, and YAML Leaf Category Row choices.
- [x] Raw Nordea descriptions are excluded from prompts by default.
- [x] The Allowed Category Set excludes Parent/Section Rows, derived rows, and missing categories.
- [x] A valid model response for an existing leaf category populates `suggested_category`, `method`, `confidence`, and `reason`.
- [x] The categorization method identifies the model suggestion, for example `local_llm_gemma`.
- [x] Model suggestions remain `review_required=true` and cannot auto-write workbook values.
- [x] The Review Required workbook does not gain new primary LLM suggestion columns.
- [x] Invalid JSON, missing fields, and categories outside the Allowed Category Set leave the original unmatched review state intact and produce a warning.
- [x] Tests cover prompt construction, valid existing-leaf suggestions, invalid provider responses, review workbook shape, report output, and audit output with mocked provider calls.

## Blocked By

- [ISSUE-026: Add Local LLM Opt-In Provider Scaffold](./2026-05-27-issue-026-add-local-llm-opt-in-provider-scaffold.md)
