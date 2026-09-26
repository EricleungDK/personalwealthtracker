# Data Contracts

Last updated: 2026-09-26

## Template Workbook Metadata

A public Template Workbook must include a hidden `Template Metadata` sheet with:

- `template_id`: `local-wealth-tracker-template`.
- `template_version`: the supported public template version, initially `1.0`.
- `workbook_kind`: `synthetic_template`.
- `tracker_currency`: the template's default Tracker Currency.
- `template_schema`: the workbook schema identifier, initially `net-worth-v1`.

Template validation must reject workbooks with missing metadata, unsupported template IDs, unsupported versions, unsupported workbook kinds, or unsupported template schemas before treating them as public package templates.

The v1 synthetic template uses the `Net worth` sheet, category labels in column `B`, year headers in row `2`, month headers in row `3`, and a Jan-Dec month block. It contains generic section labels, generic leaf rows such as `Groceries (monthly)`, formulas for parent/derived rows, and no private workbook values or personal categories.

Supported v1 customization is limited to known template dimensions: renaming existing category labels, renaming existing section labels, changing the Tracker Currency in visible cells and hidden metadata, setup profile path overrides for known private local paths, and period columns created by the workbook planner. Template customization must reject unsupported formula changes, arbitrary layout edits, missing metadata, unknown labels, duplicate labels, blank labels, and unsupported template versions instead of attempting spreadsheet repair.

## Transaction

Normalized statement row:

- `transaction_id`: deterministic hash from date, amount, description, and row order.
- `date`: booked date.
- `interest_date`: Nordea `Rentedato`, when available.
- `description`: categorization text from the statement parser. Nordea CSV prefers merchant-useful `Name` values and falls back to `Title`; Nordea PDF uses merged detail text.
- `amount`: booked DKK amount.
- `currency`: `DKK` for MVP 1.
- `direction`: `income` for non-negative amounts, `expense` for negative amounts.
- `balance`: statement balance after transaction, when available.
- `original_amount` and `original_currency`: optional metadata when a foreign card transaction line exposes the original amount.

Nordea CSV transactions may include raw source details such as `Name`, `Title`, `Sender`, `Recipient`, `Balance`, and `Reconciled` for audit. Account-number fields are retained only as source details and must not become categorization text or category-memory keys.

## Trusted Statement Adapter

A Trusted Statement Adapter wraps a deterministic known-format parser and returns a trusted import result for monthly planning. The adapter result records:

- `adapter_name`: public adapter name such as `nordea-csv` or `nordea-pdf`.
- `parser_identity`: parser identity written to reports and audit outputs.
- `source_statement`: local source path.
- `transactions`: normalized `Transaction` records.
- `diagnostics`: import diagnostics with `severity`, `code`, and `message`.

The normalized transaction fields required from trusted adapters are `transaction_id`, `date`, `amount`, `currency`, `description`, `direction`, and `source_file`. Additional fields such as balance, merchant, original amount/currency, and raw source details may be present when the deterministic parser can provide them.

Adapter diagnostics use `unsupported_currency`, `out_of_period`, `duplicate_row`, or `adapter_failure` for known v1 cases. Unsupported currencies and out-of-period transactions are error diagnostics and block monthly planning. Duplicate normalized rows are warning diagnostics because repeated rows may be legitimate but should be visible to review and audit flows.

## Statement Import Assistant

The Statement Import Assistant is for unknown statement formats. Its output is an untrusted review artifact, not monthly planning evidence. The first v1 artifact is `untrusted_import_review_<year>_<month>.csv` with:

