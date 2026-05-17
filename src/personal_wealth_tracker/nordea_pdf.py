from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from .models import Transaction
from .utils import assign_stable_transaction_ids, parse_danish_date, parse_danish_decimal


DATE_RE = re.compile(r"^\d{2}\.\d{2}(?:\.\d{2,4})?$")
AMOUNT_RE = re.compile(r"^-?\d{1,3}(?:\.\d{3})*,\d{2}$|^-?\d+,\d{2}$")
PERIOD_RE = re.compile(r"Periode:\s*(\d{2}\.\d{2}\.(\d{4}))\s*-\s*(\d{2}\.\d{2}\.(\d{4}))")
STATEMENT_CURRENCY_RE = re.compile(r"Valuta:\s*([A-Z]{3})")
FOREIGN_AMOUNT_RE = re.compile(r"(?P<rate>\d+,\d+)\s+(?P<currency>[A-Z]{3})\s+(?P<amount>-?\d+(?:\.\d{3})*,\d{2})")
FOOTER_MARKERS = (
    "er der korttransaktioner",
    "indsigelse",
    "nordea danmark",
    "patent- og registreringsstyrelsen",
    "cvr-nr",
    "slutsaldo",
    "ultimo",
)


@dataclass(frozen=True)
class TextCell:
    text: str
    x0: float
    top: float


@dataclass(frozen=True)
class TransactionLine:
    date_text: str
    interest_date_text: str | None
    details: tuple[str, ...]
    amount_text: str
    balance_text: str | None


def parse_nordea_pdf(path: Path, expected_currency: str = "DKK") -> list[Transaction]:
    pages = _extract_pages(path)
    statement_currency = _extract_statement_currency(pages)
    expected_currency = expected_currency.upper()
    if statement_currency != expected_currency:
        raise ValueError(
            f"Nordea statement currency {statement_currency!r} does not match "
            f"expected currency {expected_currency!r}."
        )

    period_start, period_end = _extract_statement_period(pages)
    raw_lines: list[TransactionLine] = []

    for page in pages:
        raw_lines.extend(_extract_transaction_lines(page, period_start.year, period_end.year))

    transactions: list[Transaction] = []
    for line in raw_lines:
        amount = parse_danish_decimal(line.amount_text)
        balance = parse_danish_decimal(line.balance_text) if line.balance_text else None
        booked_date = _parse_statement_row_date(line.date_text, period_start, period_end)
        interest_date = (
            _parse_statement_row_date(line.interest_date_text, period_start, period_end)
            if line.interest_date_text
            else None
        )
        description = " ".join(part for part in line.details if part).strip()
        original_amount, original_currency = _extract_original_amount(description)
        transactions.append(
            Transaction(
                transaction_id="",
                date=booked_date,
                interest_date=interest_date,
                description=description,
                amount=amount,
                currency=statement_currency,
                direction="income" if amount >= Decimal("0") else "expense",
                balance=balance,
                merchant=_derive_merchant(description),
                source_file=path,
                original_amount=original_amount,
                original_currency=original_currency,
                details=line.details,
            )
        )

    return assign_stable_transaction_ids(transactions)


def _extract_pages(path: Path) -> list[list[TextCell]]:
    try:
        import pdfplumber
    except ImportError as exc:
        raise RuntimeError("pdfplumber is required for PDF parsing. Install with `uv sync`.") from exc

    pages: list[list[TextCell]] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(
                keep_blank_chars=False,
                use_text_flow=False,
                extra_attrs=[],
            )
            cells = [
                TextCell(text=str(word["text"]), x0=float(word["x0"]), top=float(word["top"]))
                for word in words
            ]
            pages.append(cells)
    return pages


def _extract_period_year(pages: list[list[TextCell]]) -> int:
    _, period_end = _extract_statement_period(pages)
    return period_end.year


def _extract_statement_period(pages: list[list[TextCell]]) -> tuple[date, date]:
    text = " ".join(cell.text for page in pages for cell in page)
    match = PERIOD_RE.search(text)
    if not match:
        raise ValueError("Could not find Nordea statement period.")
    return parse_danish_date(match.group(1)), parse_danish_date(match.group(3))


def _extract_statement_currency(pages: list[list[TextCell]]) -> str:
    text = " ".join(cell.text for page in pages for cell in page)
    match = STATEMENT_CURRENCY_RE.search(text)
    if not match:
        raise ValueError("Could not find Nordea statement currency marker.")
    return match.group(1).upper()


