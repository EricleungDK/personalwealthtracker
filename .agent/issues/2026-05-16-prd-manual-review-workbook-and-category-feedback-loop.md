---
type: prd
id: PRD-2026-05-16-MANUAL-REVIEW-FEEDBACK
title: Manual Review Workbook And Category Feedback Loop
status: ready
labels:
  - ready-for-agent
created: 2026-05-16
---

# Manual Review Workbook And Category Feedback Loop

## Problem Statement

The monthly tracker workflow currently produces a `review_required` CSV that is not practical for real manual classification. It exposes sparse exception data, including transaction IDs without enough transaction context, and it is not directly shaped as the source of truth for confirmed review decisions.

During local dry-run testing with a real Nordea CSV, the transaction classification rate and no-review rate were low. The current output makes that problem harder to fix because the user has to inspect transactions manually, map transaction IDs back to descriptions, and reshape data before category memory can learn from confirmed decisions.

The operator workflow needs a human-friendly review artifact that shows full transaction context, offers dropdowns based on the actual tracker workbook fields, distinguishes current-month manual decisions from future learning, and feeds reviewed decisions back into a follow-up dry run safely.

## Solution

Add a durable manual review and feedback loop for monthly dry runs.

The workflow should first stabilize transaction IDs so reviewed decisions can be matched reliably across repeated exports. Dry runs should then generate both the existing machine-friendly CSV and a human-friendly Excel review workbook. The review workbook should include a focused `Review Required` sheet, a complete `All Transactions` audit sheet, a `Category Options` sheet sourced from the current Tracker Workbook row labels, and run metadata including reporting period, parser, and transaction ID scheme.

Manual review should use `manual_category` for the current-month transaction decision and `learn_to_memory` to opt into future Category Memory learning. A follow-up dry run should accept an explicit `--review-decisions` file, apply exact transaction-ID decisions before automatic categorization, and preserve existing workbook write safety. The learning command should also import reviewed XLSX artifacts, but only learn rows where `learn_to_memory=yes` and the selected workbook field is learnable.

Dry-run reports should include Categorization Quality diagnostics so classification rate, no-review rate, unmatched rows, review-required rows, and method distribution are visible every month.

## User Stories

1. As the tracker owner, I want the manual review output to show transaction descriptions, so that I can classify transactions without cross-referencing another file.
2. As the tracker owner, I want a review workbook with dropdowns, so that classification is faster and less error-prone than typing category names.
3. As the tracker owner, I want dropdown options to come from my current Tracker Workbook fields, so that review choices match the actual workbook I maintain.
4. As the tracker owner, I want all workbook fields available in the dropdown, so that the review surface reflects the full tracker rather than a partial config list.
5. As the tracker owner, I want unsafe or derived workbook fields flagged, so that I can see when a selected field will not be learned or directly written.
6. As the tracker owner, I want exact workbook row labels used as category values, so that a reviewed category maps back to the workbook without translation.
7. As the tracker owner, I want a focused work queue for transactions requiring review, so that I can quickly classify only the rows needing action.
8. As the tracker owner, I want an all-transactions audit sheet, so that I can debug low classification and no-review rates across the whole statement.
9. As the tracker owner, I want merchant identity visible in the review workbook, so that I can decide whether a decision is safe to learn for future months.
10. As the tracker owner, I want `manual_category` to mean the current-month category decision, so that I can classify a transaction without implying future automation.
11. As the tracker owner, I want `learn_to_memory` to be opt-in, so that only trusted merchant decisions become future Category Memory.
12. As the tracker owner, I want blank or `no` `learn_to_memory` values to avoid future learning, so that one-off decisions do not poison future categorization.
13. As the tracker owner, I want reviewed decisions to apply only when I explicitly pass the review file, so that stale files are not accidentally used.
14. As the tracker owner, I want reviewed decisions validated against the reporting month, so that April decisions cannot accidentally affect May.
15. As the tracker owner, I want reviewed decisions matched by stable transaction IDs, so that repeated exports of the same month can reuse my work.
16. As the tracker owner, I want missing or stale transaction IDs reported clearly, so that decisions are not silently applied to the wrong row.
17. As the tracker owner, I want manual decisions to override automatic categorization for exact transactions, so that my reviewed category wins for the current month.
18. As the tracker owner, I want workbook write safety to remain authoritative, so that manual review cannot force writes into formula-owned, fixed, populated, or unsafe cells.
19. As the tracker owner, I want dry-run reports to show transaction classification rate, so that I can measure whether the categorizer is improving.
20. As the tracker owner, I want dry-run reports to show no-review rate, so that I can measure how much manual work remains.
21. As the tracker owner, I want categorization counts by method, so that I can see whether matches came from rules, category memory, manual decisions, or unmatched fallback.
22. As the tracker owner, I want Category Memory learning from reviewed XLSX files, so that I do not have to reshape the review workbook into a separate CSV.
23. As the tracker owner, I want the existing CSV outputs retained, so that automation, debugging, and simple file inspection still work.
24. As a developer, I want transaction ID schemes versioned, so that old review artifacts can be accepted or rejected explicitly.
25. As a developer, I want review workbooks to include run metadata, so that imports can validate period, parser, and ID compatibility.
26. As a developer, I want stable duplicate handling for transaction IDs, so that repeated identical transactions remain distinguishable without relying on source row order.
27. As a developer, I want review workbook generation tested with synthetic data, so that real financial data stays ignored and uncommitted.
28. As a developer, I want the review decision importer tested through the CLI and pipeline, so that current-month manual decisions are visible in dry-run outputs.
29. As a developer, I want category-memory import validation tested, so that `learn_to_memory=yes` cannot learn derived or fixed workbook fields.
30. As a developer, I want this feature split into small implementation slices, so that each part is independently verifiable.

