# Project Overview

This page is the non-technical map of PersonalWorthTracker. It explains what lives where, how a monthly run moves through the project, and which files are scripts, components, or documentation.

For the step-by-step monthly checklist, use [monthly_workflow.md](monthly_workflow.md).

## What The Project Does

PersonalWorthTracker is a local command-line helper for updating a personal Excel wealth tracker. It reads a Nordea bank statement, classifies the transactions, checks the tracker workbook for safe target cells, and writes review outputs before anything is committed to a copied workbook.

The original tracker workbook, real bank statements, generated reports, category memory, backups, and processed workbooks stay local and ignored by Git.

## Project Map

```mermaid
flowchart TD
  LocalFiles["Local personal files<br/>ignored by Git"] --> Inputs["Net Worth Tracker.xlsx<br/>Nordea CSV or PDF statements"]
  Inputs --> CLI["wealth-tracker<br/>terminal command"]
  CLI --> Source["src/personal_wealth_tracker<br/>project code"]
  Source --> Outputs["reports and copied workbooks<br/>ignored by Git"]

  Config["config<br/>public categories and rules"] --> Source
  Docs["docs<br/>operator docs and project maps"] --> User["You or an agent"]
  AgentDocs[".agent<br/>planning, issues, deep system notes"] --> User
  Tests["tests<br/>synthetic and redacted checks"] --> Source
  Scripts["scripts<br/>helper utilities"] --> Tests
```

Read this diagram as:

- `Local personal files` are your real finance files. They are useful for running the tool, but should not be committed.
- `src/personal_wealth_tracker` is where the application logic lives.
- `config` contains committed shared rules; private merchant-specific rules and proxy split rules belong in ignored local files such as `rules.local.yaml`.
- `docs` is the user-facing place to understand and operate the project.
- `.agent` is the working memory and issue tracker for coding agents.

## Monthly Run Flow

```mermaid
flowchart LR
  Statement["Nordea statement<br/>CSV preferred, PDF fallback"] --> Parser["Parser<br/>turns bank rows into transactions"]
  Tracker["Tracker workbook<br/>existing Excel file"] --> WorkbookRead["Workbook reader<br/>finds rows, months, formulas, existing values"]
  Rules["Config, category registry, category memory, and local proxy split rules<br/>known categories and learned choices"] --> Categorizer["Categorizer<br/>chooses transaction categories"]

  Parser --> Categorizer
  Categorizer --> Planner["Workbook planner<br/>decides write, skip, or review"]
  WorkbookRead --> Planner

  Planner --> DryRun["Dry-run outputs<br/>report, audit, CSV, review workbook"]
  DryRun --> Review["Manual review workbook<br/>choose manual_category, new_parent_category, new_leaf_category, and learn_to_memory"]
  Review --> Decisions["Monthly Review Decisions<br/>current-month overrides"]
  Review --> Registry["Category Registry<br/>validated new leaf registrations"]
  Review --> Memory["Category Memory<br/>future learned merchant choices"]
  Registry --> Rules
  Decisions --> Planner
  Memory --> Rules
  Planner --> Commit["Commit mode<br/>writes only to a copied workbook"]
```

The important split is:

- Dry run means plan and report only.
- Monthly Review Decisions fix specific transactions for the selected month.
- The Category Registry in `config/categories.yaml` defines Parent/Section Row labels, Leaf Category Row labels, derived rows, aliases, and where missing leaf categories may be added.
- Category Memory learns selected merchant choices for future months.
- Proxy Split Transfer rules in ignored `rules.local.yaml` can split one intermediary transfer into fixed allocation lines plus an optional Residual Review Line.
- Commit mode writes only safe values into a copied workbook under `data/processed/`.

## Main Components

```mermaid
flowchart TD
  CLI["cli.py<br/>reads command options"] --> Pipeline["pipeline.py<br/>coordinates the run"]
  Pipeline --> Config["config.py<br/>loads settings and rules"]
  Pipeline --> Csv["nordea_csv.py<br/>CSV bank parser"]
  Pipeline --> Pdf["nordea_pdf.py<br/>PDF bank parser"]
  Pipeline --> Memory["category_memory.py<br/>private learned categories"]
  Pipeline --> Review["review_decisions.py<br/>reads reviewed XLSX or CSV"]
  Pipeline --> Categorizer["categorizer.py<br/>matches transactions to categories"]
  Pipeline --> Workbook["workbook.py<br/>plans and writes workbook changes safely"]
  Pipeline --> Reporting["reporting.py<br/>writes reports, audit logs, review files"]
  Pipeline --> Models["models.py<br/>shared data shapes"]
  Cleanup["cleanup.py<br/>separate workbook maintenance"] --> Workbook
```

