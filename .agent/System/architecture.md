# Architecture

Last updated: 2026-09-27

## Runtime Flow

Entry points (`cli.py`): `wealth-tracker monthly` (default operator path, `pipeline.run_monthly`) and the per-month flags command (`--tracker --statement --year --month`, `pipeline.run_pipeline`). `monthly` picks the newest CSV in `data/raw_statements/`, infers the month from row dates, reuses `reports/review_required_<year>_<mon>.xlsx` as decisions when present, always asks the local Consensus, and commits unless `--dry-run`.

1. Config is loaded from YAML files in `config/` (`config.py`), including the category registry, `trust_policy`, and `local_llm` settings.
2. `statement_adapters.py` routes the bank statement by `--statement-format`: `auto` infers `.csv` as `nordea-csv` and `.pdf` as `nordea-pdf`; explicit modes override extension inference. Currency and target month are validated here; out-of-period rows block the run.
3. `nordea_csv.py` parses Nordea CSV exports (both date formats) into normalized bank transactions using merchant-rich fields for categorization and raw CSV fields for audit.
4. `nordea_pdf.py` remains available as a fallback/legacy parser for Nordea PDFs with embedded text.
5. `categorizer.py` applies private proxy split rules to matching transfers, then per row Category Memory first, Guidance Aliases (`config/guidance_aliases.local.yaml`), historical mappings, recurring amount/date rules, and keyword rules.
6. Refunds are assigned to the reporting month where they appear; prior workbook periods are not reopened automatically.
7. Deterministic reimbursement/claim matches can map to existing workbook rows such as `Expense claims`; no separate offset model is introduced.
8. Reviewed monthly decisions (the Exception Sheet, or `--review-decisions`) override categorization by exact transaction ID (`review_decisions.py`).
9. Local model suggestions go through the Suggester port (`suggester.py`); `ConsensusSuggester` asks two local Ollama models (`local_llm.py`) and records their votes (ADR 0002).
10. `trust_policy.py` stamps each row `auto` or `review` with a reason (ADR 0001), re-stamped after decisions and votes.
11. Reviewed new leaf category requests validate against the YAML category registry and are registered in memory for workbook planning; `config/categories.yaml` gains them (minimal text insert with a description) only after the month commit succeeds (issue #19).
12. `workbook.py` locates the `Net worth` sheet, target month column, and category rows, and plans value updates.
13. `workbook.py` plans missing registered leaf rows at the end of their parent SUM section; `row_insertion.py` inserts them formula-aware and fails closed on a structural and numeric before/after check (ADR 0006).
14. `reporting.py` writes report, JSONL audit, categorized CSV, review CSV, and the Exception Sheet XLSX (`Review Required` + `Audit`); `monthly` rewrites one sheet per month with decisions carried forward (issue #20).
15. Atomic Month Commit (ADR 0003): only when zero rows are in review, commit creates a backup, writes eligible updates to a copied workbook under `data/processed/`, persists new leaves, and learns Category Memory with provenance (`category_memory.py`, ADR 0004). Otherwise nothing is written besides outputs.

Supporting modules: `setup_workspace.py` (`setup`), `template_workbook.py` (`template-workbook`), `statement_import_assistant.py` (`import-statement`, untrusted unknown formats), `importer_profiles.py` (`importer-profile`), `cleanup.py` (`cleanup-currency-labels`), `outbound_redaction.py` (unused hosted allowlist, ADR 0005), `models.py`, `utils.py`.

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
- all source transactions have `auto` authority from the Trust Policy,
- all parsed transactions belong to the requested target month,
- the statement currency matches the configured tracker currency,
- the category is not a protected fixed row,
- the target cell is empty,
- the target cell is not a formula.

Reviewed `new_parent_category` and `new_leaf_category` values create a category-registry update, not a financial workbook value write. If the new leaf is missing from the workbook, dry-run reports an `insert_leaf_category` structure change. Planning applies structure changes in order to the in-memory workbook so update rows are final; commit replays them only on a copied workbook. Unsupported parent formula shapes or a failed safety check keep the change in review.

Commit mode writes only planned updates whose action is `write`, and only when no row or update is in review (Atomic Month Commit).

## Future Extension Points

- Additional statement parsers can be added as Trusted Statement Adapters beside `nordea_csv.py` and `nordea_pdf.py`.
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
- Category memory is a private local store under `data/category_memory/`, kept separate from `config/rules.local.yaml`. It is learned on a successful month commit (dry run writes none): human decisions as `human`, consensus results as `auto`, which categorise only after two consistent committed months (ADR 0004). Automatic workbook writes still require all writer safeguards.
- Category Memory learning validates targets against YAML leaf categories and skips parent, derived, missing, or non-leaf labels.
- `learn-category-memory` remains a separate manual import path for reviewed workbooks.
- Proxy split rules can be introduced as a deterministic categorization step for one source transaction that needs multiple category allocations. Concrete personal rules should be read from ignored local config, while tracked code validates that allocation targets are registry leaf categories, that the source amount covers all fixed allocations before splitting, and that recurring monthly split limits are not exceeded.
- Bank API ingestion can feed the same normalized transaction model.
- Local LLM classification runs on every `monthly` run and with `--local-llm-suggestions` on the per-month command, for unmatched transactions and low-confidence deterministic suggestions; high-confidence deterministic matches are not replaced.
- Local LLM Mode integrates with Ollama through its local HTTP API rather than shelling out to `ollama run`, so provider calls can be mocked, timed out, and validated as structured suggestions whose authority the Trust Policy decides.
- Local LLM provider failures, timeouts, unavailable models, and invalid structured responses should not fail the monthly planning run. The run should keep the original deterministic or unmatched review state and report a warning.
- Local LLM Mode runs Consensus: `gemma4:26b` (`model`) and `gemma4:12b` (`second_model`) each vote per row, with installed `qwen3:14b` as either voter's fallback model (ADR 0002). Category models sit behind the Suggester port; the Ollama adapter uses the chat API with a JSON schema of enum leaves plus `NONE`, temperature 0, keep-alive, and a 180-second cold-start timeout, and may retry the fallback model for a row when the primary model times out or fails.
- Google Drive integration can wrap workbook download/upload while preserving the same writer safeguards.