- `review_required`: always `yes` for imported unknown-format rows.
- `eligible_for_workbook_write`: always `no` until a later confirmed-import workflow promotes reviewed data.
- `source_row`: source row or model-reported row number.
- `date`: model-assisted or blank date candidate.
- `amount`: model-assisted or blank amount candidate.
- `currency`: model-assisted or fallback tracker currency candidate.
- `description`: raw row or model-assisted description candidate.
- `direction`: model-assisted `income` or `expense` candidate.
- `provenance`: `deterministic_raw_row` or `model_assisted_untrusted`.
- `confidence`: extraction confidence, not write confidence.
- `suggested_category`: Educated Import Guess from a local Importer Profile, if one matched.
- `guess_state`: `high_confidence`, `low_confidence`, or blank.
- `guess_confidence`: confidence for the Importer Profile guess, not write confidence.
- `guess_reason`: review-facing explanation for why the profile guessed this category.
- `guess_profile`: local Importer Profile name that produced the guess.
- `source_format_changed`: `yes` when source layout diagnostics detected a changed format.
- `validation_warnings`: `|`-separated validation warnings.
- `confirmed`: blank review column for the user to confirm a row.
- `confirmed_category`: blank review column for the user to accept or correct a suggested category.

Validation diagnostics include `missing_date`, `invalid_amount`, `unsupported_currency`, `duplicate_row`, `changed_layout`, `out_of_period`, `missing_direction`, `provider_unavailable`, and `provider_failure`. Missing or invalid fields and out-of-period rows remain visible in the review artifact. Local model assistance is optional; if unavailable or invalid, the assistant falls back to deterministic raw-row review output.

No Statement Import Assistant output may directly create workbook write permission, Category Memory, or an Importer Profile. Later confirmed-import workflows may decide how reviewed rows become trusted evidence.

## Importer Profiles

Importer Profiles are private local JSON files under `data/importer_profiles/` by default. They are created only from confirmed unknown-import review rows, not raw model suggestions. The v1 profile stores:

- `profile_version`: profile schema version.
- `profile_name`: local profile name.
- `source_identity`: reviewed artifact name, artifact schema, and a header fingerprint.
- `field_mappings`: reviewed field names for date, amount, currency, description, and direction.
- `validation_assumptions`: tracker currency, required fields, and validation warning types observed during reviewed imports.
- `confirmed_import_count`: number of confirmed rows learned into the profile.
- `category_decisions`: normalized description identities, confirmed categories, source row references, and decision counts.

Importer Profiles must not store raw statement dumps. Profile export is explicit through the importer-profile export workflow; public packages may ship only synthetic/demo profiles.

Educated Import Guesses from Importer Profiles are review hints. High-confidence guesses are filterable with `guess_state=high_confidence`; low-confidence guesses remain `guess_state=low_confidence`. Changed layouts, unsupported currencies, invalid fields, duplicates, and out-of-period rows keep validation warnings visible and cap profile guesses to low confidence.

## CategorizedTransaction

- `transaction`: normalized transaction.
- `suggested_category`: existing tracker row category or null.
- `confidence`: deterministic confidence score.
- `categorization_method`: `category_memory`, `guidance_alias`, `historical`, `recurring`, `rule`, `monthly_review_decision`, model methods such as `local_llm_gemma`, or `unmatched`.
- `reason`: human-readable explanation for report and audit.
- `votes`: model votes (category or null, confidence, source model) behind a model suggestion.
- `alternatives`: other leaves the Suggester offered for the row; feed the Exception Sheet dropdown.
- `authority`: `auto` or `review`, decided once per row by the Trust Policy (`trust_policy.py`). `review` rows must not be auto-written. `review_required` is derived from it.
- `authority_reason`: one-line Trust Policy reason, shown as `reason` in the `Audit` sheet.

Trust Policy rules, in order: rows not from a Trusted Statement Adapter are `review`; Monthly Review Decisions are `auto`; proxy split sources are `auto` (excluded from totals); rows without a category, with a Subscription Leaf Proposal, in `never_auto_categories`, or above `auto_max_amount` are `review`; model rows need `min_agreement` agreeing votes; deterministic rows need confidence at or above `confidence_thresholds.auto_write`. Thresholds live under `trust_policy` in `config/settings.yaml` (defaults: `auto_max_amount` 1000, `min_agreement` 2, `never_auto_categories` Rent, Mom, Dad, both insurances, the three investment leaves, salary). See `docs/adr/0001-per-row-authority.md`.