Plain-language component roles:

- `cli.py` is the front door. It turns terminal options into a command.
- `pipeline.py` is the coordinator. It decides which step runs next.
- `nordea_csv.py` and `nordea_pdf.py` turn bank files into transaction records.
- `categorizer.py` decides what each transaction probably is.
- `review_decisions.py` applies your reviewed Excel decisions by exact transaction ID.
- `category_memory.py` stores future learned category choices in ignored local data.
- `workbook.py` protects the tracker workbook from unsafe writes.
- `reporting.py` produces the files you inspect after a dry run.
- `cleanup.py` is for separate workbook maintenance tasks, not monthly transaction updates.

## Outputs And Decision Files

```mermaid
flowchart TD
  Transaction["Transaction<br/>one bank movement"] --> Categorized["Categorized transaction<br/>transaction plus chosen category"]
  Categorized --> Update["Workbook update plan<br/>target row, target cell, action, reason"]
  Update --> Report["report_<period>.md<br/>human-readable summary"]
  Update --> CategorizedCsv["categorized_transactions_<period>.csv<br/>all transactions"]
  Update --> ReviewCsv["review_required_<period>.csv<br/>simple review queue"]
  Update --> ReviewXlsx["review_required_<period>.xlsx<br/>Excel review workbook"]
  Update --> Audit["audit_<period>.jsonl<br/>machine-readable trace"]
  Update --> CopiedWorkbook["data/processed workbook<br/>only in commit mode"]
```

Use the files this way:

- Start with the Markdown report to understand the run quality and planned workbook changes.
- Use `review_required_<period>.xlsx` when you need to manually classify transactions.
- Use `All Transactions` inside the review workbook to debug a low classification rate or low no-review rate.
- Use `Category Options` inside the review workbook to see workbook fields and safety notes.
- Use the audit log only when you need a detailed machine-readable trace.

## Scripts And Tests

```mermaid
flowchart LR
  Script["scripts/generate_redacted_nordea_fixture.py<br/>creates safe synthetic Nordea fixture"] --> Fixtures["tests/fixtures<br/>redacted CSV and PDF"]
  Fixtures --> Tests["tests<br/>unit and integration checks"]
  Tests --> Modules["src/personal_wealth_tracker<br/>application modules"]
  Tests --> DocsTests["tests/test_documentation.py<br/>documentation guardrails"]
```

The script is not part of the monthly operator workflow. It exists so tests can cover Nordea parsing without committing real bank statements.

## Documentation Map

- [monthly_workflow.md](monthly_workflow.md) - monthly operator checklist.
- [README.md](../README.md) - setup commands, privacy rules, dry-run and commit examples.
- [.agent/System/architecture.md](../.agent/System/architecture.md) - deeper technical architecture notes.
- [.agent/System/domain_language.md](../.agent/System/domain_language.md) - project vocabulary used by agents.
- [.agent/System/data_contracts.md](../.agent/System/data_contracts.md) - expected data shapes and safety contracts.
- [.agent/issues/kanban.md](../.agent/issues/kanban.md) - local issue tracker.

## Glossary

- CLI: Command-line interface. The `wealth-tracker` command you run in the terminal.
- Parser: Code that turns a bank statement file into structured transactions.
- Transaction: One bank movement from a statement.
- Category: The tracker workbook row a transaction belongs to.
- Parent/Section Row: A workbook row such as `Living expenses`, `Services`, or `Insurance` that groups or totals child rows and is not a valid transaction category target.
- Leaf Category Row: A workbook row under a parent section that can receive source-backed transaction totals, manual review decisions, and Category Memory learning.
- Category Registry: The YAML category source in `config/categories.yaml` that records parent, leaf, derived, alias, and allowed-new-child rules.
- Dry run: A run that plans and reports but does not write workbook values.
- Commit mode: A run with `--commit`; it writes eligible values only to a copied workbook.
- Review workbook: The Excel file where you choose `manual_category` for existing leaf rows, `new_parent_category` and `new_leaf_category` for missing leaf rows, and optional `learn_to_memory`.
- Monthly Review Decisions: Current-month manual choices applied by exact transaction ID.
- Category Memory: Private learned merchant/category choices for future runs.
- Proxy Split Transfer: One intermediary bank transfer split into explicit tracker allocation lines while preserving the source transaction for audit.
- Residual Review Line: The leftover amount from a larger proxy split transfer; it is reviewed for the current month and not learned into Category Memory.
- Fixed row: A workbook row the automation must not overwrite.
- Formula-owned row: A workbook row controlled by Excel formulas.
- Audit log: A detailed machine-readable record of what happened.
- Mermaid: A text format for diagrams inside Markdown.
