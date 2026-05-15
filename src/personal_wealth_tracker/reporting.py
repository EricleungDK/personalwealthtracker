from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from .models import CategorizedTransaction, TrackerUpdate, WorkbookStructureChange


def write_outputs(
    output_dir: Path,
    mode: str,
    year: int,
    month: str,
    source_statement: Path,
    tracker_path: Path,
    categorized: list[CategorizedTransaction],
    updates: list[TrackerUpdate],
    structure_changes: list[WorkbookStructureChange] | None = None,
    statement_parser: str = "nordea-pdf",
) -> tuple[Path, Path, Path, Path]:
    structure_changes = structure_changes or []
    output_dir.mkdir(parents=True, exist_ok=True)
    period = f"{year}_{month.lower()}"
    report_path = output_dir / f"report_{period}.md"
    audit_path = output_dir / f"audit_{period}.jsonl"
    categorized_path = output_dir / f"categorized_transactions_{period}.csv"
    review_path = output_dir / f"review_required_{period}.csv"

    _write_report(
        report_path,
        mode,
        year,
        month,
        statement_parser,
        categorized,
        updates,
        structure_changes,
    )
    _write_audit(
        audit_path,
        mode,
        year,
        month,
        source_statement,
        statement_parser,
        tracker_path,
        categorized,
        updates,
        structure_changes,
    )
    _write_categorized_csv(categorized_path, categorized)
    _write_review_csv(review_path, categorized, updates)
    return report_path, audit_path, categorized_path, review_path


def _write_report(
    path: Path,
    mode: str,
    year: int,
    month: str,
    statement_parser: str,
    categorized: list[CategorizedTransaction],
    updates: list[TrackerUpdate],
    structure_changes: list[WorkbookStructureChange],
) -> None:
    total = len(categorized)
    review_count = sum(1 for item in categorized if item.review_required)
    write_count = sum(1 for update in updates if update.write_action == "write")
    skip_count = sum(1 for update in updates if update.write_action == "skip")

    lines = [
        "# Monthly Wealth Tracker Automation Report",
        "",
        f"- Reporting month: {month} {year}",
        f"- Mode: {mode}",
        f"- Statement parser: {statement_parser}",
        f"- Transactions processed: {total}",
        f"- Transactions requiring review: {review_count}",
        f"- Proposed workbook writes: {write_count}",
        f"- Skipped workbook updates: {skip_count}",
        "- Workbook cleanup tasks: not run during monthly update.",
        "",
        "## Planned Structure Changes",
        "",
    ]

    if structure_changes:
        for change in structure_changes:
            target_months = ", ".join(
                f"{month} {change.target_year}" for month in change.target_months
            )
            lines.append(
                f"- {change.change_type}: {target_months}, "
                f"{change.source_range or 'unresolved'} -> {change.target_range or 'unresolved'} "
                f"({change.write_action}; {change.reason})"
            )
    else:
        lines.append("- No workbook structure changes planned.")

    lines.extend(
        [
            "",
            "## Proposed Updates",
            "",
        ]
    )

    if updates:
        categorized_by_id = {
            item.transaction.transaction_id: item
            for item in categorized
        }
        for update in updates:
            lines.append(
                f"- {update.category}: {update.amount} -> {update.target_cell or 'unresolved'} "
                f"({update.write_action}; {update.reason})"
            )
            for transaction_id in update.source_transactions:
                item = categorized_by_id.get(transaction_id)
                if item is None:
                    continue
                lines.append(
                    f"  - Source {transaction_id}: {item.transaction.amount} DKK, "
                    f"{item.reason}"
                )
    else:
        lines.append("- No categorized updates were produced.")

    lines.extend(["", "## Review Required", ""])
    review_items = [item for item in categorized if item.review_required]
    if review_items:
        for item in review_items:
            category = item.suggested_category or "Unmatched"
            lines.append(
                f"- {item.transaction.date}: {item.transaction.amount} DKK, "
                f"{category}, confidence {item.confidence:.2f}, {item.reason}"
            )
    else:
        lines.append("- No transaction-level review items.")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_audit(
    path: Path,
    mode: str,
    year: int,
    month: str,
    source_statement: Path,
    statement_parser: str,
    tracker_path: Path,
    categorized: list[CategorizedTransaction],
    updates: list[TrackerUpdate],
    structure_changes: list[WorkbookStructureChange],
) -> None:
    update_by_transaction = {
        transaction_id: update
        for update in updates
        for transaction_id in update.source_transactions
    }
    timestamp = datetime.now().isoformat(timespec="seconds")
    with path.open("w", encoding="utf-8") as handle:
        for change in structure_changes:
            payload = {
                "record_type": "workbook_structure_change",
                "run_timestamp": timestamp,
                "mode": mode,
                "statement_parser": statement_parser,
                "source_statement": str(source_statement),
                "target_workbook": str(tracker_path),
                "target_year": year,
                "target_month": month,
                "change_type": change.change_type,
                "target_structure_year": change.target_year,
                "target_months": list(change.target_months),
                "source_range": change.source_range,
                "target_range": change.target_range,
                "action": change.write_action,
                "reason": change.reason,
            }
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        for item in categorized:
            transaction = item.transaction
            update = update_by_transaction.get(transaction.transaction_id)
            payload = {
                "record_type": "transaction",
                "run_timestamp": timestamp,
                "mode": mode,
                "statement_parser": statement_parser,
                "source_statement": str(source_statement),
                "target_workbook": str(tracker_path),
                "target_year": year,
                "target_month": month,
                "transaction_id": transaction.transaction_id,
                "transaction_date": transaction.date.isoformat(),
                "description": transaction.description,
                "amount": str(transaction.amount),
                "currency": transaction.currency,
                "suggested_category": item.suggested_category,
                "confidence": item.confidence,
                "categorization_method": item.categorization_method,
                "target_row": update.target_row if update else None,
                "target_cell": update.target_cell if update else None,
                "action": update.write_action if update else "review_required",
                "reason": update.reason if update else item.reason,
            }
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _write_categorized_csv(path: Path, categorized: list[CategorizedTransaction]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "transaction_id",
                "date",
                "description",
                "amount",
                "currency",
                "direction",
                "category",
                "confidence",
                "method",
                "review_required",
            ]
        )
        for item in categorized:
            transaction = item.transaction
            writer.writerow(
                [
                    transaction.transaction_id,
                    transaction.date.isoformat(),
                    transaction.description,
                    transaction.amount,
                    transaction.currency,
                    transaction.direction,
                    item.suggested_category or "",
                    f"{item.confidence:.2f}",
                    item.categorization_method,
                    item.review_required,
                ]
            )


def _write_review_csv(
    path: Path, categorized: list[CategorizedTransaction], updates: list[TrackerUpdate]
) -> None:
    update_by_transaction = {
        transaction_id: update
        for update in updates
        for transaction_id in update.source_transactions
    }
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["type", "id", "date_or_cell", "amount", "category", "reason"])
        for item in categorized:
            if item.review_required:
                transaction = item.transaction
                writer.writerow(
                    [
                        "transaction",
                        transaction.transaction_id,
                        transaction.date.isoformat(),
                        transaction.amount,
                        item.suggested_category or "",
                        item.reason,
                    ]
                )
        for update in updates:
            if update.write_action != "write":
                writer.writerow(
                    [
                        "workbook_update",
                        ",".join(update.source_transactions),
                        update.target_cell or "",
                        update.amount,
                        update.category,
                        update.reason,
                    ]
                )
