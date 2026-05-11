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
- Treat populated tracker workbook cells as authoritative and report conflicting statement totals for review instead of overwriting them.
- Use bank statements as evidence for cashflow rows, not asset value rows.
- Use investment statement month-end market values for asset value rows when investment ingestion is added.
- Exclude internal transfers from generic income and expense totals unless a rule intentionally maps the transfer to a specific tracker cashflow row.
- Treat credit card settlement payments as liability movement rather than expense evidence.
- Use Nordea bank statement salary deposits for net salary income only; preserve workbook formula/manual logic for tax and labour market contribution rows.
- Allow matched Nordea salary deposits to update `Full-time job (net)` when workbook safety checks pass.
- If multiple salary-like deposits match in one reporting month, sum them for reporting but require review before writing.
- Never write `Income (net)` directly; preserve it as a derived workbook row.
- Never write section total rows directly; write only source-backed leaf workbook rows and preserve workbook aggregation logic.
- Leave pre-filled recurring workbook values untouched; use observed payments to confirm or flag differences for review.
- Allow automatic writes only for high-confidence deterministic category matches; fuzzy, unmatched, or ambiguous transactions remain review-only.
- Net same-month refunds against deterministic matched expense categories; keep unmatched or vague refunds review-only.
- Record later-month refunds in the reporting month where they appear; do not automatically reopen or revise prior workbook periods.
- Keep reimbursement handling aligned to existing workbook rows; map deterministic claims to `Expense claims` without adding a separate offset model.
- Support future auto-learning from confirmed review decisions only; do not learn new rules from unconfirmed automatic matches.
- Store learned category memory separately from hand-written local rules, under ignored private generated data.
- Treat one confirmed review decision as enough to create review-free future category memory matches, while preserving workbook write safeguards.
- Add future learning through a separate command that imports a reviewed decision file into category memory.
- Keep category-memory learning separate from workbook commit mode; require a new dry-run review before committing changed categorization.

## Out Of Scope For MVP 1

- OCR and scanned PDFs.
- Generic PDF table parsing across banks.
- Google Drive read/write.
- Bank API or Open Banking ingestion.
- Scheduler and monthly notifications.
- LLM categorization.
- Budget threshold alerts.
- Live FX conversion.
- Investment statement ingestion for asset value rows.
- Crypto or other digital asset valuation without a dedicated source.
- Generic multi-bank statement ingestion.

## Success Criteria

- The agent can parse the provided Nordea statement layout without using OCR.
- DKK booked amounts are used as the source of truth.
- Tracker workbook currency labels and assumptions should align to DKK.
- Workbook label cleanup should be handled as a separate one-off task, not during monthly update runs.
- Future writer support should create missing month/year period columns safely, preserving workbook formulas, formatting, headers, and structure.
- Dry-run output must clearly report planned period-column creation before commit mode performs it.
- New period columns should copy formulas and formatting from the immediately previous period column, with the copy source reported in dry-run output.
- Missing year creation should add a full 12-month year block when the existing workbook pattern can be confidently detected.
- New period/year creation should preserve formulas, styles, widths, and structure while clearing ordinary copied manual values.
- New period/year creation may retain copied non-formula values only for explicitly configured carry-forward recurring rows.
- Carry-forward recurring rows should be configured separately from fixed/protected rows.
- Statements with mismatched currency or mismatched transaction periods fail before workbook planning.
- Low-confidence, unmatched, fixed-row, formula, and manual-value conflicts are flagged instead of overwritten.
- The original workbook is never modified directly.
- Sensitive financial files are ignored by default.
- Near-term bank-side ingestion remains Nordea-only until a new bank source is explicitly introduced.
- Future monthly planning should combine Nordea cashflow evidence and investment account valuation evidence into one proposed update set for the reporting month.
- Report cross-source mismatches between Nordea cashflow and investment account evidence instead of automatically reconciling or overriding one source with the other.
- Convert USD investment statement values to DKK using a user-maintained fixed conversion rate when investment statement support is added.
- Record the applied conversion rate in monthly reports and audit logs.
- Do not write conversion-rate metadata into the tracker workbook unless the workbook structure is explicitly changed later.
- Update individual investment asset rows only from explicit holding-level values; use total-only investment values only for mapped total rows or review.
- Keep crypto and other digital asset rows out of scope until a dedicated valuation source is introduced.
