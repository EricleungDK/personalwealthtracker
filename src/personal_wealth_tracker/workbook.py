from __future__ import annotations

import shutil
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from .config import AppConfig
from .models import CategorizedTransaction, TrackerUpdate


DERIVED_WORKBOOK_ROWS = frozenset(
    {
        "Income (net)",
        "Labour market contribution",
        "Taxes",
        "Cashflow",
        "Recurring payments",
        "Living expenses",
        "Services",
        "Insurance",
        "Investments",
        "Assets",
        "Total net worth",
    }
)
NET_SALARY_ROW = "Full-time job (net)"
EXPENSE_CLAIMS_ROW = "Expense claims"
INCOME_LIKE_ROWS = frozenset({NET_SALARY_ROW, EXPENSE_CLAIMS_ROW})


def plan_updates(
    tracker_path: Path,
    categorized: list[CategorizedTransaction],
    year: int,
    month: str,
    config: AppConfig,
) -> list[TrackerUpdate]:
    workbook, sheet = _load_sheet(tracker_path, config.sheet_name)
    category_rows = _category_rows(sheet, config.category_column)
    target_column = _target_month_column(sheet, year, month, config)

    grouped: dict[str, list[CategorizedTransaction]] = defaultdict(list)
    for item in categorized:
        if not item.suggested_category:
            continue
        grouped[item.suggested_category].append(item)

    updates: list[TrackerUpdate] = []
    for category, items in sorted(grouped.items()):
        amount = _category_amount(category, items)
        row = category_rows.get(category)
        cell = sheet.cell(row=row, column=target_column) if row and target_column else None
        existing_value = cell.value if cell else None
        action, reason = _write_decision(category, row, target_column, existing_value, items, config)
        updates.append(
            TrackerUpdate(
                year=year,
                month=month,
                category=category,
                amount=amount,
                source_transactions=tuple(item.transaction.transaction_id for item in items),
                target_row=row,
                target_column=target_column,
                target_cell=cell.coordinate if cell else None,
                existing_value=existing_value,
                write_action=action,
                reason=reason,
            )
        )

    workbook.close()
    return updates


def _category_amount(category: str, items: list[CategorizedTransaction]) -> Decimal:
    signed_total = sum((item.transaction.amount for item in items), Decimal("0"))
    if category in INCOME_LIKE_ROWS:
        return signed_total
    return -signed_total


def commit_updates(
    tracker_path: Path,
    updates: list[TrackerUpdate],
    config: AppConfig,
    output_dir: Path,
) -> Path:
    workbook, sheet = _load_sheet(tracker_path, config.sheet_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"{tracker_path.stem}_auto_{timestamp}{tracker_path.suffix}"

    for update in updates:
        if update.write_action != "write" or update.target_row is None or update.target_column is None:
            continue
        sheet.cell(row=update.target_row, column=update.target_column).value = float(update.amount)

    workbook.save(output_path)
    workbook.close()
    return output_path


def create_backup(tracker_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{tracker_path.stem}_backup_{timestamp}{tracker_path.suffix}"
    shutil.copy2(tracker_path, backup_path)
    return backup_path


def _load_sheet(tracker_path: Path, sheet_name: str):
    try:
        import openpyxl
    except ImportError as exc:
        raise RuntimeError("openpyxl is required for workbook access. Install with `uv sync`.") from exc

    workbook = openpyxl.load_workbook(tracker_path)
    if sheet_name not in workbook.sheetnames:
        workbook.close()
        raise ValueError(f"Workbook does not contain sheet {sheet_name!r}.")
    return workbook, workbook[sheet_name]


def _category_rows(sheet, category_column: int) -> dict[str, int]:
    rows: dict[str, int] = {}
    for row in range(1, sheet.max_row + 1):
        value = sheet.cell(row=row, column=category_column).value
        if isinstance(value, str) and value.strip():
            rows[value.strip()] = row
    return rows


def _target_month_column(sheet, year: int, month: str, config: AppConfig) -> int:
    current_year: int | None = None
    for column in range(1, sheet.max_column + 1):
        year_value = sheet.cell(row=config.year_header_row, column=column).value
        if year_value not in (None, ""):
            try:
                current_year = int(year_value)
            except (TypeError, ValueError):
                current_year = None

        month_value = sheet.cell(row=config.month_header_row, column=column).value
        if current_year == year and str(month_value).strip().lower() == month.lower():
            return column

    raise ValueError(f"Could not find target column for {month} {year}.")


def _write_decision(
    category: str,
    row: int | None,
    column: int | None,
    existing_value: object,
    items: list[CategorizedTransaction],
    config: AppConfig,
) -> tuple[str, str]:
    if row is None:
        return "review", "Target category row not found."
    if column is None:
        return "review", "Target month column not found."
    if any(item.review_required for item in items):
        return "review", "One or more source transactions require review."
    if category in DERIVED_WORKBOOK_ROWS:
        return "skip", "Derived workbook row is formula-owned and not writable."
    if category in config.fixed_rows and not config.overwrite_fixed_rows:
        return "skip", "Fixed row is protected by config."
    if isinstance(existing_value, str) and existing_value.startswith("="):
        return "skip", "Target cell contains a formula."
    if existing_value not in (None, ""):
        return "review", "Target cell already contains a manual value."
    if category == NET_SALARY_ROW and len(items) > 1:
        return "review", "Multiple salary deposits matched; review before writing."
    return "write", "Eligible for commit mode write."
