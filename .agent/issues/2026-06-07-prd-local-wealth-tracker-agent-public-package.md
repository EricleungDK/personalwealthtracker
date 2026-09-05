---
type: prd
id: PRD-2026-06-07-LOCAL-WEALTH-TRACKER-AGENT-PUBLIC-PACKAGE
title: Local Wealth-Tracker Agent Public Package
status: done
labels:
  - done
created: 2026-06-07
---

# Local Wealth-Tracker Agent Public Package

## Problem Statement

PersonalWorthTracker currently works as a local-first Monthly Tracker Workbook Updater for the owner's private workflow. It has a strong safety model, useful review artifacts, Category Memory, local rules, proxy split rules, and optional review-only local model suggestions. But it is still shaped around one private Tracker Workbook, private financial inputs, Nordea-first statement parsing, and ignored local profile data.

The owner wants this to become a public package that other people can use as a Local Wealth-Tracker Agent with a Template Excel Workbook. The package should support arbitrary personal finance workflows over time, without leaking private workbook structure, real statement data, local importer profiles, Category Memory, or proxy split assumptions. The product should feel agentic because it guides setup, imports statements, proposes mappings, creates review artifacts, and plans safe workbook updates locally. It must not become an autonomous finance agent that silently trusts model output or directly edits arbitrary spreadsheets.

The main challenge is separating the reusable public agent, template workbook, synthetic examples, and generic workflow contracts from the owner's private profile layer while preserving the existing local-first safety boundaries.

## Solution

Create a public-package plan for a Local Wealth-Tracker Agent that installs a Python CLI package, a clean synthetic Template Excel Workbook, synthetic statement examples, sample profile/config files, local setup directories, and optional Ollama/local-model integration.

The current repository should remain the incubation repo while the public/private boundary is clarified. Packaging work should start on a branch in this repo. Only after the reusable agent boundary is clear should the project split into a public package/repository and a private profile layer.

The public package should ship a clean synthetic template workbook inspired by the current workbook schema, not a copy of the owner's personal tracker. The template must contain no real values, private categories, personal sheet names, private proxy split assumptions, or hidden financial history. It should include template version metadata so the agent can identify supported workbook schemas.

The agent may customize known workbook dimensions in v1: categories, section labels, period columns, currency settings, and profile paths. Arbitrary formula and layout editing is out of scope until supported workbook schemas and template versions make those changes safe.

For statements, the public package should distinguish between Trusted Statement Adapters and a Statement Import Assistant. Trusted Statement Adapters are deterministic parsers for known formats. Unknown or arbitrary statement formats may use a local model-assisted Statement Import Assistant to transform inputs into normalized transaction review artifacts, but those outputs are Untrusted Imported Transactions until reviewed by the user.

After a user confirms an unknown-format import, the agent may create a private local Importer Profile. Future imports from a similar source may produce Educated Import Guesses for field mappings and transaction categories. High-confidence guesses should be visible and filterable in review artifacts so users can quickly set them aside and focus on lower-confidence rows. They should not be silently trusted as workbook write permission.

Local model assistance remains review-only. The agent may use a local LLM to assist import, categorization, and setup explanations, but model output is never a source of financial authority. Workbook planning, Category Memory learning, and copied-workbook commits remain gated by explicit review decisions and existing workbook safety checks.

## User Stories