def _extract_transaction_lines(
    page: list[TextCell], fallback_start_year: int, fallback_end_year: int | None = None
) -> list[TransactionLine]:
    rows = _group_rows(page)
    header = _find_header(rows)
    if header is None:
        return []

    header_top, header_cells = header
    anchors = _column_anchors(header_cells)
    lines: list[TransactionLine] = []
    current: dict[str, object] | None = None

    for top, cells in rows:
        if top <= header_top:
            continue
        classified = _classify_row(cells, anchors)
        date_text = classified.get("date")
        amount_text = classified.get("amount")

        if date_text and amount_text:
            if current is not None:
                lines.append(_line_from_current(current))
            current = {
                "date_text": date_text,
                "interest_date_text": classified.get("interest_date"),
                "details": list(classified.get("details", [])),
                "amount_text": amount_text,
                "balance_text": classified.get("balance"),
            }
            continue

        details = classified.get("details")
        if current is not None and details:
            if _is_footer_row(cells):
                break
            if not _is_detail_continuation_row(cells, anchors):
                continue
            current_details = current["details"]
            assert isinstance(current_details, list)
            current_details.extend(details)

    if current is not None:
        lines.append(_line_from_current(current))

    valid_lines: list[TransactionLine] = []
    for line in lines:
        try:
            parse_danish_date(line.date_text, fallback_end_year or fallback_start_year)
            parse_danish_decimal(line.amount_text)
        except ValueError:
            continue
        valid_lines.append(line)
    return valid_lines


def _group_rows(cells: list[TextCell], tolerance: float = 3.0) -> list[tuple[float, list[TextCell]]]:
    rows: list[tuple[float, list[TextCell]]] = []
    for cell in sorted(cells, key=lambda item: (item.top, item.x0)):
        for index, (top, row_cells) in enumerate(rows):
            if abs(cell.top - top) <= tolerance:
                row_cells.append(cell)
                rows[index] = ((top + cell.top) / 2, row_cells)
                break
        else:
            rows.append((cell.top, [cell]))

    return [(top, sorted(row_cells, key=lambda item: item.x0)) for top, row_cells in rows]


def _find_header(rows: list[tuple[float, list[TextCell]]]) -> tuple[float, list[TextCell]] | None:
    for top, cells in rows:
        labels = {_normalize_header_label(cell.text) for cell in cells}
        if {"dato", "rentedato", "detaljer", "beloeb", "saldo"}.issubset(labels):
            return top, cells
    return None


def _column_anchors(cells: list[TextCell]) -> dict[str, float]:
    anchors = {_normalize_header_label(cell.text): cell.x0 for cell in cells}
    return {
        "date": anchors["dato"],
        "interest_date": anchors["rentedato"],
        "details": anchors["detaljer"],
        "amount": anchors["beloeb"],
        "balance": anchors["saldo"],
    }


def _normalize_header_label(value: str) -> str:
    return value.strip().lower().replace("ø", "oe").replace("ö", "oe").replace("ó", "o")


def _classify_row(cells: list[TextCell], anchors: dict[str, float]) -> dict[str, object]:
    result: dict[str, object] = {"details": []}
    detail_parts: list[str] = []

    for cell in cells:
        target = _nearest_column(cell.x0, anchors)
        text = cell.text.strip()
        if not text:
            continue
        if target == "date" and DATE_RE.match(text):
            result["date"] = text
        elif target == "interest_date" and DATE_RE.match(text):
            result["interest_date"] = text
        elif target == "amount" and AMOUNT_RE.match(text):
            result["amount"] = text
        elif target == "balance" and AMOUNT_RE.match(text):
            result["balance"] = text
        else:
            detail_parts.append(text)

    if detail_parts:
        result["details"] = [" ".join(detail_parts)]
    return result


def _is_detail_continuation_row(cells: list[TextCell], anchors: dict[str, float]) -> bool:
    detail_start = anchors["details"]
    next_column_start = anchors["amount"]
    return any(detail_start <= cell.x0 < next_column_start for cell in cells)


def _is_footer_row(cells: list[TextCell]) -> bool:
    text = " ".join(cell.text for cell in cells).strip().lower()
    return any(marker in text for marker in FOOTER_MARKERS)


def _nearest_column(x0: float, anchors: dict[str, float]) -> str:
    ordered = sorted(anchors.items(), key=lambda item: item[1])
    selected = ordered[0][0]
    for name, anchor_x in ordered:
        if x0 >= anchor_x:
            selected = name
        else:
            break
    return selected


def _line_from_current(current: dict[str, object]) -> TransactionLine:
    return TransactionLine(
        date_text=str(current["date_text"]),
        interest_date_text=(
            str(current["interest_date_text"]) if current.get("interest_date_text") else None
        ),
        details=tuple(str(item) for item in current.get("details", [])),
        amount_text=str(current["amount_text"]),
        balance_text=str(current["balance_text"]) if current.get("balance_text") else None,
    )


def _parse_statement_row_date(value: str, period_start: date, period_end: date) -> date:
    for year in {period_start.year, period_end.year}:
        try:
            parsed = parse_danish_date(value, year)
        except ValueError:
            continue
        if period_start <= parsed <= period_end:
            return parsed
    return parse_danish_date(value, period_end.year)


def _extract_original_amount(description: str) -> tuple[Decimal | None, str | None]:
    match = FOREIGN_AMOUNT_RE.search(description)
    if not match:
        return None, None
    return parse_danish_decimal(match.group("amount")), match.group("currency")


def _derive_merchant(description: str) -> str | None:
    first_line = description.split("  ")[0].strip()
    if not first_line:
        return None
    return first_line[:80]
