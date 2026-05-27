---
type: issue
id: ISSUE-030
title: Add Local Gemma Evaluation Diagnostics And Docs
status: blocked
slice_type: AFK
labels:
  - blocked
parent: 2026-05-27-prd-local-gemma-review-suggestions.md
blocked_by:
  - ISSUE-028
  - ISSUE-029
created: 2026-05-27
---

# Add Local Gemma Evaluation Diagnostics And Docs

## Parent

[PRD: Local Gemma Review Suggestions](./2026-05-27-prd-local-gemma-review-suggestions.md)

## What To Build

Add operator-facing diagnostics and documentation for Local LLM Mode. Dry-run reports and audit logs should make local model usage measurable, and user-facing docs should explain setup assumptions, explicit opt-in, review-only behavior, fallback behavior, and the first recommended Gemma model choices.

## Acceptance Criteria

- [ ] Reports include Local LLM Mode status when the feature is enabled.
- [ ] Reports include counts for eligible rows, attempted provider calls, existing-leaf suggestions, `no_suggestion`, new leaf candidates, invalid responses, and provider failures.
- [ ] Reports preserve the existing classification rate and no-review rate semantics.
- [ ] Audit output records enough local model metadata to trace suggestion status without requiring raw prompt dumps.
- [ ] Provider warnings are visible when Ollama is unavailable, the model is missing, the call times out, or a response is invalid.
- [ ] User-facing workflow docs explain that Local LLM Mode is explicit opt-in and review-only.
- [ ] User-facing workflow docs explain that `gemma4:e4b` is the initial target and `gemma4:e2b` is the fallback for the user's M1 16 GB MacBook.
- [ ] Docs explain that model suggestions reuse existing review workbook suggestion fields and do not add primary columns.
- [ ] Docs explain that raw Nordea descriptions are excluded from prompts by default.
- [ ] Tests cover report metrics, audit warnings, and documentation invariants where the project already has doc tests.

## Blocked By

- [ISSUE-028: Apply Local Gemma To Low-Confidence Review Rows](./2026-05-27-issue-028-apply-local-gemma-to-low-confidence-review-rows.md)
- [ISSUE-029: Handle Local Gemma No-Suggestion And New-Leaf Candidates](./2026-05-27-issue-029-handle-local-gemma-no-suggestion-and-new-leaf-candidates.md)
