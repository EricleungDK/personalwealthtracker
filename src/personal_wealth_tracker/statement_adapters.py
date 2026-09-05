from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable

from .models import StatementImportDiagnostic, Transaction
from .nordea_csv import parse_nordea_csv
from .nordea_pdf import parse_nordea_pdf
from .utils import normalize_month


NORMALIZED_TRANSACTION_FIELDS = (
    "transaction_id",
    "date",
    "amount",
    "currency",
    "description",
    "direction",
    "source_file",
)

MONTH_NUMBERS = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


class StatementImportError(ValueError):
    def __init__(
        self,
        message: str,
        diagnostics: tuple[StatementImportDiagnostic, ...],
    ) -> None:
        super().__init__(message)
        self.diagnostics = diagnostics


@dataclass(frozen=True)
class TrustedStatementAdapter:
    name: str
    parser_identity: str
    extensions: tuple[str, ...]
    parse: Callable[[Path, str], list[Transaction]]


@dataclass(frozen=True)
class TrustedStatementImport:
    adapter_name: str
    parser_identity: str
    source_statement: Path
    transactions: list[Transaction]
    diagnostics: tuple[StatementImportDiagnostic, ...]


def import_trusted_statement(
    statement_path: Path,
    *,
    statement_format: str,
    expected_currency: str,
    year: int,
    month: str,
) -> TrustedStatementImport:
    month = normalize_month(month)
    adapter = resolve_statement_adapter(statement_path, statement_format)
    try:
        transactions = adapter.parse(statement_path, expected_currency.upper())
    except ValueError as exc:
        diagnostics = (
            StatementImportDiagnostic(
                severity="error",
                code=_parser_failure_code(str(exc)),
                message=str(exc),
            ),
        )
        raise StatementImportError(str(exc), diagnostics) from exc

    diagnostics = _duplicate_row_diagnostics(transactions) + _period_diagnostics(
        transactions,
        year,
        month,
    )
    errors = tuple(diagnostic for diagnostic in diagnostics if diagnostic.severity == "error")
    if errors:
        raise StatementImportError("; ".join(diagnostic.message for diagnostic in errors), errors)

    return TrustedStatementImport(
        adapter_name=adapter.name,
        parser_identity=adapter.parser_identity,
        source_statement=statement_path,
        transactions=transactions,
        diagnostics=diagnostics,
    )


def resolve_statement_adapter(statement_path: Path, statement_format: str) -> TrustedStatementAdapter:
    adapters = _trusted_statement_adapters()
    if statement_format != "auto":
        if statement_format in adapters:
            return adapters[statement_format]
        raise ValueError(
            "Unsupported statement format "
            f"{statement_format!r}. Use auto, nordea-csv, or nordea-pdf."
        )

    suffix = statement_path.suffix.lower()
    for adapter in adapters.values():
        if suffix in adapter.extensions:
            return adapter
    raise ValueError(
        f"Could not infer statement format from {statement_path.name!r}. "
        "Use --statement-format nordea-csv or --statement-format nordea-pdf."
    )


def _trusted_statement_adapters() -> dict[str, TrustedStatementAdapter]:
    return {
        "nordea-csv": TrustedStatementAdapter(
            name="nordea-csv",
            parser_identity="nordea-csv",
            extensions=(".csv",),
            parse=_parse_nordea_csv,
        ),
        "nordea-pdf": TrustedStatementAdapter(
            name="nordea-pdf",
            parser_identity="nordea-pdf",
            extensions=(".pdf",),
            parse=_parse_nordea_pdf,
        ),
    }


def _parse_nordea_csv(path: Path, expected_currency: str) -> list[Transaction]:
    return parse_nordea_csv(path, expected_currency=expected_currency)


def _parse_nordea_pdf(path: Path, expected_currency: str) -> list[Transaction]:
    return parse_nordea_pdf(path, expected_currency=expected_currency)


def _duplicate_row_diagnostics(
    transactions: list[Transaction],
) -> tuple[StatementImportDiagnostic, ...]:
    counts = Counter(_duplicate_fingerprint(transaction) for transaction in transactions)
    diagnostics: list[StatementImportDiagnostic] = []
    for fingerprint, count in counts.items():
        if count <= 1:
            continue
        diagnostics.append(
            StatementImportDiagnostic(
                severity="warning",
                code="duplicate_row",
                message=(
                    "Duplicate normalized transaction row detected "
                    f"({count} occurrences): {fingerprint[0]} {fingerprint[1]} "
                    f"{fingerprint[2]} {fingerprint[3]}."
                ),
            )
        )
    return tuple(diagnostics)


def _period_diagnostics(
    transactions: list[Transaction],
    year: int,
    month: str,
) -> tuple[StatementImportDiagnostic, ...]:
    start, end = _target_period(year, month)
    out_of_period = [
        transaction for transaction in transactions if not (start <= transaction.date < end)
    ]
    if not out_of_period:
        return ()

    dates = [transaction.date for transaction in out_of_period]
    return (
        StatementImportDiagnostic(
            severity="error",
            code="out_of_period",
            message=(
                f"Statement contains {len(out_of_period)} transaction(s) outside target period "
                f"{month} {year}: {min(dates).isoformat()} to {max(dates).isoformat()}."
            ),
        ),
    )


def _target_period(year: int, month: str) -> tuple[date, date]:
    month_number = MONTH_NUMBERS[month]
    start = date(year, month_number, 1)
    if month_number == 12:
        return start, date(year + 1, 1, 1)
    return start, date(year, month_number + 1, 1)


def _parser_failure_code(message: str) -> str:
    normalized = message.lower()
    if "currency" in normalized or "valuta" in normalized:
        return "unsupported_currency"
    return "adapter_failure"


def _duplicate_fingerprint(transaction: Transaction) -> tuple[str, str, str, str, str]:
    return (
        transaction.date.isoformat(),
        str(transaction.amount),
        transaction.currency,
        transaction.description,
        str(transaction.balance or ""),
    )
