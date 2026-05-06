Personal Wealth Tracker Automation — Codex Project Plan

1. Project Background

I currently maintain a personal wealth tracker in an Excel workbook stored in Google Drive. The workbook tracks monthly net worth, assets, liabilities, income, recurring payments, living expenses, services, insurance, investments, and other personal finance categories.

The current process is mostly manual. Every month, I need to collect bank balances, income, expenses, credit card balances, and other financial information, then type the numbers into the correct month and category in the tracker. Some fixed or recurring costs are already pre-filled in the spreadsheet, but variable transactions still require manual entry.

The main problem is that this workflow is repetitive and easy to forget. When I miss a month, the tracker becomes inaccurate and harder to catch up later.

The goal of this project is to build a Python-based automation agent that can help update the tracker every month using bank data, downloaded bank statements, Google Drive tooling, rule-based categorization, and eventually a local/open-source LLM.

⸻

2. Current Tracker Structure

The existing workbook contains one main sheet named:

Net worth

The tracker is organized horizontally by year and month. Categories are organized vertically in rows.

Observed high-level sections include:

* Total net worth
* Growth
* Assets
* Deposits
* Saving Account
* Financial instruments
* JEPI
* OXY
* Real estate
* Digital assets
* Commodities
* Objects of value
* Receivables
* Liabilities
* Consumer debt
* Nordea Credit Card
* Real estate debt
* Accrued taxes
* Cashflow
* Income (net)
* Full-time job (net)
* Labour market contribution
* Taxes
* Recurring payments
* Living expenses
* Rent
* Family support categories such as Mom and Dad
* Shopping
* Food & Drinks
* Lunch
* Cleaning costs
* Services
* Disney+
* Louis Nielsen
* Apple Cloud
* Fitness center membership
* Google Cloud
* Max
* Metro
* Insurance
* House insurance Tryg
* Akasse
* Liability insurance
* Others
* Mobile phone
* Traveling
* Banking account fees
* Investments
* Annuity K43
* Annuity M12
* Stock investment plan

The automation must respect the existing workbook structure. It should not replace the tracker with a new format unless explicitly decided later.

⸻

3. Problem Statement

The current wealth tracking workflow has these issues:

1. Monthly manual data entry takes time.
2. It is easy to forget to update the tracker.
3. Bank transactions need to be reviewed and categorized manually.
4. Some expenses are recurring, but variable spending is not automated.
5. Generic expense categorization is not enough because the tracker has a personal category structure.
6. Historical categorization decisions should be reused to improve consistency.
7. The tracker is stored in Google Drive, so future versions need safe Google Drive read/write access.
8. Bank API availability is uncertain, so the system must support both API ingestion and manual statement upload.
9. The system must avoid overwriting existing manually maintained values.
10. The user needs a clear report after every run to confirm what changed and what requires review.

⸻

4. Project Goal

Build an automated personal wealth tracker agent that runs monthly, reads financial data, categorizes transactions according to the existing tracker structure, and updates the correct month column in the workbook.

The desired long-term workflow is:

On the 1st day of every month, the agent collects previous-month account or statement data, categorizes transactions and income, maps them to existing tracker rows, updates the correct month column in the Google Drive Excel workbook or Google Sheet, and produces a short review report.

⸻

5. Target Outcome

The finished system should be able to:

1. Access the personal wealth tracker file.
2. Identify the target reporting month.
3. Retrieve bank data through an API when available.
4. Fall back to reading downloaded bank statements when API access is unavailable.
5. Parse transaction data from CSV, XLSX, or PDF files.
6. Normalize transaction dates, descriptions, amounts, currencies, and directions.
7. Categorize transactions using historical mappings, rules, recurring payment logic, and eventually an LLM.
8. Map categorized totals into the tracker’s existing rows.
9. Update the correct month column.
10. Preserve existing formulas, formatting, and manually pre-filled fixed costs.
11. Generate a Markdown review report after every run.
12. Produce an audit log of all proposed or committed changes.
13. Support dry-run mode before writing changes.
14. Flag low-confidence or conflicting items for human review.
15. Optionally send a monthly digest notification.

⸻

6. Recommended System Design

6.1 Main Components