1. As a new user, I want to install a local wealth-tracker package, so that I can start tracking my finances without cloning a private project.
2. As a new user, I want a clean Template Excel Workbook, so that I can start from a supported tracker structure.
3. As a new user, I want the template workbook to contain no private data, so that I can trust it is safe to inspect and modify.
4. As a new user, I want synthetic examples, so that I can learn the workflow without exposing real financial data.
5. As a new user, I want a guided setup command, so that the package creates local folders, sample config, and profile paths for me.
6. As a new user, I want to choose my Tracker Currency, so that the workbook and reports match my financial context.
7. As a new user, I want to customize categories and section labels, so that the tracker reflects how I think about my finances.
8. As a new user, I want to add or create period columns safely, so that I can track future months without manually rebuilding formulas.
9. As a new user, I want the agent to explain unsupported workbook edits, so that I do not accidentally break a template schema.
10. As a new user, I want my real workbook, statements, local rules, importer profiles, and learned memory to stay private, so that using the package does not risk committing sensitive data.
11. As a user with a known statement format, I want a deterministic statement adapter, so that my transactions are parsed consistently.
12. As a user with an unknown statement format, I want a Statement Import Assistant, so that I can attempt to import arbitrary bank or finance exports.
13. As a user with an unknown statement format, I want imported transactions to be review-required, so that model-assisted parsing is not mistaken for trusted data.
14. As a user importing a statement, I want to review date, amount, currency, description, and direction fields, so that I can confirm the normalized transaction data is correct.
15. As a user importing a statement, I want validation warnings for missing dates, invalid amounts, unsupported currencies, duplicate rows, and out-of-period transactions, so that bad imports are caught early.
16. As a user who confirms an import once, I want the agent to remember a local Importer Profile, so that future imports from the same source require less setup.
17. As a user with an Importer Profile, I want the agent to make Educated Import Guesses, so that repeated statement formats become easier to process.
18. As a user reviewing an import, I want high-confidence guesses shown clearly, so that I can filter them out and focus on lower-confidence rows.
19. As a user reviewing an import, I want low-confidence guesses highlighted, so that I know where to spend review effort.
20. As a user reviewing an import, I want to confirm or correct suggested categories, so that monthly planning uses my decisions rather than model guesses.
21. As a user reviewing an import, I want confirmed decisions to become eligible for future learning only when I opt in, so that the agent does not overgeneralize.
22. As a user, I want Category Memory and Importer Profiles stored locally, so that my learned financial patterns are private by default.
23. As a user, I want to manually export an importer profile only when I choose, so that sharing is explicit.
24. As a user, I want local LLM support to be optional, so that the package works without requiring a model installation.
25. As a user with local LLM support, I want the model to help with imports and category suggestions, so that manual review is faster.
26. As a user with local LLM support, I want model suggestions to remain review-only, so that the agent does not autonomously edit my finances.
27. As a user, I want dry-run reports before workbook writes, so that I can inspect planned changes.
28. As a user, I want commit mode to write only to copied workbooks, so that my original tracker remains unchanged.
29. As a user, I want workbook safety checks to block formulas, populated cells, derived rows, and unsupported layout changes, so that automation does not corrupt my tracker.
30. As a user, I want reports and audit logs, so that I can trace what the agent parsed, suggested, reviewed, learned, and wrote.
31. As a developer, I want a clear public/private boundary, so that reusable code can be packaged without carrying private assumptions.
32. As a developer, I want template workbook version metadata, so that workbook adapters can validate compatibility.
33. As a developer, I want a statement adapter interface, so that deterministic parsers can be added for known formats.
34. As a developer, I want a model-assisted import contract, so that unknown statement formats produce review artifacts rather than trusted transactions.
35. As a developer, I want importer profiles represented as local data, so that they can be validated, reset, or exported intentionally.
36. As a developer, I want synthetic fixtures for statements and workbooks, so that public tests do not use real financial data.
37. As a developer, I want package docs to describe non-goals, so that users do not expect arbitrary workbook formula editing or autonomous finance decisions.

## Implementation Decisions

- Treat the public product as a Local Wealth-Tracker Agent, not merely a Nordea-to-Excel script.
- Keep the current repository as the incubation repo until the public/private boundary is clear.
- Start packaging work on a branch in this repository before splitting into a public repository or separate package.
- Split the long-term system into a public package/repo and a private profile layer.
- The public package should install a Python CLI command.
- The public package should include a clean synthetic Template Excel Workbook.
- The public package should include synthetic statement examples and sample config/profile files.
- The public package should create ignored local data directories during setup.
- The public package may include optional Ollama/local-model integration.
- The public package should not ship a desktop app in v1.
- The public template workbook must not be copied from the owner's real Tracker Workbook.
- The public template workbook must include template version metadata.
- The v1 template customization scope is categories, section labels, period columns, currencies, and profile paths.
- Arbitrary formula editing and arbitrary layout editing are out of scope for v1.
- Define a Template Excel Workbook schema contract before supporting layout-level customization.
- Define a public/private path contract for real statements, generated outputs, Category Memory, Importer Profiles, local rules, and proxy split rules.
- Preserve the existing copied-workbook commit model.
- Preserve the existing rule that the original Tracker Workbook is not directly modified.
- Preserve workbook safety checks for formulas, populated cells, fixed rows, derived rows, section totals, unsupported rows, unsupported columns, and ambiguous structure.
- Introduce a Trusted Statement Adapter concept for deterministic parsers of known formats.
- Introduce a Statement Import Assistant concept for local model-assisted unknown-format imports.
- Unknown-format imports produce Untrusted Imported Transactions until user review confirms them.
- Confirmed unknown-format imports may create private local Importer Profiles.
- Importer Profiles may generate Educated Import Guesses for future similar imports.
- Educated Import Guesses may suggest field mappings and transaction categories.
- High-confidence Educated Import Guesses should be visible and filterable in review artifacts.
- Low-confidence guesses, changed layouts, invalid fields, unsupported currencies, and out-of-period transactions should remain prominent review work.
- Importer Profiles are private local profile data by default.
- Public releases may ship only synthetic/demo importer profiles.
- Users may manually export Importer Profiles only by explicit action.
- Local model assistance remains review-only and must not become direct workbook write authority.
- Category Memory learning remains based on explicit confirmed review decisions.
- Model suggestions should not train Importer Profiles or Category Memory unless the user confirms the underlying decision.
- CLI workflow should be designed around commands such as setup/init, import statement, review import, plan month, learn memory, and commit copied workbook.
- The public package should document that "arbitrary finance workflow" means extensible adapters plus model-assisted review flows, not guaranteed trusted parsing of every possible financial document.

