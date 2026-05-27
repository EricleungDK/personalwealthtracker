# Architecture

Last updated: 2026-05-27

## Runtime Flow

1. CLI receives tracker path, Nordea statement path, target year/month, config directory, output directory, statement-format selection, and optional commit flag.
2. Config is loaded from YAML files in `config/`.
3. `pipeline.py` routes the bank statement by `--statement-format`: `auto` infers `.csv` as `nordea-csv` and `.pdf` as `nordea-pdf`; explicit modes override extension inference.
4. `nordea_csv.py` parses Nordea CSV exports into normalized bank transactions using merchant-rich fields for categorization and raw CSV fields for audit.
5. `nordea_pdf.py` remains available as a fallback/legacy parser for Nordea PDFs with embedded text.
6. The statement currency is validated against config before transactions are normalized.
7. `categorizer.py` applies Category Memory first, then historical mappings, recurring amount/date rules, and keyword rules.
8. The pipeline rejects statements containing transactions outside the requested target month.
9. Refunds are assigned to the reporting month where they appear; prior workbook periods are not reopened automatically.
10. Deterministic reimbursement/claim matches can map to existing workbook rows such as `Expense claims`; no separate offset model is introduced.
11. Reviewed monthly decisions, when supplied, override categorization by exact transaction ID.
12. Reviewed new leaf category requests validate against the YAML category registry and may update `config/categories.yaml` before workbook planning.
13. `workbook.py` locates the `Net worth` sheet, target month column, and category rows.
14. `workbook.py` plans missing registered leaf rows as structure changes and can insert them into a copied workbook only when placement, sibling formatting, and parent formulas are safe.
15. `reporting.py` writes report, audit, categorized CSV, review CSV, and review XLSX outputs with the statement parser name.
16. Commit mode creates a backup and writes eligible updates to a copied workbook only.

## Parser Design

Nordea CSV is the preferred bank cashflow source because the export includes merchant-like fields that improve deterministic categorization. The CSV parser uses the export header shape, semicolon delimiter, Danish decimal strings, and DKK row currency validation.

The Nordea PDF parser uses header anchors rather than fixed absolute coordinates. This handles the observed difference between the first page and continuation pages while staying specific to the known Nordea statement layout.

The PDF parser assumes the PDF has embedded selectable text. Scanned PDFs and OCR are excluded from MVP 1.

Both bank statement parsers reject non-DKK input for MVP 1. The PDF parser rejects statements without the expected `Valuta` marker and stops collecting continuation rows when Nordea footer/legal text appears after the transaction table.

## Safety Design

The YAML category registry classifies workbook labels as parent/section rows, leaf category rows, or derived rows. Parent/section rows organize the workbook and may allow reviewed child creation. Leaf category rows are the valid targets for transaction categorization, workbook value planning, and Category Memory learning. Derived rows can appear in context and reports but are not direct write targets.

Workbook updates are planned before writing. A planned value update becomes writable only when:

- the category row exists,
- the category is a leaf category in the registry or otherwise allowed by compatibility rules,
- the target month column exists,
- all source transactions are high-confidence,
- all parsed transactions belong to the requested target month,
- the statement currency matches the configured tracker currency,
- the category is not a protected fixed row,
- the target cell is empty,
- the target cell is not a formula.
- all included transactions have high-confidence deterministic category matches.

Reviewed `new_parent_category` and `new_leaf_category` values create a category-registry update, not a financial workbook value write. If the new leaf is missing from the workbook, dry-run reports an `insert_leaf_category` structure change. Commit mode applies that structure change only to a copied workbook and blocks ambiguous parent formula updates.

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
- Category memory is a private local store under `data/category_memory/`, populated only from confirmed review decisions and kept separate from `config/rules.local.yaml`; one confirmed decision can become a deterministic future match, but automatic workbook writes still require all writer safeguards.
- Category Memory learning validates targets against YAML leaf categories and skips parent, derived, missing, or non-leaf labels.
- The learning workflow is a separate CLI path that imports a reviewed decision file into category memory, rather than prompting during monthly dry-run or commit execution.
- Commit mode should not import category memory in the same command; changed category memory should be validated through a later dry run before workbook writing.
- Proxy split rules can be introduced as a deterministic categorization step for one source transaction that needs multiple category allocations. Concrete personal rules should be read from ignored local config, while tracked code validates that allocation targets are registry leaf categories, that the source amount covers all fixed allocations before splitting, and that recurring monthly split limits are not exceeded.
- Bank API ingestion can feed the same normalized transaction model.
- Local LLM classification can be added as an explicit opt-in review-assistance step for unmatched transactions and low-confidence deterministic suggestions that already require review.
- Future Local LLM Mode should integrate with Ollama through its local HTTP API rather than shelling out to `ollama run`, so provider calls can be mocked, timed out, and validated as structured review-only suggestions.
- Local LLM provider failures, timeouts, unavailable models, and invalid structured responses should not fail the monthly planning run. The run should keep the original deterministic or unmatched review state and report a warning.
- The first local Gemma provider target should be configured for the user's Apple Silicon M1 16 GB machine with `gemma4:e4b` as the default model and `gemma4:e2b` as the fallback model if performance is unacceptable.
- Google Drive integration can wrap workbook download/upload while preserving the same writer safeguards.
