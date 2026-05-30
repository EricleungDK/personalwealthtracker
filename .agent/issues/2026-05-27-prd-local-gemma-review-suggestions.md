---
type: prd
id: PRD-2026-05-27-LOCAL-GEMMA-REVIEW-SUGGESTIONS
title: Local Gemma Review Suggestions
status: complete
labels:
  - done
created: 2026-05-27
---

# Local Gemma Review Suggestions

## Problem Statement

The monthly tracker has a safe deterministic categorization pipeline, but real Nordea CSV runs still leave unresolved review work. Unmatched transactions and low-confidence deterministic suggestions force the tracker owner to manually inspect merchant context and choose a category in the review workbook.

The owner wants model-assisted categorization, but without turning the product into a remote API workflow or letting model output write to the Tracker Workbook automatically. The existing docs explicitly keep external APIs and LLMs out of MVP 1, while the architecture leaves room for local LLM classification after deterministic rules fail. The target machine is an Apple Silicon M1 MacBook with 16 GB unified memory, so the first provider should be a local Gemma model through Ollama rather than a remote OpenAI or Google API.

The review workbook is already wide. Any model-assisted design must reduce manual review effort without adding a cluster of new columns or weakening the existing review decision and Category Memory boundaries.

## Solution

Add an explicit opt-in Local LLM Mode that uses a local Gemma model through Ollama's local HTTP API to produce review-only category suggestions.

The feature should run only when the operator deliberately enables it, for example with a CLI flag and local config. It should process only unmatched transactions and low-confidence deterministic suggestions that already require review. High-confidence deterministic matches, Monthly Review Decisions, Category Memory matches, proxy split allocations, and workbook safety checks remain authoritative.

The local model prompt should use minimized context by default: Merchant Identity, amount, date, direction, and the Allowed Category Set from the YAML category registry. Raw Nordea descriptions stay out of the prompt unless a future evaluation shows minimized context is insufficient and an explicit debug/evaluation mode is added.

The provider should target `gemma4:e4b` first for the user's M1 16 GB MacBook, with `gemma4:e2b` as the lighter fallback if performance is unacceptable. The implementation should call Ollama's local HTTP API, not shell out to `ollama run`, so calls can be mocked, timed out, and validated.

The model output must be structured and constrained to one of three review outcomes: an existing YAML Leaf Category Row, `no_suggestion`, or an LLM New Leaf Candidate. Existing leaf suggestions should populate the existing `suggested_category`, `method`, `confidence`, and `reason` fields with `method=local_llm_gemma`. New leaf candidates should not update the Category Registry directly; they should be expressed in the reason/suggestion text so the operator can choose `new_parent_category` and `new_leaf_category` through the existing reviewed workflow.

If Ollama is unavailable, the model is missing, a request times out, or the response is invalid, the monthly run should continue. The original deterministic or unmatched review state should remain intact, and the report/audit output should include a warning. Provider failures should never silently broaden prompt data, auto-write workbook values, or import Category Memory.

## User Stories

1. As the tracker owner, I want local model suggestions for unmatched transactions, so that I spend less time manually searching for categories.
2. As the tracker owner, I want local model suggestions for low-confidence deterministic matches, so that weak rule matches get a second review hint.
3. As the tracker owner, I want high-confidence deterministic matches left alone, so that existing trusted automation is not replaced by a model guess.
4. As the tracker owner, I want Local LLM Mode to be explicit opt-in, so that model use happens only when I ask for it.
5. As the tracker owner, I want Gemma to run locally through Ollama, so that transaction context does not need to go to a remote API.
6. As the tracker owner, I want the first model target to fit my M1 16 GB MacBook, so that the workflow is usable on my actual machine.
7. As the tracker owner, I want a lighter fallback model, so that I can still test the workflow if the default model is too slow or memory-heavy.
8. As the tracker owner, I want prompts to use Merchant Identity instead of raw Nordea descriptions by default, so that local prompt data stays minimized.
9. As the tracker owner, I want the model to choose only from YAML Leaf Category Rows, so that parent rows, section totals, and invented write targets are rejected.
10. As the tracker owner, I want the model to be able to say `no_suggestion`, so that uncertain rows are not forced into bad categories.
11. As the tracker owner, I want the model to hint that a new leaf may be needed, so that missing categories are easier to notice.
12. As the tracker owner, I want new leaf hints to go through the existing review fields, so that the Category Registry is never updated automatically.
13. As the tracker owner, I want model suggestions to appear in existing suggestion fields, so that the Review Required sheet does not become wider.
14. As the tracker owner, I want `manual_category` to remain my confirmed decision, so that model output is never confused with approval.
15. As the tracker owner, I want `learn_to_memory=yes` to remain the only path to Category Memory learning, so that model output cannot train itself.
16. As the tracker owner, I want provider failures to fall back to ordinary manual review, so that a missing local model does not block a monthly run.
17. As the tracker owner, I want report warnings when Local LLM Mode fails or is partly skipped, so that I know which suggestions were not produced.
18. As the tracker owner, I want audit output to show model suggestion status, so that the run remains traceable.
19. As the tracker owner, I want dry-run quality metrics to include local model assistance, so that I can judge whether it reduces review effort.
20. As the tracker owner, I want commit mode safety unchanged, so that local model suggestions cannot write unsafe workbook cells.
21. As a developer, I want a structured provider response contract, so that invalid JSON and invalid categories can be rejected consistently.
22. As a developer, I want the Ollama integration mocked in tests, so that test runs do not require a local model installation.
23. As a developer, I want timeouts and invalid responses tested, so that provider failure behavior is reliable.
24. As a developer, I want prompt construction tested independently, so that minimized prompt context does not regress.
25. As a developer, I want the pipeline integration tested end-to-end with synthetic statements and workbooks, so that real financial data stays ignored.