## Testing Decisions

- Test external behavior through CLI commands, generated review artifacts, reports, audit logs, copied workbooks, and local profile files.
- Do not test implementation details of individual helper functions when public workflow behavior can be tested instead.
- Use synthetic statements, synthetic workbooks, synthetic importer profiles, and mocked local model providers only.
- Add tests for setup/init behavior that verify local directories, sample config, and template workbook placement without touching private paths.
- Add tests for template workbook version validation.
- Add tests for allowed v1 workbook customization: categories, section labels, period columns, currency settings, and profile paths.
- Add tests proving arbitrary formula/layout edits are rejected or marked unsupported.
- Add tests for public/private path separation so real inputs, generated outputs, Category Memory, Importer Profiles, local rules, and proxy split rules remain ignored/local by default.
- Add tests for Trusted Statement Adapter behavior using existing Nordea CSV/PDF fixtures and future synthetic adapters.
- Add tests for Statement Import Assistant review artifacts using mocked local model output.
- Add tests that unknown-format imports produce Untrusted Imported Transactions until user confirmation.
- Add tests for importer profile creation from confirmed imports.
- Add tests for Educated Import Guesses on a later similar import.
- Add tests for changed header/layout/currency/date behavior that forces review instead of silently trusting an importer profile.
- Add review artifact tests that high-confidence guesses are visible and filterable.
- Add review artifact tests that low-confidence guesses are easy to identify.
- Add tests proving model suggestions cannot directly write workbook values.
- Add tests proving Category Memory learning still requires explicit review confirmation and opt-in learning.
- Add tests proving commit mode writes only to copied workbooks and preserves the original workbook.
- Reuse existing workbook safety, review workbook, Category Memory, local LLM, and pipeline integration test patterns where possible.

## Out of Scope

- Desktop app packaging.
- Remote SaaS product.
- Remote LLM APIs as a required runtime.
- Autonomous finance decisions.
- Direct edits to the user's original workbook.
- Silent trust of unknown-format model imports.
- Guaranteed parsing of every bank, broker, card, payroll, or investment document.
- Arbitrary workbook formula editing.
- Arbitrary workbook layout editing.
- Public shipping of the owner's real Tracker Workbook.
- Public shipping of real statements, generated reports, Category Memory, Importer Profiles, private local rules, proxy split rules, or personal categories.
- Generic investment statement automation beyond existing future-investment evidence boundaries.
- Live FX lookup.
- Bank API or Open Banking integration.
- Scheduler, notifications, and cloud sync.

## Further Notes

This PRD comes from the 2026-06-07 packaging grilling session. The key product shift is from a private Monthly Tracker Workbook Updater toward a public Local Wealth-Tracker Agent with a Template Excel Workbook. The key safety boundary remains unchanged: local model output can assist setup, import, and review, but it is not financial authority. User review, Category Memory opt-in, workbook safety checks, and copied-workbook commit mode remain the bridge from suggestions to actual tracker updates.

This PRD should be split into independently implementable issues before code changes begin. Likely issue themes are public/private package boundary, template workbook schema, CLI setup workflow, Statement Import Assistant contract, Importer Profile storage, Educated Import Guess review UX, and packaging/docs cleanup.