wealth-tracker-agent/
├── config/
│   ├── categories.yaml
│   ├── rules.yaml
│   ├── fixed_rows.yaml
│   └── settings.yaml
├── data/
│   ├── raw_statements/
│   ├── watched_folder/
│   ├── processed/
│   ├── category_memory/
│   └── backups/
├── reports/
│   ├── monthly_reports/
│   └── audit_logs/
├── src/
│   ├── main.py
│   ├── scheduler.py
│   ├── google_drive_client.py
│   ├── google_sheets_client.py
│   ├── excel_client.py
│   ├── bank_api_client.py
│   ├── statement_parser.py
│   ├── transaction_normalizer.py
│   ├── category_mapper.py
│   ├── llm_classifier.py
│   ├── confidence_router.py
│   ├── tracker_writer.py
│   ├── validation.py
│   ├── audit_logger.py
│   ├── report_generator.py
│   └── notification_dispatcher.py
├── tests/
│   ├── test_statement_parser.py
│   ├── test_transaction_normalizer.py
│   ├── test_category_mapper.py
│   ├── test_tracker_writer.py
│   └── test_validation.py
├── logs/
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md

⸻

7. Data Ingestion Strategy

The automation should support two ingestion paths.

7.1 Option A — Bank API Available

Bank API
   ↓
Fetch account balances and transactions
   ↓
Normalize transaction fields
   ↓
Categorize transactions
   ↓
Update tracker

This is the preferred long-term path if the bank provides API access or can be accessed through an Open Banking provider.

Potential future provider:

GoCardless Bank Account Data / Nordigen-style Open Banking API

This should be added only after the local statement-based workflow is reliable.

7.2 Option B — Downloaded Bank Statement

Downloaded bank statement
   ↓
Read CSV / XLSX / PDF statement
   ↓
Normalize transaction fields
   ↓
Categorize transactions
   ↓
Update tracker

This should be the MVP path because it avoids bank API complexity.

7.3 Watched Folder Fallback

The project should support a watched folder where the user can drop a monthly bank statement.

Example:

data/watched_folder/

If no bank API is configured, the agent should look for the latest statement file in this folder.

If both API and statement files are available, the system should prefer the configured primary source and avoid duplicate processing.

⸻

8. Monthly Workflow

8.1 Scheduled Trigger

The automation should eventually run on the 1st day of each month.

Example:

Run date: 2026-03-01
Reporting period: February 2026
Target workbook column: February under year 2026

8.2 Workflow Diagram

flowchart TD
    A[Scheduled run on 1st of month] --> B[Determine previous month]
    B --> C[Load config]
    C --> D[Load tracker workbook]
    D --> E[Create backup copy]
    E --> F[Read tracker structure and historical categories]
    F --> G{Bank API configured?}
    G -- Yes --> H[Fetch transactions from bank API]
    G -- No --> I[Read latest statement from watched folder]
    H --> J[Normalize transaction data]
    I --> J[Normalize transaction data]
    J --> K[Deduplicate transactions]
    K --> L[Match historical categorization]
    L --> M[Apply fixed and recurring payment rules]
    M --> N[Apply keyword rules]
    N --> O{Still uncertain?}
    O -- Yes --> P[Use LLM classifier]
    O -- No --> Q[Aggregate by tracker category]
    P --> R[Validate LLM JSON and category]
    R --> Q
    Q --> S[Run confidence router]
    S --> T[Generate dry-run preview]
    T --> U{Commit mode enabled?}
    U -- No --> V[Generate report only]
    U -- Yes --> W[Write safe updates to copied workbook]
    W --> X[Write audit log]
    V --> X
    X --> Y[Generate monthly digest]

⸻

9. Transaction Categorization Strategy

The system should not rely only on the LLM. A hybrid approach is safer and easier to test.

9.1 Categorization Priority

Use this order:

1. Exact historical match
2. Known recurring payment rule
3. Merchant keyword rule
4. Amount-and-date pattern match
5. LLM classification
6. Human review fallback

9.2 Historical Match

If a transaction merchant or description was categorized before, reuse that category.

Example:

historical_mappings:
  "APPLE.COM/BILL": "Apple Cloud"
  "FITNESS WORLD": "Fitness center membership"
  "GOOGLE CLOUD": "Google Cloud"
  "DISNEY PLUS": "Disney+"
  "LOUIS NIELSEN": "Louis Nielsen"

9.3 Rule-Based Mapping

Rules should live in config/rules.yaml.

Example:

rules:
  - category: Rent
    match_keywords: ["rent", "husleje"]
    transaction_type: expense
  - category: Food & Drinks
    match_keywords: ["netto", "rema", "føtex", "bilka", "lidl", "meny"]
    transaction_type: expense
  - category: Mobile phone
    match_keywords: ["telmore", "yousee", "telenor", "3 mobil"]
    transaction_type: expense
  - category: Full-time job (net)
    match_keywords: ["salary", "payroll", "løn"]
    transaction_type: income

9.4 Fixed and Pre-Filled Rows