## Implementation Decisions

- Add Local LLM Mode as a review-assistance feature, not as a deterministic categorization source.
- Local LLM Mode is explicit opt-in through CLI and/or local config; it must not run merely because Ollama is installed.
- Use Ollama's local HTTP API for provider calls.
- Avoid adding a new HTTP dependency unless the standard library proves insufficient for timeouts and JSON handling.
- Configure `gemma4:e4b` as the initial default model for the user's Apple Silicon M1 16 GB MacBook.
- Configure `gemma4:e2b` as the lighter fallback model.
- Local model calls are eligible only for unmatched transactions and low-confidence deterministic suggestions with `review_required=true`.
- High-confidence deterministic matches, Monthly Review Decisions, Category Memory matches, and proxy split allocation lines are not replaced by model output.
- Prompt context defaults to Merchant Identity, amount, date, direction, and the Allowed Category Set.
- Raw Nordea descriptions are excluded from the prompt by default.
- The Allowed Category Set contains YAML Leaf Category Rows only.
- The model response must parse into one of: existing leaf category, `no_suggestion`, or LLM New Leaf Candidate.
- Existing leaf suggestions reuse `suggested_category`, `method`, `confidence`, and `reason`.
- `method` should identify local Gemma suggestions, for example `local_llm_gemma`.
- The Review Required sheet should not gain new primary model suggestion columns.
- `manual_category`, `new_parent_category`, `new_leaf_category`, and `learn_to_memory` remain the only editable review decision fields.
- LLM New Leaf Candidates are hints only and must flow through the existing reviewed new-leaf category workflow.
- Provider failures, invalid JSON, invalid categories, missing models, unavailable Ollama, and timeouts should not fail the monthly run.
- Failure fallback keeps the original deterministic or unmatched review state and adds report/audit warnings.
- Workbook planning and commit mode safety remain unchanged.
- Category Memory learning remains based only on confirmed reviewed decisions with `learn_to_memory=yes`.

## Testing Decisions

- Test external behavior through CLI/pipeline output, review workbooks, categorized CSVs, reports, and audit logs rather than provider implementation details.
- Add focused unit tests for prompt construction to verify minimized context and YAML leaf-only category sets.
- Add provider client tests using mocked Ollama HTTP responses for valid category, `no_suggestion`, new leaf candidate, invalid JSON, invalid category, timeout, and unavailable model cases.
- Add pipeline tests showing local model suggestions applied to unmatched rows and low-confidence deterministic review rows.
- Add pipeline tests showing high-confidence deterministic matches are unchanged when Local LLM Mode is enabled.
- Add review workbook tests proving no new primary model columns are added and suggestions appear in existing fields.
- Add report/audit tests for provider attempt counts, successful suggestions, failures, and warning text.
- Add Category Memory tests proving local model suggestions are not learned unless the operator confirms the decision through the existing reviewed workflow.
- Use synthetic statements, synthetic workbooks, and mocked provider calls only.

## Out of Scope

- Remote LLM APIs.
- Using the user's ChatGPT/Codex Plus subscription as a runtime provider.
- Auto-writing workbook values from model output.
- Auto-updating the Category Registry from model output.
- Auto-learning Category Memory from model output.
- Prompting with raw Nordea descriptions by default.
- Reading itemized Revolut, credit card, or investment statements.
- Generic multi-provider LLM abstraction beyond the local Ollama/Gemma path.
- Installing Ollama or downloading Gemma models automatically.
- Changing workbook commit safety rules.

## Further Notes

This PRD comes from the local Gemma grilling session on 2026-05-27. The key boundary is that Local LLM Mode can reduce manual search effort in the review workbook, but it does not become a source of truth. The Tracker Workbook remains authoritative, deterministic high-confidence matches remain authoritative, and user-confirmed review decisions remain the only bridge from suggestions to workbook writes or Category Memory.