Future Local LLM Mode should reuse the existing suggestion fields rather than widening the primary review queue. A local model suggestion may populate `suggested_category`, `categorization_method`, `confidence`, `reason`, and `votes`; the Trust Policy keeps it `review` until `min_agreement` votes agree (a single local model never does), and it is not a confirmed decision until the operator fills `manual_category` or the reviewed new-leaf fields. Local LLM Mode may assist unmatched transactions and low-confidence deterministic suggestions that already require review; high-confidence deterministic matches should not be replaced by model output.

## Local LLM Suggestion Contract

Category models sit behind the Suggester port (`suggester.py`): `suggest(rows, context) -> suggestions`. Context carries the leaf glossary (`description:` per leaf), guidance aliases, up to five Category Memory neighbours by normalised merchant identity, and reviewed policy text. The Ollama row prompt shows the raw statement merchant text (`merchant`); normalised identity stays the lookup key. Adapters: `OllamaSuggester` (`local_llm.py`), `FakeSuggester` (scripted votes for tests), and `ConsensusSuggester` (two Suggesters; `local_consensus(settings)` wires `model` and `second_model`). Each suggestion carries:

- `transaction_id`: row the suggestion is for.
- `category`: an existing YAML Leaf Category Row, a Subscription Leaf Proposal `<Service> subscription`, or NONE (no suggestion).
- `new_leaf_parent`: `Services` when `category` is a Subscription Leaf Proposal, else blank. A proposed service that already names a leaf (`Apple Cloud`, or `Claude` once `Claude subscription` exists) returns that leaf instead.
- `confidence`: `0.0` to `1.0`. Category answers whose highest vote is below the configured review threshold are ignored and counted as low-confidence responses so weak guesses do not populate review suggestion fields.
- `alternatives`: other leaves the model considered; enum-constrained in the schema, non-leaf values dropped.
- `evidence`: short review-facing reason, used in the `reason` field.
- `source`: model that answered.
- `failure`: blank, `invalid_response`, or `provider_failure`.
- `votes`: Consensus only; one `Vote` per answering voter. Off-leaf answers count as NONE; the suggestion is the primary voter's leaf, else the second's, else the primary's proposal, else the second's, and other voters' leaves join `alternatives`. An existing leaf always beats a proposal; proposals with the same name after case and whitespace folding vote for the same leaf, a different proposal votes NONE, but a proposal is `review` regardless of agreement.

Each answered suggestion becomes its `votes` (or one `Vote` of category, confidence, source) on the row. Agreement counts distinct vote sources, so one model voting twice is one voter, and the Trust Policy re-stamps the row's authority. Failed and low-confidence suggestions leave the row unchanged.

The Ollama adapter calls `/api/chat` with a system message holding the glossary, a JSON schema `format` whose `category` is an enum of leaves plus `NONE` and `NEW_SUBSCRIPTION` (service named in `new_subscription_service`, validated as up to 40 word characters, spaces and `.+&'-`) and whose `reason` precedes `category`, `think: false`, temperature 0, `keep_alive`, and a 180-second cold-start timeout. If the configured model is not installed it uses the installed fallback model.

Invalid JSON, missing required fields, categories outside the Allowed Category Set, low-confidence category responses, timeouts, unavailable Ollama, or unavailable models should leave the original deterministic or unmatched review state intact and add a report/audit warning instead of failing the monthly run. Provider failures may retry the configured fallback model once for a row before counting as unrecovered provider failures.

## TrackerUpdate