Some tracker rows contain fixed or recurring values that are already pre-filled.

The system should support a config file such as:

fixed_rows:
  - Rent
  - Disney+
  - Apple Cloud
  - Fitness center membership

Recommended behavior:

* Do not overwrite fixed rows by default.
* Compare detected transactions against fixed row values.
* If the detected value differs from the pre-filled value, flag it in the report.
* Allow overwrite only if explicitly enabled in config.

9.5 LLM-Based Categorization

Suggested model:

DeepSeek-R1-Distill-Qwen-7B

The LLM should be used only when historical and rule-based logic cannot classify a transaction confidently.

The LLM prompt should include:

* Transaction date
* Transaction description
* Amount
* Currency
* Direction: income or expense
* Allowed tracker categories only
* Similar past transactions if available
* Required structured JSON output

Example output:

{
  "category": "Food & Drinks",
  "confidence": 0.86,
  "reason": "Merchant appears to be grocery or food related."
}

Important LLM note:

DeepSeek-R1-Distill models are reasoning-focused and may be slower per transaction. This is acceptable for a small monthly batch, but if speed becomes a problem, consider a smaller/faster instruct model for classification.

⸻

10. Tracker Update Logic

10.1 Identify Target Month Column

The tracker has years and months across columns. The writer must locate the correct year and month before writing.

Example:

Run date: 2026-03-01
Target reporting month: February 2026
Target column: Feb under year 2026

10.2 Identify Target Category Row

The writer must find the row based on the tracker category name.

Example:

Category: Google Cloud
Target row: Google Cloud row
Target month column: February 2026
Action: write monthly total amount

10.3 Preserve Existing Values

Before writing, the system must check whether the target cell already contains a value.

Recommended behavior:

* If the cell is empty, write the generated value.
* If the cell contains a formula, do not overwrite it.
* If the cell already contains a fixed recurring value, do not overwrite it unless configured.
* If the cell contains a manual value, flag it for review.
* If the generated value differs significantly from the existing value, flag it for review.

10.4 Aggregation Rule

Multiple transactions can map to the same tracker row in the same month. These should be summed before writing.

Example:

Transaction 1: Netto, 250 DKK → Food & Drinks
Transaction 2: Rema 1000, 180 DKK → Food & Drinks
Transaction 3: Føtex, 320 DKK → Food & Drinks
Monthly total: 750 DKK → Food & Drinks row

10.5 Optional Auto-Filled Cell Highlighting

When a value is written automatically, the system may apply a light fill color to the updated cell.

Purpose:

* Make automated entries easy to identify.
* Help compare manual vs automated entries.
* Support later review and debugging.

This should be optional and configurable.

⸻

11. Dry-Run and Commit Modes

The system should run in dry-run mode by default.

11.1 Dry-Run Mode

Dry-run mode should:

* Parse the statement.
* Categorize transactions.
* Aggregate totals.
* Detect target workbook cells.
* Report what would be written.
* Report conflicts and low-confidence items.
* Not modify the workbook.

Example CLI:

python -m src.main \
  --tracker "Net Worth Tracker.xlsx" \
  --statement "statement_2026_02.csv" \
  --year 2026 \
  --month Feb \
  --dry-run

11.2 Commit Mode

Commit mode should write changes only to a copied workbook, never directly to the original file.

Example CLI:

python -m src.main \
  --tracker "Net Worth Tracker.xlsx" \
  --statement "statement_2026_02.csv" \
  --year 2026 \
  --month Feb \
  --commit

Commit mode should:

* Create a backup first.
* Write only validated updates.
* Skip review-required items.
* Generate a Markdown report.
* Generate an audit log.

⸻

12. Accuracy and Review Controls

12.1 Confidence Thresholds

Suggested thresholds:

confidence_thresholds:
  auto_write: 0.85
  review_required: 0.60
  reject_below: 0.60

Behavior:

* >= 0.85: eligible for auto-write
* 0.60 - 0.84: include in review report
* < 0.60: do not write automatically

12.2 Review Report

Each run should generate a Markdown report.

Example:

Monthly Wealth Tracker Automation Report
Reporting Month: February 2026
Mode: Dry run
Updated / Proposed items:
- Full-time job (net): 70,736
- Rent: 8,970
- Food & Drinks: 4,200
- Google Cloud: 328
Flagged for review:
- Unknown merchant: 349 DKK, suggested category Shopping, confidence 0.64
- Transfer: 2,000 DKK, possible category Saving Account, confidence 0.58
Skipped items:
- Existing manual value found in Nordea Credit Card row
- Fixed row detected for Disney+

⸻

13. Audit Log Requirements

