# Architecture

Last updated: 2026-05-06

## Runtime Flow

1. CLI receives tracker path, Nordea PDF path, target year/month, config directory, output directory, and optional commit flag.
2. Config is loaded from YAML files in `config/`.
3. `nordea_pdf.py` extracts text with coordinates from the Nordea PDF and reconstructs transaction rows from the `Dato`, `Rentedato`, `Detaljer`, `Beløb`, and `Saldo` columns.
4. Transactions are normalized to DKK booked amounts and deterministic transaction IDs.
5. `categorizer.py` applies historical mappings first, then keyword rules.
6. `workbook.py` locates the `Net worth` sheet, target month column, and category rows.
7. `reporting.py` writes report, audit, categorized CSV, and review CSV outputs.
8. Commit mode creates a backup and writes eligible updates to a copied workbook only.

## Parser Design

The Nordea parser uses header anchors rather than fixed absolute coordinates. This handles the observed difference between the first page and continuation pages while staying specific to the known Nordea statement layout.

The parser assumes the PDF has embedded selectable text. Scanned PDFs and OCR are excluded from MVP 1.

## Safety Design

Workbook updates are planned before writing. A planned update becomes writable only when:

- the category row exists,
- the target month column exists,
- all source transactions are high-confidence,
- the category is not a protected fixed row,
- the target cell is empty,
- the target cell is not a formula.

Commit mode writes only planned updates whose action is `write`.

## Future Extension Points

- Additional statement parsers can be added beside `nordea_pdf.py`.
- Bank API ingestion can feed the same normalized transaction model.
- Local LLM classification can be added after deterministic rules fail.
- Google Drive integration can wrap workbook download/upload while preserving the same writer safeguards.
