# Public/Private Boundary

This repository is the incubation workspace for a future public Local Wealth-Tracker Agent package. The public package can contain reusable code, synthetic examples, sample configuration, and documented contracts. Private profile data stays local and ignored by Git.

The Local Wealth-Tracker Agent helps with setup, statement import, review artifacts, monthly planning, Category Memory, and copied-workbook updates. It is not an autonomous finance authority. Model output, importer guesses, and generated suggestions stay review-only until a user confirms decisions and the workbook safety checks allow a copied-workbook write.

## Public Package Responsibilities

Public package artifacts are safe to commit and distribute:

- `src/personal_wealth_tracker/` reusable CLI and workflow code.
- `config/settings.yaml`, `config/categories.yaml`, and `config/rules.yaml` sample public configuration.
- `config/rules.local.example.yaml`, `config/guidance_aliases.local.example.yaml`, and `config/profile.example.yaml` sample public configuration for local overlays and profile paths.
- `docs/` user-facing workflow, project maps, and public/private boundary documentation.
- `.agent/System/` durable architecture, data-contract, domain-language, and privacy notes for coding agents.
- `tests/fixtures/` redacted or synthetic fixtures only.
- `scripts/` utilities for generating safe synthetic or redacted fixtures.

Public artifacts must not embed real statements, real workbook values, personal category assumptions, private proxy split rules, Category Memory, Importer Profiles, credentials, or generated report outputs.

## Private Profile Responsibilities

Private profile artifacts are local-only and ignored by Git:

- Real tracker workbook: for example `Net Worth Tracker.xlsx`.
- Real statements and exports under `data/raw_statements/`.
- Watched or staging inputs under `data/watched_folder/`.
- Generated Category Memory under `data/category_memory/`.
- Local Importer Profiles under `data/importer_profiles/`.
- Copied workbooks from `cleanup` under `data/processed/`.
- Workbook backups under `data/backups/`.
- The Commit Ledger `data/commit_ledger.json` (amounts each committed month wrote).
- Generated reports and review artifacts under `reports/`.
- Local run logs under `logs/`.
- Local config overlays such as `config/*.local.yaml`.
- Local profile files such as `profiles/*.local.yaml`.

Private profile artifacts may contain transaction descriptions, account-specific paths, merchant patterns, Category Memory, Importer Profiles, proxy split rules, generated audits, copied workbooks, or real financial history. They must stay out of public package artifacts unless explicitly redacted or replaced with synthetic data.

## Local Path Contract

Use these paths for the current incubation repo and future setup workflow:

| Purpose | Public sample | Private local path |
|---------|---------------|--------------------|
| Runtime settings | `config/settings.yaml` | `config/settings.local.yaml` |
| Category registry | `config/categories.yaml` | future local overlay only when explicitly supported |
| Rule examples | `config/rules.local.example.yaml` | `config/rules.local.yaml` |
| Guidance Aliases | `config/guidance_aliases.local.example.yaml` | `config/guidance_aliases.local.yaml` |
| Profile examples | `config/profile.example.yaml` | `profiles/<profile>.local.yaml` |
| Real statements | none | `data/raw_statements/` |
| Category Memory | none | `data/category_memory/` |
| Importer Profiles | synthetic/demo only | `data/importer_profiles/` |
| Generated reports | none | `reports/` |
| Copied workbooks | none | `data/processed/` |
| Backups | none | `data/backups/` |
| Commit Ledger | none | `data/commit_ledger.json` |
| Logs | none | `logs/` |

The sample public configuration documents the expected shape of local paths, but users should copy it to an ignored profile file before adding real paths.

## Safety Rules

- Commit mode backs up the Tracker Workbook to `data/backups/` before updating it in place, so every committed month accumulates in one workbook.
- A re-commit of a month rewrites only cells still holding the Commit Ledger amount; cells you edited stay in review.
- `cleanup --commit` writes only to a copied workbook under `data/processed/`.
- Unknown or model-assisted statement imports remain untrusted until user review confirms them.
- Category Memory learns only from confirmed review decisions with explicit learning opt-in.
- Importer Profiles learn only from confirmed imports and stay private by default.
- Local model suggestions and Educated Import Guesses are review assistance, not write authority.
- Workbook safety checks still block formulas, populated cells, fixed rows, derived rows, section totals, unsupported rows, unsupported columns, and ambiguous structure.

## Public Release Gate

Before any package or repository is published publicly, inspect the diff for these private artifact classes:

- real statements or exports,
- real tracker workbooks or copied workbooks,
- generated reports, review workbooks, or audit logs,
- Category Memory,
- Importer Profiles,
- private local rules,
- proxy split rules with personal labels or amounts,
- credentials, tokens, environment files, or local machine paths.

Only synthetic fixtures, redacted fixtures, and sample public configuration belong in public release artifacts.