Every run should create an audit log.

The audit log should record:

* Run timestamp
* Mode: dry-run or commit
* Source statement file or API source
* Target workbook
* Target year and month
* Transaction ID or generated hash
* Original transaction description
* Amount
* Suggested category
* Confidence
* Categorization method
* Target row
* Target cell
* Action: proposed, written, skipped, review_required
* Reason for action

Suggested output formats:

reports/audit_logs/audit_2026_02.csv
reports/audit_logs/audit_2026_02.jsonl

The audit log is important because this project changes personal finance data and must be traceable.

⸻

14. Monthly Digest Notification

A future version should send a monthly digest after each run.

Possible channels:

* Email
* Telegram
* Markdown file saved to Google Drive

Digest should include:

* Run status
* Reporting month
* Number of transactions processed
* Number auto-categorized
* Number flagged for review
* Number skipped
* Total income detected
* Total expenses detected
* Top spending categories
* Link or path to the full report

This should not be part of the first MVP unless the local workflow is already stable.

⸻

15. Budget Threshold Alerts

Budget threshold alerts are a future enhancement.

Example:

budget_thresholds:
  Food & Drinks: 4500
  Shopping: 2500
  Traveling: 3000

If monthly spending exceeds the configured threshold, the digest report should include a warning.

This is not required for MVP 1.

⸻

16. Data Model

16.1 Normalized Transaction

class Transaction:
    transaction_id: str
    date: date
    description: str
    merchant: str | None
    amount: float
    currency: str
    direction: str  # income or expense
    account_name: str | None
    source_file: str | None

16.2 Categorized Transaction

class CategorizedTransaction:
    transaction_id: str
    date: date
    description: str
    amount: float
    direction: str
    suggested_category: str
    confidence: float
    categorization_method: str  # historical, rule, recurring, llm, manual
    review_required: bool

16.3 Tracker Update

class TrackerUpdate:
    year: int
    month: str
    category: str
    amount: float
    source_transactions: list[str]
    target_row: int
    target_column: int
    existing_value: float | str | None
    write_action: str  # write, skip, review

⸻

17. Security and Privacy Requirements

This project handles sensitive financial data. Security should be built in from the beginning.

Recommended controls:

1. Store credentials in .env or a secrets manager.
2. Do not commit bank statements, credentials, tracker files, logs, or local model outputs.
3. Use read-only bank API permissions where possible.
4. Use local LLM inference if privacy is important.
5. Avoid sending transaction data to external LLM APIs unless explicitly approved.
6. Keep an audit log of every proposed or committed tracker update.
7. Create a backup before every write operation.
8. Redact sensitive account identifiers in reports where possible.

Suggested .gitignore:

.env
credentials.json
token.json
data/raw_statements/
data/watched_folder/
data/processed/
data/category_memory/
data/backups/
reports/audit_logs/
logs/
*.xlsx
*.csv
*.pdf

⸻

18. Error Handling Requirements

The system should handle these cases safely:

* Tracker workbook not found
* Google Drive file not found
* Google API authentication failure
* Bank API unavailable
* Bank statement missing
* Multiple candidate statement files found
* Bank statement format changed
* Duplicate transactions detected
* Unknown tracker category
* Target year not found
* Target month column not found
* Target category row not found
* Target cell already populated
* Target cell contains a formula
* LLM output is invalid JSON
* LLM suggests a category that does not exist
* Exchange rate or currency mismatch
* Expense/income sign confusion
* Transfer between own accounts mistaken as expense
* Credit card repayment mistaken as spending

The system should never silently overwrite important existing data.

⸻

19. Suggested Technical Stack

19.1 Python Libraries

pandas
openpyxl
python-dotenv
pydantic
PyYAML
google-api-python-client
google-auth
google-auth-oauthlib
APScheduler
loguru
pytest

For Google Sheets later:

gspread
Google Sheets API v4

For PDF statements later:

pdfplumber
camelot
tabula-py

For local LLM later:

Ollama
llama.cpp
vLLM
Hugging Face Transformers

⸻

20. Phased Delivery Plan

MVP 1 — Local Statement Upload Automation

Build a local Python script that:

1. Reads a downloaded bank statement file.
2. Reads the existing tracker workbook.
3. Locates the target year and month column.
4. Loads category rules from YAML.
5. Normalizes transactions.
6. Categorizes using rules and historical mappings only.
7. Aggregates totals by tracker category.
8. Runs in dry-run mode by default.
9. Generates a Markdown review report.
10. Generates an audit log.
11. Writes only to a copied workbook when --commit is used.

Do not implement Google Drive, bank API, scheduler, or LLM in MVP 1.

