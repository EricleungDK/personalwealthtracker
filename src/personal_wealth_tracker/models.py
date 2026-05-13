from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    date: date
    interest_date: date | None
    description: str
    amount: Decimal
    currency: str
    direction: str
    balance: Decimal | None = None
    merchant: str | None = None
    account_name: str | None = None
    source_file: Path | None = None
    original_amount: Decimal | None = None
    original_currency: str | None = None
    details: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CategorizedTransaction:
    transaction: Transaction
    suggested_category: str | None
    confidence: float
    categorization_method: str
    review_required: bool
    reason: str


@dataclass(frozen=True)
class TrackerUpdate:
    year: int
    month: str
    category: str
    amount: Decimal
    source_transactions: tuple[str, ...]
    target_row: int | None
    target_column: int | None
    target_cell: str | None
    existing_value: str | int | float | None
    write_action: str
    reason: str


@dataclass(frozen=True)
class WorkbookStructureChange:
    change_type: str
    target_year: int
    target_months: tuple[str, ...]
    source_range: str | None
    target_range: str | None
    write_action: str
    reason: str


@dataclass(frozen=True)
class WorkbookPlan:
    updates: list[TrackerUpdate]
    structure_changes: list[WorkbookStructureChange]


@dataclass(frozen=True)
class RunResult:
    mode: str
    target_year: int
    target_month: str
    transactions: list[Transaction]
    categorized_transactions: list[CategorizedTransaction]
    updates: list[TrackerUpdate]
    structure_changes: list[WorkbookStructureChange]
    report_path: Path
    audit_path: Path
    categorized_csv_path: Path
    review_csv_path: Path
    output_workbook_path: Path | None = None
