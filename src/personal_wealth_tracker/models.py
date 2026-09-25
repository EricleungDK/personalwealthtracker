from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from pathlib import Path


class Authority(str, Enum):
    auto = "auto"
    review = "review"


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
class Vote:
    category: str | None
    confidence: float
    source: str


@dataclass(frozen=True)
class CategorizedTransaction:
    transaction: Transaction
    suggested_category: str | None
    confidence: float
    categorization_method: str
    reason: str
    authority: Authority = Authority.review
    authority_reason: str = ""
    votes: tuple[Vote, ...] = ()
    source_transaction_id: str | None = None
    split_rule: str | None = None
    split_role: str | None = None
    allocated_amount: Decimal | None = None
    residual_amount: Decimal | None = None

    @property
    def review_required(self) -> bool:
        return self.authority is Authority.review


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
    parent_category: str | None = None
    leaf_category: str | None = None


@dataclass(frozen=True)
class CategoryRegistryAddition:
    parent_category: str
    leaf_category: str
    source_transaction_ids: tuple[str, ...]


@dataclass(frozen=True)
class LocalLLMDiagnostics:
    enabled: bool = False
    provider: str = "ollama"
    endpoint: str = "http://localhost:11434"
    model: str = "gemma4:12b"
    fallback_model: str = "gemma4:e4b"
    active_model: str | None = None
    eligible_count: int = 0
    attempted_count: int = 0
    existing_leaf_suggestions: int = 0
    no_suggestion_count: int = 0
    low_confidence_response_count: int = 0
    invalid_response_count: int = 0
    provider_failure_count: int = 0
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class StatementImportDiagnostic:
    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class WorkbookPlan:
    updates: list[TrackerUpdate]
    structure_changes: list[WorkbookStructureChange]


@dataclass(frozen=True)
class RunResult:
    mode: str
    target_year: int
    target_month: str
    statement_parser: str
    transactions: list[Transaction]
    categorized_transactions: list[CategorizedTransaction]
    updates: list[TrackerUpdate]
    structure_changes: list[WorkbookStructureChange]
    report_path: Path
    audit_path: Path
    categorized_csv_path: Path
    review_csv_path: Path
    output_workbook_path: Path | None = None
    review_xlsx_path: Path | None = None
    category_registry_additions: tuple[CategoryRegistryAddition, ...] = ()
    local_llm_diagnostics: LocalLLMDiagnostics = field(default_factory=LocalLLMDiagnostics)
    statement_import_diagnostics: tuple[StatementImportDiagnostic, ...] = ()