MVP 2 — Safe Excel Writer Enhancements

Add:

1. Backup creation before commit.
2. Formula detection.
3. Existing value conflict detection.
4. Optional auto-filled cell highlighting.
5. Better fixed-row handling.
6. More unit tests around workbook writing.

MVP 3 — Google Drive Integration

Add:

1. Download tracker from Google Drive.
2. Create timestamped backup.
3. Update copied workbook.
4. Upload updated workbook back to Google Drive.
5. Save monthly report to Google Drive.

MVP 4 — LLM Categorization

Add:

1. Local LLM support.
2. Allowed-category-only prompt.
3. Structured JSON output validation.
4. Similar historical examples.
5. Confidence router.
6. Save confirmed decisions into category memory.

MVP 5 — Monthly Scheduler and Digest

Add:

1. Monthly scheduler.
2. Run on the 1st day of the month.
3. Process previous month.
4. Generate digest notification.
5. Support manual re-run.

MVP 6 — Bank API Integration

If bank API access is available:

1. Add Open Banking connection.
2. Fetch account balances and transactions directly.
3. Handle consent renewal.
4. Fall back to watched folder when API fails.

MVP 7 — Budget Threshold Alerts

Add:

1. Configurable category spending thresholds.
2. Warnings in monthly digest.
3. Month-over-month comparison.

⸻

21. Recommended First Coding Milestone

The best first coding milestone is:

Create a local Python script that takes:
1. the existing tracker workbook,
2. one downloaded bank statement file,
3. a category rules YAML file,
4. a target year and month,
then outputs:
1. a dry-run Markdown report,
2. a CSV/JSONL audit log,
3. a CSV file of categorized transactions,
4. a list of transactions requiring review,
5. an updated copy of the workbook only when --commit is used.

This avoids Google API, bank API, scheduling, and LLM complexity at the beginning while still proving the core workflow.

⸻

22. Suggested Codex Implementation Prompt

Build a Python project for automating a personal wealth tracker stored as an Excel workbook.
The tracker has one main sheet named "Net worth". Years and months are arranged horizontally across columns, and financial categories are arranged vertically in rows. The automation must update the correct category row and target month column without breaking existing formulas or formatting.
Start with MVP 1 only.
The script should accept:
1. an existing tracker workbook path,
2. one downloaded bank statement CSV/XLSX file,
3. a category rules YAML file,
4. a target year and month.
The script should:
1. parse and normalize transactions,
2. categorize transactions using rules and historical mappings only,
3. aggregate monthly totals by existing tracker category,
4. detect the correct row and month column in the workbook,
5. run in dry-run mode by default,
6. generate a Markdown review report,
7. generate a CSV or JSONL audit log,
8. write only to a copied workbook when --commit is used,
9. never overwrite existing manual values or formulas without flagging them,
10. skip low-confidence or unknown-category transactions.
Do not implement Google Drive, bank API, scheduler, or LLM yet. Design the project structure so these can be added later.

⸻

23. Extra Details to Add Before Coding

To make implementation more accurate, add these details when available:

1. Bank name.
2. Whether the bank supports API or Open Banking access.
3. Example downloaded bank statement file.
4. Statement format: CSV, XLSX, or PDF.
5. Exact transaction columns: date, text, amount, balance, currency.
6. Whether expenses are negative or positive.
7. Whether tracker values are in DKK, EUR, or another currency.
8. How to handle exchange rates.
9. Whether credit card payments should be expenses or transfers.
10. Whether transfers between own accounts should be ignored.
11. Whether investment purchases affect cashflow, assets, or both.
12. Which rows are manually maintained and should never be overwritten.
13. Which rows are fixed recurring costs.
14. Whether the final file should remain Excel or be converted to Google Sheets.
15. Whether manual approval is required before writing.
16. Preferred monthly report destination: local file, email, Telegram, or Google Drive.
17. Runtime environment: laptop, server, Docker, GitHub Actions, cloud VM, or Raspberry Pi.

⸻

24. Definition of Done

The project is successful when:

1. The agent can process a monthly statement without manual typing.
2. At least 80–90% of recurring and obvious transactions are categorized correctly.
3. Low-confidence transactions are flagged instead of guessed silently.
4. The correct month column is detected and updated.
5. Existing formulas and formatting remain intact.
6. Existing manual values are not overwritten silently.
7. A backup is created before every commit.
8. Dry-run mode gives a clear preview before writing.
9. A Markdown report is generated after every run.
10. An audit log records all proposed and committed changes.
11. Historical categorization improves future accuracy.
12. The workflow can eventually run automatically every month.