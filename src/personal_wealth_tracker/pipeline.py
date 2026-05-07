from __future__ import annotations

from datetime import date
from pathlib import Path

from .categorizer import categorize_transactions
from .config import load_config
from .models import RunResult, Transaction
from .nordea_pdf import parse_nordea_pdf
from .reporting import write_outputs
from .utils import normalize_month
from .workbook import commit_updates, create_backup, plan_updates


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


def run_pipeline(
    tracker_path: Path,
    statement_path: Path,
    config_dir: Path,
    year: int,
    month: str,
    output_dir: Path,
    commit: bool = False,
) -> RunResult:
    month = normalize_month(month)
    config = load_config(config_dir)

    if config.tracker_currency.upper() != config.statement_currency.upper():
        raise ValueError(
            f"Tracker currency {config.tracker_currency!r} must match statement currency "
            f"{config.statement_currency!r} for MVP 1."
        )

    transactions = parse_nordea_pdf(statement_path, expected_currency=config.statement_currency)
    _validate_target_period(transactions, year, month)
    categorized = categorize_transactions(transactions, config)
    updates = plan_updates(tracker_path, categorized, year, month, config)
    mode = "commit" if commit else "dry-run"

    output_workbook_path = None
    if commit:
        create_backup(tracker_path, Path("data/backups"))
        output_workbook_path = commit_updates(tracker_path, updates, config, Path("data/processed"))

    report_path, audit_path, categorized_csv_path, review_csv_path = write_outputs(
        output_dir=output_dir,
        mode=mode,
        year=year,
        month=month,
        source_statement=statement_path,
        tracker_path=tracker_path,
        categorized=categorized,
        updates=updates,
    )

    return RunResult(
        mode=mode,
        target_year=year,
        target_month=month,
        transactions=transactions,
        categorized_transactions=categorized,
        updates=updates,
        report_path=report_path,
        audit_path=audit_path,
        categorized_csv_path=categorized_csv_path,
        review_csv_path=review_csv_path,
        output_workbook_path=output_workbook_path,
    )


def _validate_target_period(transactions: list[Transaction], year: int, month: str) -> None:
    start, end = _target_period(year, month)
    out_of_period = [
        transaction for transaction in transactions if not (start <= transaction.date < end)
    ]
    if not out_of_period:
        return

    dates = [transaction.date for transaction in out_of_period]
    raise ValueError(
        f"Statement contains {len(out_of_period)} transaction(s) outside target period "
        f"{month} {year}: {min(dates).isoformat()} to {max(dates).isoformat()}."
    )


def _target_period(year: int, month: str) -> tuple[date, date]:
    month_number = MONTH_NUMBERS[month]
    start = date(year, month_number, 1)
    if month_number == 12:
        return start, date(year + 1, 1, 1)
    return start, date(year, month_number + 1, 1)
