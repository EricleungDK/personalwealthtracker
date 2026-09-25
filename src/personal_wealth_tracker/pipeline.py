from __future__ import annotations

from pathlib import Path
from datetime import date

from .categorizer import categorize_transactions
from .category_memory import learn_committed_month, load_category_memory, load_reviewed_policy
from .config import load_config, register_category_registry_additions
from .local_llm import apply_suggestions, disabled_diagnostics, local_consensus
from .models import CategoryRegistryAddition, RunResult
from .reporting import write_outputs
from .review_decisions import (
    MonthlyReviewDecision,
    apply_monthly_review_decisions,
    load_monthly_review_decisions,
    validate_monthly_review_decision_categories,
)
from .statement_adapters import import_trusted_statement
from .suggester import Suggester, build_suggester_context
from .trust_policy import apply_trust_policy
from .utils import normalize_month
from .workbook import (
    commit_updates,
    create_backup,
    plan_workbook_changes,
    rows_in_review,
    workbook_category_options,
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


def run_pipeline(
    tracker_path: Path,
    statement_path: Path,
    config_dir: Path,
    year: int,
    month: str,
    output_dir: Path,
    commit: bool = False,
    category_memory_dir: Path = Path("data/category_memory"),
    statement_format: str = "auto",
    review_decisions_path: Path | None = None,
    local_llm_suggestions: bool = False,
    suggester: Suggester | None = None,
) -> RunResult:
    month = normalize_month(month)
    config = load_config(config_dir)

    if config.tracker_currency.upper() != config.statement_currency.upper():
        raise ValueError(
            f"Tracker currency {config.tracker_currency!r} must match statement currency "
            f"{config.statement_currency!r} for MVP 1."
        )

    statement_import = import_trusted_statement(
        statement_path,
        statement_format=statement_format,
        expected_currency=config.statement_currency,
        year=year,
        month=month,
    )
    statement_parser = statement_import.parser_identity
    transactions = statement_import.transactions
    category_memory = load_category_memory(category_memory_dir)
    categorized = categorize_transactions(
        transactions,
        config,
        category_memory=category_memory,
    )
    category_registry_additions: tuple[CategoryRegistryAddition, ...] = ()
    review_decisions: dict[str, MonthlyReviewDecision] = {}
    if review_decisions_path is not None:
        review_decisions = load_monthly_review_decisions(review_decisions_path, year, month)
        category_registry_additions = _category_registry_additions(review_decisions)
        if category_registry_additions:
            category_registry_additions = register_category_registry_additions(
                config_dir,
                category_registry_additions,
            )
            config = load_config(config_dir)
        valid_categories = {
            option.category
            for option in workbook_category_options(tracker_path, year, month, config)
        } | set(config.category_registry.leaf_categories)
        validate_monthly_review_decision_categories(review_decisions, valid_categories)
        categorized = apply_trust_policy(
            apply_monthly_review_decisions(categorized, review_decisions),
            config,
        )
    local_llm_diagnostics = disabled_diagnostics(config.local_llm)
    if local_llm_suggestions:
        categorized, local_llm_diagnostics = apply_suggestions(
            categorized,
            config,
            suggester or local_consensus(config.local_llm),
            build_suggester_context(
                config,
                category_memory,
                reviewed_policy=load_reviewed_policy(category_memory_dir),
            ),
        )
    workbook_plan = plan_workbook_changes(tracker_path, categorized, year, month, config)
    updates = workbook_plan.updates
    structure_changes = workbook_plan.structure_changes
    mode = "commit" if commit else "dry-run"
    review_count = len(rows_in_review(categorized, updates))

    output_workbook_path = None
    if commit and not review_count:
        create_backup(tracker_path, Path("data/backups"))
        output_workbook_path = commit_updates(
            tracker_path,
            updates,
            config,
            Path("data/processed"),
            structure_changes=structure_changes,
        )
        learn_committed_month(
            category_memory_dir,
            categorized,
            review_decisions,
            f"{year}-{month}",
            frozenset(config.category_registry.leaf_categories) - config.fixed_rows,
        )

    (
        report_path,
        audit_path,
        categorized_csv_path,
        review_csv_path,
        review_xlsx_path,
    ) = write_outputs(
        output_dir=output_dir,
        mode=mode,
        year=year,
        month=month,
        source_statement=statement_path,
        tracker_path=tracker_path,
        categorized=categorized,
        updates=updates,
        structure_changes=structure_changes,
        statement_parser=statement_parser,
        workbook_config=config,
        category_registry_additions=category_registry_additions,
        local_llm_diagnostics=local_llm_diagnostics,
        review_xlsx_path=_review_xlsx_output_path(
            output_dir,
            year,
            month,
            review_decisions_path,
        ),
    )

    return RunResult(
        mode=mode,
        target_year=year,
        target_month=month,
        statement_parser=statement_parser,
        transactions=transactions,
        categorized_transactions=categorized,
        updates=updates,
        structure_changes=structure_changes,
        report_path=report_path,
        audit_path=audit_path,
        categorized_csv_path=categorized_csv_path,
        review_csv_path=review_csv_path,
        output_workbook_path=output_workbook_path,
        review_xlsx_path=review_xlsx_path,
        review_count=review_count,
        category_registry_additions=category_registry_additions,
        local_llm_diagnostics=local_llm_diagnostics,
        statement_import_diagnostics=statement_import.diagnostics,
    )


def _category_registry_additions(review_decisions) -> tuple[CategoryRegistryAddition, ...]:
    additions_by_category: dict[tuple[str, str], list[str]] = {}
    for decision in review_decisions.values():
        if not decision.new_leaf_category:
            continue
        key = (decision.new_parent_category, decision.new_leaf_category)
        additions_by_category.setdefault(key, []).append(decision.transaction_id)
    return tuple(
        CategoryRegistryAddition(
            parent_category=parent_category,
            leaf_category=leaf_category,
            source_transaction_ids=tuple(transaction_ids),
        )
        for (parent_category, leaf_category), transaction_ids in additions_by_category.items()
    )


def _validate_target_period(transactions, year: int, month: str) -> None:
    month = normalize_month(month)
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


def _review_xlsx_output_path(
    output_dir: Path,
    year: int,
    month: str,
    review_decisions_path: Path | None,
) -> Path | None:
    if review_decisions_path is None:
        return None

    default_path = output_dir / f"review_required_{year}_{month.lower()}.xlsx"
    if review_decisions_path.resolve() != default_path.resolve():
        return None
    return output_dir / f"review_required_{year}_{month.lower()}_after_decisions.xlsx"
