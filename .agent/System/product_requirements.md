# Product Requirements

Last updated: 2026-05-07

## Goal

Build a local-first automation agent that reduces monthly manual entry in the existing personal wealth tracker workbook.

The MVP processes a Nordea account statement PDF, maps transactions to the existing tracker categories, and produces reviewable outputs before writing anything.

## MVP 1 Scope

- Parse a Nordea `Kontoudskrift` PDF with embedded text.
- Normalize transaction date, interest date, description, DKK amount, direction, balance, and optional original foreign amount metadata.
- Categorize transactions using historical mappings, recurring amount/date rules, and keyword rules.
- Aggregate transaction amounts into existing tracker category rows.
- Detect the target year/month column in the `Net worth` sheet.
- Generate a Markdown report, JSONL audit log, categorized transaction CSV, and review-required CSV.
- Reject non-DKK statements and statements containing transactions outside the requested reporting month.
- Dry-run by default.
- In commit mode, write only eligible values to a copied workbook.

## Out Of Scope For MVP 1

- OCR and scanned PDFs.
- Generic PDF table parsing across banks.
- Google Drive read/write.
- Bank API or Open Banking ingestion.
- Scheduler and monthly notifications.
- LLM categorization.
- Budget threshold alerts.
- FX conversion.

## Success Criteria

- The agent can parse the provided Nordea statement layout without using OCR.
- DKK booked amounts are used as the source of truth.
- Statements with mismatched currency or mismatched transaction periods fail before workbook planning.
- Low-confidence, unmatched, fixed-row, formula, and manual-value conflicts are flagged instead of overwritten.
- The original workbook is never modified directly.
- Sensitive financial files are ignored by default.
