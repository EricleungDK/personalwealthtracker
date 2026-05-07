# Architecture

Last updated: 2026-05-07

## Runtime Flow

1. CLI receives tracker path, Nordea PDF path, target year/month, config directory, output directory, and optional commit flag.
2. Config is loaded from YAML files in `config/`.
3. `nordea_pdf.py` extracts text with coordinates from the Nordea PDF and reconstructs transaction rows from the `Dato`, `Rentedato`, `Detaljer`, `Beløb`, and `Saldo` columns.
4. The statement currency is validated against config before transactions are normalized.
5. `categorizer.py` applies historical mappings first, then recurring amount/date rules, then keyword rules.
6. The pipeline rejects statements containing transactions outside the requested target month.
7. `workbook.py` locates the `Net worth` sheet, target month column, and category rows.
8. `reporting.py` writes report, audit, categorized CSV, and review CSV outputs.
9. Commit mode creates a backup and writes eligible updates to a copied workbook only.

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

Commit mode writes only planned updates whose action is `write`.

## Future Extension Points

- Additional statement parsers can be added beside `nordea_pdf.py`.
- Bank API ingestion can feed the same normalized transaction model.
- Local LLM classification can be added after deterministic rules fail.
- Google Drive integration can wrap workbook download/upload while preserving the same writer safeguards.
