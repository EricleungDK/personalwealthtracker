# Public/Private Boundary

This repository is the incubation workspace for a future public Local Wealth-Tracker Agent package. The public package can contain reusable code, synthetic examples, sample configuration, and documented contracts. Private profile data stays local and ignored by Git.

The Local Wealth-Tracker Agent helps with setup, statement import, review artifacts, monthly planning, Category Memory, and copied-workbook updates. It is not an autonomous finance authority. Importer guesses and untrusted imports stay review-only. Local model suggestions reach a copied workbook without a user decision only when the Trust Policy grants `auto` (two local models agree, amount within the cap, category not never-auto; see [ADR 0001](adr/0001-per-row-authority.md), [ADR 0002](adr/0002-local-two-model-consensus.md)) and workbook safety checks pass.

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
- Copied workbooks under `data/processed/`.
- Workbook backups under `data/backups/`.
- Generated reports and review artifacts under `reports/`.
- Local run logs under `logs/`.
- Local config overlays such as `config/*.local.yaml`.
- Local profile files such as `profiles/*.local.yaml`.

Private profile artifacts may contain transaction descriptions, account-specific paths, merchant patterns, Category Memory, Importer Profiles, proxy split rules, generated audits, copied workbooks, or real financial history. They must stay out of public package artifacts unless explicitly redacted or replaced with synthetic data.

## Local Path Contract

Use these paths for the current incubation repo and future setup workflow:

| Purpose | Public sample | Private local path |
|---------|---------------|--------------------|
| Runtime settings | `config/settings.yaml` | none yet (`config/settings.local.yaml` is not loaded; edit `settings.yaml` locally) |
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
| Logs | none | `logs/` |

The sample public configuration documents the expected shape of local paths, but users should copy it to an ignored profile file before adding real paths.

## Safety Rules

- The original Tracker Workbook is never modified directly.
- Commit mode writes only to a copied workbook under `data/processed/`.
- Unknown or model-assisted statement imports remain untrusted until user review confirms them.
- Category Memory learns only when a month commits: user decisions as `human` (opt out with `learn_to_memory` `no`), consensus results as `auto`, trusted only after two committed months ([ADR 0004](adr/0004-memory-learned-on-commit-with-provenance.md)).
- Importer Profiles learn only from confirmed imports and stay private by default.
- Educated Import Guesses are review assistance, not write authority. Local model suggestions get write authority only through Consensus under the Trust Policy.
- Models run locally; no financial data leaves the machine. Hosted judgment is deferred and not enabled ([ADR 0005](adr/0005-hosted-judgment-deferred.md)).
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