## Implementation Decisions

- Implement stable content-based transaction IDs before official review workbook generation.
- Version transaction ID schemes with a readable scheme name.
- Transaction IDs must not depend on source file path or original row position.
- Duplicate transactions should be disambiguated using a deterministic occurrence number after stable sorting by transaction content.
- The review artifact should include run metadata: reporting year, reporting month, statement parser, generated timestamp, and transaction ID scheme.
- Keep the existing `review_required` CSV as a machine-friendly artifact.
- Add a review XLSX artifact generated by monthly dry runs.
- The review XLSX should contain `Review Required`, `All Transactions`, `Category Options`, and `Run Metadata` sheets.
- `Review Required` is the operator work queue and should contain only rows needing manual action.
- `All Transactions` is the audit/debug context and should contain every parsed transaction.
- `Category Options` should be sourced from all non-empty labels in the current Tracker Workbook category column.
- `manual_category` dropdown values should use exact Tracker Workbook row labels.
- The review workbook should not hide derived, fixed, or otherwise unsafe workbook fields, but should flag learnability and write-safety warnings.
- `learn_to_memory` should be a dropdown with blank default and `yes`/`no` options.
- `manual_category` filled with blank or `no` `learn_to_memory` means use the decision for the current month only.
- `manual_category` filled with `learn_to_memory=yes` means use the decision for the current month and attempt to learn it into Category Memory.
- Category Memory learning should be opt-in and limited to learnable workbook fields.
- A learnable workbook field exists in the workbook and is not derived or fixed.
- Current-month cell write safety remains separate from learnability; a populated or formula current-month cell can block writing without blocking future learning.
- Add an explicit `--review-decisions` CLI option for applying Monthly Review Decisions.
- Do not auto-detect the latest review workbook from the reports directory.
- Import should validate reviewed artifact reporting period and transaction ID scheme.
- Import should warn or fail clearly for reviewed transaction IDs that are not present in the current statement.
- Monthly Review Decisions should apply by exact transaction ID before automatic categorization.
- Desired categorization precedence is Monthly Review Decisions, Category Memory, hand-written historical mappings, recurring rules, keyword rules, unmatched review.
- Workbook write safety remains authoritative after manual decisions are applied.
- `learn-category-memory` should support reviewed XLSX artifacts in addition to the existing reviewed CSV workflow.
- Dry-run reports should include Categorization Quality diagnostics for classification rate, no-review rate, unmatched count, review-required count, and counts by categorization method.

## Testing Decisions

- Tests should verify external behavior through parser, pipeline, CLI, reporting, review workbook, and category-memory interfaces rather than private implementation details.
- Transaction ID tests should prove stable IDs across repeated parses of the same transactions and across changed input ordering.
- Transaction ID tests should cover duplicate-looking transactions and deterministic disambiguation.
- Review workbook tests should use synthetic tracker workbooks and synthetic transactions only.
- Review workbook tests should verify sheets, headers, dropdown validations, metadata, category options from workbook labels, and learnability/status columns.
- Monthly Review Decision tests should verify explicit CLI input, period validation, missing transaction handling, exact-ID overrides, method reporting, and preservation of workbook safety.
- Category Memory XLSX import tests should verify opt-in learning, blank/no learning behavior, learnable-field validation, warning/skip behavior for derived or fixed fields, and preservation of existing memory.
- Report tests should verify Categorization Quality diagnostics and method distributions.
- Documentation tests should be updated if the monthly workflow runbook changes.
- Real CSV, workbook, review, report, backup, and memory files remain ignored and must not be committed.

## Out of Scope

- LLM categorization.
- Automatic learning during workbook commit.
- Auto-detecting or auto-applying the latest review workbook.
- Fuzzy matching reviewed decisions when transaction IDs do not match.
- A graphical application or web UI for review.
- Generic bank support beyond current Nordea sources.
- Investment statement evidence.
- Changing existing workbook write safety rules.
- Committing real bank, workbook, review, report, backup, or category-memory data.

## Further Notes

This PRD came from a grilling session after a local dry run showed that real CSV transaction classification rate and no-review rate were still too low. The key correction was that the manual review artifact should become the source-of-truth decision sheet for current-month review and optional future learning, not just a sparse exception report.