- `year` and `month`: target workbook period.
- `category`: tracker row name.
- `amount`: absolute monthly total for the category.
- `source_transactions`: transaction IDs included in the total.
- `target_row`, `target_column`, `target_cell`: resolved workbook target.
- `existing_value`: current workbook value before writing.
- `write_action`: `write`, `skip`, or `review`.
- `reason`: action explanation.

Direct value updates should target leaf workbook rows only. Derived workbook rows and section totals should appear in reports as skipped or formula-owned when encountered, not as writable targets.

Future period-column creation should be represented separately from value updates so reports can distinguish planned structure changes from financial cell writes. Dry-run output should expose the planned structure change before commit mode applies it.

Leaf-row insertion records (`insert_leaf_category`) carry `parent_category`, `leaf_category`, `source_range` (format source row, the section's last row) and `target_range` (the new row, `parent SUM end + 1`). Rows are numbered for the workbook state after all earlier changes in the list, which commit replays in order. `review` records carry the blocking reason.

Period-column creation records should include the target year/month and the source template period column used for formulas and formatting.

Year-block creation records should include the target year, the 12 period columns to create, and the source year block used as the template.

Structure-change records should distinguish preserved formulas, cleared copied manual values, and any deliberately retained pre-filled values. Retained pre-filled values should identify the configured carry-forward recurring row that allowed the value to remain.

Future writer config should distinguish `fixed_rows` from `carry_forward_rows`: fixed rows block automated overwrites, while carry-forward rows permit retaining copied recurring values during period/year creation.

## Outputs

Every run writes:

- Markdown monthly report.
- JSONL audit log.
- Categorized transaction CSV.
- Review-required CSV.
- Review-required XLSX workbook.

Outputs are ignored because they may contain sensitive transaction data.

Report and audit outputs include the bank statement parser name, such as `nordea-csv` or `nordea-pdf`, so a run can be traced to the source format used.

Reports include a `Category Registry Updates` section. Existing `manual_category` decisions remain monthly review decisions, while validated `new_parent_category` and `new_leaf_category` rows are reported as category registry additions.

Audit logs use `category_registry_addition` records for validated new leaf registrations. These records include the parent category, leaf category, reporting period, source transaction IDs, statement parser, source statement, and target workbook.

## Review Workbook

The manual review workbook contains:

- `Review Required`: the Exception Sheet; only rows in review (`review` authority, or source of a `review` workbook update).
- `Audit`: every `auto` row not in review (a row blocked by its workbook cell is only on `Review Required`) with `category`, `corrected_category` (blank keeps the row; a leaf or `NONE` becomes a Monthly Review Decision on the next `--review-decisions` run), `source` (categorization method), `votes` (`category (model, confidence)`, `;`-joined), `reason` (Trust Policy reason), and `evidence`.
- `Decision Options` (hidden): one column per `Review Required` row holding that row's `manual_category` dropdown list.
- `Category Options` (hidden): workbook/category registry option metadata; dropdown source, read by `learn-category-memory`.
- `Run Metadata` (hidden): reporting period, statement parser, generated timestamp, and transaction ID scheme; read by the decision loaders.

`Audit` shows split columns (`split_role`, `split_rule`, `source_transaction_id`, `allocated_amount`, `residual_amount`) only when one of its rows is a split row.

Review decision columns:

- `manual_category`: current-month decision. Blank accepts `suggested_category`; `NONE` rejects it and leaves the row uncategorised; otherwise an existing tracker workbook label or registered YAML Leaf Category Row. Every row's dropdown lists its suggestion, `alternatives` and voted categories first, then `NONE`, then every leaf; each row's list lives in its own column of the hidden `Decision Options` sheet (no 255-character inline-list cap). Typing a value not in the list is allowed. A Subscription Leaf Proposal is not offered there: `suggested_parent_category` shows `Services`, and a blank row accepts the proposal as a New Leaf Category Request (`new_parent_category` = `suggested_parent_category`, `new_leaf_category` = `suggested_category`). If the YAML leaf is not present in the tracker workbook yet, workbook planning should surface the required row insertion.
- `new_parent_category`: allowed Parent/Section Row for a missing leaf category request.
- `new_leaf_category`: exact display label for the missing Leaf Category Row to add. It is mutually exclusive with `manual_category`.
- `learn_to_memory`: commit learning learns every decided row unless `no`; the manual `learn-category-memory` import learns only `yes`/truthy rows.

The `Review Required` sheet is operator-first. Loaders read columns by header name, so order and optional columns may change. Column order:

- `date`
- `description`
- `amount`
- `suggested_category`
- `suggested_parent_category` (only when a row proposes a new leaf)
- `manual_category` (header note: blank accepts; no suggestion needs a category or `NONE`)
- `reason` (Suggester/rule reason with the categorization method appended in brackets)
- `confidence`
- `new_parent_category`
- `new_leaf_category`
- `learn_to_memory`
- `blocked`: `<target_cell>: <reason>` only when the row's workbook update is `review` (blocks the commit); empty for `write` and `skip`
- `split_role`, `split_rule`, `source_transaction_id`, `allocated_amount`, `residual_amount` (only when a split row is in review)
- `transaction_id` (hidden)

Rows without `suggested_category` sort first, then by date. `merchant_identity` and `direction` are not shown (still in `Audit`).

Older reviewed workbooks remain importable: the pre-#18 layout (`transaction_id` first, with `method`, `workbook_action`, `target_cell`, `workbook_reason`, `merchant_identity` and `direction` columns) and workbooks without `new_parent_category` and `new_leaf_category` (manual category decisions only).

## Category Registry

`config/categories.yaml` is the durable category registry. It supports:

- parent entries with `allow_new_children` and `children`,
- leaf string entries, or leaf mappings with `label` and `description`,
- derived entries that are never direct transaction targets,
- explicit aliases that resolve old or short labels to registry labels.

Parent/Section Row labels group child rows and may allow reviewed new leaf requests. Leaf Category Row labels are the valid targets for `manual_category`, workbook value planning, and Category Memory learning. Derived rows such as workbook totals are allowed as context but not as write or memory targets.

Leaf `description` text forms the leaf glossary (`CategoryRegistry.leaf_glossary`, leaf → description) that the Suggester sees. A leaf without a description maps to an empty string. Adding a leaf does not change the tracker workbook; a missing leaf row is only planned for insertion when a transaction targets it.

The registry rejects duplicate labels using case-insensitive trimmed matching while preserving exact display labels in YAML and reports.

Category Memory learning validates against leaf categories. Learning skips Parent/Section Row labels, derived rows, missing categories, fixed rows, and other non-leaf targets. A reviewed `new_leaf_category` can be learned only after the reviewed second run has added it to the YAML registry, even before the new row has been inserted into the tracker workbook.

## Future Proxy Split Rules

Proxy split rules should live in private local config when they contain personal intermediary names, family labels, or fixed amounts. A proxy split rule should define the transaction trigger, direction, conversion rate, fixed allocations, and whether residual review is required.

Configured allocation targets must be Leaf Category Row labels from the Category Registry. Allocation base amounts are converted to tracker currency with the configured proxy split conversion rate before contributing to monthly statement totals.

Proxy split allocation math should use decimal arithmetic. Each configured allocation is converted and rounded to 2 decimal places before residual calculation. Residual is calculated from the absolute source transaction amount minus the rounded allocation amounts. Residual amounts below 0.01 DKK are treated as zero; negative residual means the proxy split rule does not apply and the transaction remains review-only.

A proxy split transfer whose tracker-currency amount is smaller than the configured allocation total should remain review-only. A transfer that exactly covers the configured allocations should produce only the configured allocation lines. A larger transfer should produce configured allocation lines plus a residual review line tied to the original source transaction.

Residual review decisions apply to the current monthly run only and should not be imported into Category Memory, because the residual represents a leftover allocation rather than a stable merchant identity.

Recurring proxy split rules should support a monthly application limit. The Revolut family split rule should default to at most one automatic application per reporting month, but the private local rule may raise `monthly_limit` when multiple same-month transfers are intentional. Candidates beyond the configured limit should require review instead of auto-splitting all candidates.

Categorized output should preserve the original source transaction as a proxy split source line for audit and should add separate proxy split allocation lines for the configured category allocations. The source line should not directly contribute to workbook totals; allocation lines contribute to their configured categories. If a residual amount exists, a residual review line should be emitted separately.

Proxy split allocation and residual lines should use deterministic IDs derived from the source transaction ID, split rule name, and split role. For example:

- `<source_transaction_id>:split:revolut_family_transfer:dad`
- `<source_transaction_id>:split:revolut_family_transfer:mom`
- `<source_transaction_id>:split:revolut_family_transfer:residual`

Review workbook rows for proxy split allocation and residual lines should expose split context metadata such as source transaction ID, split rule, split role, source amount, allocated amount, and residual amount. These metadata columns support auditability and should be placed so they do not push the primary review decision columns away from the transaction description.

## Future Investment Valuation

Investment statement ingestion should distinguish:

- `month_end_market_value`: the point-in-time value eligible for asset value rows.
- `market_value_currency`: the currency reported by the investment statement, expected to be USD initially.
- `fixed_conversion_rate`: the user-maintained USD-to-DKK rate used for tracker values.
- `applied_conversion_rate`: the exact rate recorded for the reporting month run.
- `tracker_currency_value`: the DKK value after applying the fixed conversion rate.
- `valuation_granularity`: whether the value is for a specific holding or a portfolio/account total.
- `holding_symbol` or `holding_name`: required when the value is holding-level.
- `units` or `shares`: audit metadata, not the value written to net worth rows.
- `contribution_amount`: cash movement eligible for cashflow rows, not asset valuation.

Investment valuation records should remain a separate evidence model from normalized bank transactions. They can be combined with bank transaction evidence during monthly workbook planning, but they should not be forced into the `Transaction` contract.

Cross-source mismatch records should link related evidence from different sources, describe the disagreement, and mark it for review without mutating either source record.

Applied conversion-rate metadata belongs in report and audit contracts, not in workbook update cells, unless a later workbook-structure decision introduces a dedicated place for it.

## Payroll Workbook Logic

Bank statement salary deposits may support net income rows, but they must not be used to infer payroll deduction rows. Payroll deduction rows such as taxes and labour market contribution should preserve existing workbook formulas or manual workbook logic unless a future source is explicitly introduced.

## Category Memory

Learned category memory is stored separately from hand-written local rules, in ignored `data/category_memory/category_memory.json`.

Memory is learned when a month commits. Each mapping has `provenance`: `human` (Exception Sheet decision, Audit correction, or manual import; entries without `provenance` load as `human`) or `auto` (consensus result, with `committed_months`). An `auto` mapping categorises only once it lists two committed months; before that it is only a Suggester memory neighbour. A `human` decision replaces an `auto` mapping for the merchant, and `NONE` removes the merchant's hint-less mappings.

Matching keys should use a normalized merchant identity by default. Recurring learned mappings may include amount tolerance and day-window hints. Learned memory should avoid full raw descriptions when they contain changing references or sensitive account details.

Reviewed policy guidance lives beside Category Memory as `data/category_memory/reviewed_policy.local.md`. It is generated from `human` mappings and preserves an editable `## Manual Guidance` section. Local LLM prompts may use this policy as review guidance, but the policy is not a confirmed transaction decision, does not bypass Category Memory gating, and does not authorize workbook writes.

A future reviewed decision import should be a separate input contract from raw review output. It should contain the transaction identifier or source fingerprint, the confirmed category, and enough metadata to derive the merchant identity and optional recurring match hints.
