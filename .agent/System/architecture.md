# Architecture

Last updated: 2026-05-07

## Runtime Flow

1. CLI receives tracker path, Nordea PDF path, target year/month, config directory, output directory, and optional commit flag.
2. Config is loaded from YAML files in `config/`.
3. `nordea_pdf.py` extracts text with coordinates from the Nordea PDF and reconstructs transaction rows from the `Dato`, `Rentedato`, `Detaljer`, `Beløb`, and `Saldo` columns.
4. The statement currency is validated against config before transactions are normalized.
5. `categorizer.py` applies historical mappings first, then recurring amount/date rules, then keyword rules.
6. The pipeline rejects statements containing transactions outside the requested target month.
7. Refunds are assigned to the reporting month where they appear; prior workbook periods are not reopened automatically.
8. Deterministic reimbursement/claim matches can map to existing workbook rows such as `Expense claims`; no separate offset model is introduced.
9. `workbook.py` locates the `Net worth` sheet, target month column, and category rows.
10. `reporting.py` writes report, audit, categorized CSV, and review CSV outputs.
11. Commit mode creates a backup and writes eligible updates to a copied workbook only.

## Parser Design

The Nordea parser uses header anchors rather than fixed absolute coordinates. This handles the observed difference between the first page and continuation pages while staying specific to the known Nordea statement layout.

The parser assumes the PDF has embedded selectable text. Scanned PDFs and OCR are excluded from MVP 1.

The parser rejects statements without the expected `Valuta` marker, rejects non-DKK statements for MVP 1, and stops collecting continuation rows when Nordea footer/legal text appears after the transaction table.

## Safety Design

Workbook updates are planned before writing. A planned update becomes writable only when:

- the category row exists,
- the target month column exists,
- all source transactions are high-confidence,
- all parsed transactions belong to the requested target month,
- the statement currency matches the configured tracker currency,
- the category is not a protected fixed row,
- the target cell is empty,
- the target cell is not a formula.
- all included transactions have high-confidence deterministic category matches.

Commit mode writes only planned updates whose action is `write`.

## Future Extension Points

- Additional statement parsers can be added beside `nordea_pdf.py`.
- Investment account statement ingestion should use a separate contract for asset values or holdings rather than reusing Nordea bank transaction semantics.
- Payroll/tax workbook rows should preserve existing formulas or manual workbook logic rather than infer payroll breakdowns from Nordea salary deposits.
- Salary categorization may plan writes to `Full-time job (net)` from matched Nordea net salary deposits, but must not overwrite formulas/manual values or write derived payroll/tax rows.
- Salary planning should flag multiple salary-like deposits in one reporting month as review-only even when the aggregate amount is calculated.
- Workbook planning should classify `Income (net)` as derived/formula-owned and exclude it from direct write targets.
- Workbook planning should classify section totals as derived/formula-owned and exclude them from direct write targets.
- A future monthly planning run should accept both Nordea bank statement input and investment account statement input, normalize them into separate evidence models, then combine them at workbook planning/reporting time.
- Investment valuation planning should convert USD values to DKK using a configured fixed conversion rate and include the applied rate in reports/audit logs for each reporting month.
- Workbook writing should use the converted DKK value only; conversion-rate metadata belongs in reports/audit logs for now.
- Workbook cleanup tasks such as currency label correction should remain separate from monthly planning and commit mode.
- Missing period-column creation should be a dedicated writer capability with tests for formulas, formatting, merged year headers, and section structure preservation.
- Period-column creation should be planned and reported in dry-run before commit mode applies the structure change to a copied workbook.
- Period-column creation should copy formulas, styles, widths, and relevant structure from the immediately previous period column and report that source in dry-run.
- Year-block creation should copy the prior year/month structure as a full 12-month block only when headers and period layout are unambiguous; otherwise the dry-run should stop for review.
- Period/year creation should clear ordinary copied non-formula values while preserving formulas, styles, widths, merged headers, and other required structure.
- Period/year creation should retain copied non-formula values only for configured carry-forward recurring rows; the writer should not infer those rows from previous values alone.
- Writer configuration should separate protected fixed rows from carry-forward recurring rows because they grant different permissions.
- Investment workbook planning should map explicit holding values to individual asset rows; total-only values require a configured total row or review.
- Digital asset rows should not be automated from bank or investment account statements unless a future dedicated valuation source is added.
- Cross-source checks should report mismatches between related cashflow and investment evidence without changing the authority of either source outside its own evidence type.
- Category memory can be added as a private local store under `data/category_memory/`, populated only from confirmed review decisions and kept separate from `config/rules.local.yaml`; one confirmed decision can become a deterministic future match, but automatic workbook writes still require all writer safeguards.
- The learning workflow should be a separate CLI path that imports a reviewed decision file into category memory, rather than prompting during monthly dry-run or commit execution.
- Commit mode should not import reviewed decisions in the same command; changed category memory should be validated through a later dry run before workbook writing.
- Bank API ingestion can feed the same normalized transaction model.
- Local LLM classification can be added after deterministic rules fail.
- Google Drive integration can wrap workbook download/upload while preserving the same writer safeguards.
