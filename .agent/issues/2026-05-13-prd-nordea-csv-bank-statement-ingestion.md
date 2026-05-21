---
type: prd
id: PRD-2026-05-13-NORDEA-CSV
title: Nordea CSV Bank Statement Ingestion
status: done
labels:
  - done
created: 2026-05-13
---

# Nordea CSV Bank Statement Ingestion

## Problem Statement

The monthly tracker workbook updater currently supports Nordea PDF statements, but the PDF statement often exposes card purchases as opaque `NordeaPay køb` rows with long transaction identifiers instead of useful merchant names. This causes most transactions to become `unmatched` and review-required even though a richer Nordea CSV export is available.

The CSV export contains merchant-like `Name` and `Title` fields such as `FOETEX SCANNGO`, `NETTO SCANNGO`, `APPLE.COM/BILL`, `CBB MOBIL`, and `MobilePay Rejsekort`. The updater should use this richer bank cashflow evidence while preserving all existing workbook safety rules.

## Solution

Add Nordea CSV as the preferred bank statement source for monthly cashflow runs. The CSV parser should normalize rows into the existing transaction model, using merchant-rich text for categorization and keeping raw CSV fields available for audit. PDF parsing remains supported as a fallback/legacy source.

The monthly CLI should support explicit or automatic statement-format selection. Reports and audit logs should show which bank statement parser was used so the source quality is visible.

## User Stories

1. As the tracker owner, I want to use my Nordea CSV export for monthly bank cashflow, so that the updater sees actual merchant names.
2. As the tracker owner, I want PDF statement support to remain available, so that older workflows still work.
3. As the tracker owner, I want `.csv` inputs to route to the CSV parser by default, so that normal usage is simple.
4. As the tracker owner, I want an explicit statement-format option, so that I can override automatic routing when needed.
5. As the tracker owner, I want CSV rows normalized into the same transaction model as PDF rows, so that categorization and workbook planning continue to use one pipeline.
6. As the tracker owner, I want `Name` and `Title` interpreted safely, so that generic provider labels like `Vipps MobilePay` do not collapse different merchants into one identity.
7. As the tracker owner, I want account numbers excluded from categorization text, so that private metadata does not pollute rules or category memory.
8. As the tracker owner, I want raw CSV fields retained for audit, so that I can trace a normalized transaction back to source evidence.
9. As the tracker owner, I want CSV currency validation, so that non-DKK or mixed-currency rows do not silently enter a DKK workbook run.
10. As the tracker owner, I want strict reporting-month validation to remain, so that an exported range cannot be accidentally applied to the wrong workbook month.
11. As the tracker owner, I want negative `MASTERCARD` rows mapped to `Nordea Credit Card`, so that debt payments are represented in the workbook liability field.
12. As the tracker owner, I want positive `MASTERCARD` rows mapped to `Mastercard refund`, so that card refunds are cashflow and not liability payments.
13. As the tracker owner, I want `Mastercard refund` available as a configured category, so that these rows have a clear target concept.
14. As the tracker owner, I want better merchant descriptions to improve existing keyword and historical categorization, so that fewer transactions require manual review.
15. As the tracker owner, I want real CSV data kept out of git, so that sensitive account, balance, salary, and merchant data remain private.
16. As a developer, I want synthetic or redacted CSV fixtures that mirror the Nordea export shape, so that parser behavior is testable without private data.
17. As a developer, I want reports and audit logs to include the parser name, so that source quality problems are diagnosable.
18. As a developer, I want this change scoped to Nordea bank transaction CSVs, so that generic bank CSV and investment PDF ingestion remain separate.

## Implementation Decisions

- Add a Nordea CSV parser beside the existing Nordea PDF parser.
- Keep the existing normalized transaction model as the bank cashflow contract.
- Treat Nordea CSV as the preferred bank statement source for bank cashflow.
- Keep PDF parser support as fallback/legacy input.
- Add statement-format routing with `auto`, `nordea-csv`, and `nordea-pdf` modes.
- Keep the existing `--statement` CLI argument for this slice; defer `--bank-statement` and `--investment-statement` naming to combined evidence work.
- Normalize CSV dates from the export's `YYYY/MM/DD` booking date format.
- Normalize CSV amounts and balances from Danish decimal strings.
- Validate every CSV row has the expected statement currency.
- Preserve strict target-period validation in the pipeline rather than silently filtering parser output.
- Choose transaction description from merchant-useful CSV fields:
  - prefer `Name` when it is present and not a generic provider label,
  - fall back to `Title`,
  - keep raw `Name`, `Title`, `Sender`, `Recipient`, `Balance`, and `Reconciled` evidence in transaction details.
- Do not use `Sender` or `Recipient` account numbers for categorization or category memory.
- Preserve existing workbook write safety: richer CSV evidence may improve categorization, but must not loosen formula, manual value, fixed row, confidence, period, or commit-to-copy safeguards.
- Add `Mastercard refund` as a configured category.
- Add deterministic category behavior for Mastercard rows:
  - negative `MASTERCARD` bank transactions map to `Nordea Credit Card`,
  - positive `MASTERCARD` bank transactions map to `Mastercard refund`.
- Keep actual local CSV files ignored and out of committed tests.
- Use synthetic or redacted CSV fixtures that mirror the Nordea export shape.
- Do not implement investment statement PDF parsing in this PRD.
- Do not implement generic bank CSV support in this PRD.
- Do not change the category-memory learning workflow in this PRD.

## Testing Decisions

- Tests should verify public behavior through parser, pipeline, CLI, reporting, and categorization interfaces rather than private helpers.
- Parser tests should use a synthetic/redacted Nordea CSV fixture with the real header shape, semicolon delimiter, UTF-8 BOM tolerance, Danish decimals, and representative rows.
- Routing tests should prove `.csv` uses Nordea CSV and `.pdf` can still use Nordea PDF.
- CLI tests should cover `--statement-format auto`, `nordea-csv`, and invalid/unsupported format behavior.
- Categorization tests should cover merchant-rich CSV descriptions, generic MobilePay name fallback to title, negative Mastercard liability mapping, and positive Mastercard refund mapping.
- Reporting/audit tests should cover parser/source metadata.
- Local smoke validation may use the user's real ignored CSV, but committed tests must not contain real financial data.

## Out of Scope

- Generic bank CSV ingestion.
- Investment account statement PDF parsing.
- Combined bank plus investment monthly evidence.
- New review UI.
- New category-memory workflow.
- LLM categorization.
- Relaxing workbook write safety.
- Committing the real Nordea CSV.

## Further Notes

This PRD was created after discovering that the wrong PDF statement source caused most April 2026 transactions to be unmatched. The provided local CSV contains the same month but includes merchant evidence that the PDF output did not expose.
