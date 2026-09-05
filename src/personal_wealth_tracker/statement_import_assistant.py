from __future__ import annotations

import csv
import json
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from .category_memory import normalize_merchant_identity
from .importer_profiles import importer_profile_path
from .models import Transaction
from .utils import normalize_month, parse_danish_decimal


REVIEW_COLUMNS = (
    "review_required",
    "eligible_for_workbook_write",
    "source_row",
    "date",
    "amount",
    "currency",
    "description",
    "direction",
    "provenance",
    "confidence",
    "suggested_category",
    "guess_state",
    "guess_confidence",
    "guess_reason",
    "guess_profile",
    "source_format_changed",
    "validation_warnings",
    "confirmed",
    "confirmed_category",
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


@dataclass(frozen=True)
class ImportAssistantDiagnostic:
    severity: str
    code: str
    message: str
    source_row: int | None = None


@dataclass(frozen=True)
class UntrustedImportedTransaction:
    source_row: int
    date: str
    amount: str
    currency: str
    description: str
    direction: str
    provenance: str
    confidence: float
    suggested_category: str | None = None
    guess_state: str = ""
    guess_confidence: float | None = None
    guess_reason: str = ""
    guess_profile: str = ""
    source_format_changed: bool = False
    validation_warnings: tuple[str, ...] = ()
    review_required: bool = True
    eligible_for_workbook_write: bool = False


@dataclass(frozen=True)
class StatementImportAssistantResult:
    review_artifact_path: Path
    rows: tuple[UntrustedImportedTransaction, ...]
    diagnostics: tuple[ImportAssistantDiagnostic, ...]
    trusted_transactions: tuple[Transaction, ...] = ()


def run_statement_import_assistant(
    *,
    source_path: Path,
    output_dir: Path,
    year: int,
    month: str,
    tracker_currency: str,
    local_model: bool = False,
    client: object | None = None,
    profiles_dir: Path | None = None,
    profile_name: str | None = None,
) -> StatementImportAssistantResult:
    month = normalize_month(month)
    source_text = source_path.read_text(encoding="utf-8")
    diagnostics = list(_layout_diagnostics(source_text))

    rows: tuple[UntrustedImportedTransaction, ...]
    if local_model:
        available, warning = _client_available(client)
        if available:
            try:
                rows = _model_rows(client, source_text)
            except (AttributeError, TypeError, ValueError, json.JSONDecodeError) as exc:
                diagnostics.append(
                    ImportAssistantDiagnostic(
                        severity="warning",
                        code="provider_failure",
                        message=f"Statement Import Assistant model output was ignored: {exc}",
                    )
                )
                rows = _raw_rows(source_text, tracker_currency)
        else:
            diagnostics.append(
                ImportAssistantDiagnostic(
                    severity="warning",
                    code="provider_unavailable",
                    message=warning or "Statement Import Assistant model is unavailable.",
                )
            )
            rows = _raw_rows(source_text, tracker_currency)
    else:
        rows = _raw_rows(source_text, tracker_currency)

    rows, validation_diagnostics = _validate_rows(rows, year, month, tracker_currency)
    diagnostics.extend(validation_diagnostics)
    rows = _apply_importer_profile_guesses(
        rows,
        diagnostics=tuple(diagnostics),
        profiles_dir=profiles_dir,
        profile_name=profile_name,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = output_dir / f"untrusted_import_review_{year}_{month.lower()}.csv"
    _write_review_artifact(artifact_path, rows)
    return StatementImportAssistantResult(
        review_artifact_path=artifact_path,
        rows=rows,
        diagnostics=tuple(diagnostics),
    )


def _client_available(client: object | None) -> tuple[bool, str | None]:
    if client is None:
        return False, "No Statement Import Assistant model client was provided."
    checker = getattr(client, "check_availability", None)
    if checker is None:
        return True, None
    availability = checker()
    if isinstance(availability, bool):
        return availability, None if availability else "Model client reported unavailable."
    available = bool(getattr(availability, "available", False))
    warning = getattr(availability, "warning", None)
    return available, str(warning) if warning else None


def _model_rows(client: object | None, source_text: str) -> tuple[UntrustedImportedTransaction, ...]:
    extractor = getattr(client, "extract_transactions")
    raw_payload = extractor(source_text)
    payload = json.loads(raw_payload) if isinstance(raw_payload, str) else raw_payload
    if not isinstance(payload, dict):
        raise ValueError("model import response must be a JSON object")
    raw_rows = payload.get("transactions")
    if not isinstance(raw_rows, list):
        raise ValueError("model import response must include a transactions list")

    rows: list[UntrustedImportedTransaction] = []
    for index, item in enumerate(raw_rows, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"model transaction {index} must be an object")
        rows.append(
            UntrustedImportedTransaction(
                source_row=_int_value(item.get("source_row"), index),
                date=str(item.get("date", "")).strip(),
                amount=str(item.get("amount", "")).strip(),
                currency=str(item.get("currency", "")).strip().upper(),
                description=str(item.get("description", "")).strip(),
                direction=str(item.get("direction", "")).strip().lower(),
                provenance="model_assisted_untrusted",
                confidence=_confidence(item.get("confidence")),
            )
        )
    return tuple(rows)


def _raw_rows(source_text: str, tracker_currency: str) -> tuple[UntrustedImportedTransaction, ...]:
    rows: list[UntrustedImportedTransaction] = []
    for index, line in enumerate(source_text.splitlines(), start=1):
        description = line.strip()
        if not description:
            continue
        rows.append(
            UntrustedImportedTransaction(
                source_row=index,
                date="",
                amount="",
                currency=tracker_currency.upper(),
                description=description,
                direction="",
                provenance="deterministic_raw_row",
                confidence=0.0,
            )
        )
    return tuple(rows)


def _validate_rows(
    rows: tuple[UntrustedImportedTransaction, ...],
    year: int,
    month: str,
    tracker_currency: str,
) -> tuple[tuple[UntrustedImportedTransaction, ...], tuple[ImportAssistantDiagnostic, ...]]:
    target_start, target_end = _target_period(year, month)
    diagnostics: list[ImportAssistantDiagnostic] = []
    updated: list[UntrustedImportedTransaction] = []

    for row in rows:
        warnings: list[str] = []
        parsed_date = _parse_iso_date(row.date)
        if not row.date:
            warnings.append("missing_date")
            diagnostics.append(_diagnostic("error", "missing_date", "Date is missing.", row))
        elif parsed_date is None:
            warnings.append("invalid_date")
            diagnostics.append(_diagnostic("error", "invalid_date", "Date is invalid.", row))
        elif not (target_start <= parsed_date < target_end):
            warnings.append("out_of_period")
            diagnostics.append(
                _diagnostic(
                    "error",
                    "out_of_period",
                    f"Date {row.date} is outside target period {month} {year}.",
                    row,
                )
            )

        if _parse_amount(row.amount) is None:
            warnings.append("invalid_amount")
            diagnostics.append(_diagnostic("error", "invalid_amount", "Amount is invalid.", row))

        if row.currency.upper() != tracker_currency.upper():
            warnings.append("unsupported_currency")
            diagnostics.append(
                _diagnostic(
                    "error",
                    "unsupported_currency",
                    f"Currency {row.currency!r} does not match tracker currency {tracker_currency!r}.",
                    row,
                )
            )

        if row.direction not in {"income", "expense"}:
            warnings.append("missing_direction")
            diagnostics.append(
                _diagnostic("warning", "missing_direction", "Direction is missing.", row)
            )

        updated.append(replace(row, validation_warnings=tuple(warnings)))

    updated, duplicate_diagnostics = _mark_duplicates(tuple(updated))
    diagnostics.extend(duplicate_diagnostics)
    return updated, tuple(diagnostics)


def _mark_duplicates(
    rows: tuple[UntrustedImportedTransaction, ...],
) -> tuple[tuple[UntrustedImportedTransaction, ...], tuple[ImportAssistantDiagnostic, ...]]:
    fingerprints: dict[tuple[str, str, str, str], list[int]] = {}
    for index, row in enumerate(rows):
        fingerprint = (row.date, row.amount, row.currency, row.description)
        if all(fingerprint):
            fingerprints.setdefault(fingerprint, []).append(index)

    duplicate_indexes = {
        index for indexes in fingerprints.values() if len(indexes) > 1 for index in indexes
    }
    if not duplicate_indexes:
        return rows, ()

    updated = []
    diagnostics = []
    for index, row in enumerate(rows):
        if index not in duplicate_indexes:
            updated.append(row)
            continue
        warnings = tuple(dict.fromkeys((*row.validation_warnings, "duplicate_row")))
        updated_row = replace(row, validation_warnings=warnings)
        updated.append(updated_row)
        diagnostics.append(
            _diagnostic(
                "warning",
                "duplicate_row",
                "Duplicate untrusted imported transaction row.",
                updated_row,
            )
        )
    return tuple(updated), tuple(diagnostics)


def _layout_diagnostics(source_text: str) -> tuple[ImportAssistantDiagnostic, ...]:
    non_empty_lines = [
        (index, line) for index, line in enumerate(source_text.splitlines(), start=1) if line.strip()
    ]
    if len(non_empty_lines) < 2:
        return ()
    delimiter = _likely_delimiter(non_empty_lines[0][1])
    if delimiter is None:
        return ()
    expected_columns = len(non_empty_lines[0][1].split(delimiter))
    diagnostics = []
    for source_row, line in non_empty_lines[1:]:
        if len(line.split(delimiter)) != expected_columns:
            diagnostics.append(
                ImportAssistantDiagnostic(
                    severity="warning",
                    code="changed_layout",
                    message=(
                        f"Source row {source_row} has a different field count than the first row."
                    ),
                    source_row=source_row,
                )
            )
    return tuple(diagnostics)


def _likely_delimiter(line: str) -> str | None:
    candidates = (";", ",", "\t", "|")
    delimiter_counts = [(delimiter, line.count(delimiter)) for delimiter in candidates]
    delimiter, count = max(delimiter_counts, key=lambda item: item[1])
    return delimiter if count else None


def _write_review_artifact(path: Path, rows: tuple[UntrustedImportedTransaction, ...]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "review_required": "yes" if row.review_required else "no",
                    "eligible_for_workbook_write": (
                        "yes" if row.eligible_for_workbook_write else "no"
                    ),
                    "source_row": row.source_row,
                    "date": row.date,
                    "amount": row.amount,
                    "currency": row.currency,
                    "description": row.description,
                    "direction": row.direction,
                    "provenance": row.provenance,
                    "confidence": _format_confidence(row.confidence),
                    "suggested_category": row.suggested_category or "",
                    "guess_state": row.guess_state,
                    "guess_confidence": (
                        "" if row.guess_confidence is None else _format_confidence(row.guess_confidence)
                    ),
                    "guess_reason": row.guess_reason,
                    "guess_profile": row.guess_profile,
                    "source_format_changed": "yes" if row.source_format_changed else "no",
                    "validation_warnings": "|".join(row.validation_warnings),
                    "confirmed": "",
                    "confirmed_category": "",
                }
            )


def _apply_importer_profile_guesses(
    rows: tuple[UntrustedImportedTransaction, ...],
    *,
    diagnostics: tuple[ImportAssistantDiagnostic, ...],
    profiles_dir: Path | None,
    profile_name: str | None,
) -> tuple[UntrustedImportedTransaction, ...]:
    source_format_changed = any(diagnostic.code == "changed_layout" for diagnostic in diagnostics)
    if profiles_dir is None or profile_name is None:
        return tuple(
            replace(row, source_format_changed=source_format_changed)
            for row in rows
        )

    profile_path = importer_profile_path(profiles_dir, profile_name)
    if not profile_path.exists():
        return tuple(
            replace(row, source_format_changed=source_format_changed)
            for row in rows
        )
    payload = json.loads(profile_path.read_text(encoding="utf-8"))
    decisions = {
        str(item.get("description_identity", "")): item
        for item in payload.get("category_decisions", [])
        if isinstance(item, dict)
    }

    updated = []
    for row in rows:
        identity = normalize_merchant_identity(row.description)
        decision = decisions.get(identity)
        if decision is None:
            updated.append(replace(row, source_format_changed=source_format_changed))
            continue

        decision_count = int(decision.get("decision_count", 1))
        confidence = 0.85 if decision_count >= 2 else 0.65
        if source_format_changed or row.validation_warnings:
            confidence = min(confidence, 0.5)
        guess_state = "high_confidence" if confidence >= 0.8 else "low_confidence"
        category = str(decision.get("category", "")).strip()
        reason = (
            f"Matched Importer Profile {profile_name!r} for description identity "
            f"{identity!r}; decision_count={decision_count}."
        )
        if source_format_changed:
            reason += " Source format changed; review carefully."
        if row.validation_warnings:
            reason += " Validation warnings are present; review carefully."

        updated.append(
            replace(
                row,
                suggested_category=category or None,
                guess_state=guess_state,
                guess_confidence=confidence,
                guess_reason=reason,
                guess_profile=profile_name,
                source_format_changed=source_format_changed,
            )
        )
    return tuple(updated)


def _target_period(year: int, month: str) -> tuple[date, date]:
    month_number = MONTH_NUMBERS[month]
    start = date(year, month_number, 1)
    if month_number == 12:
        return start, date(year + 1, 1, 1)
    return start, date(year, month_number + 1, 1)


def _diagnostic(
    severity: str,
    code: str,
    message: str,
    row: UntrustedImportedTransaction,
) -> ImportAssistantDiagnostic:
    return ImportAssistantDiagnostic(
        severity=severity,
        code=code,
        message=f"Source row {row.source_row}: {message}",
        source_row=row.source_row,
    )


def _parse_iso_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_amount(value: str) -> Decimal | None:
    if not value:
        return None
    try:
        if "," in value:
            return parse_danish_decimal(value)
        return Decimal(value)
    except (InvalidOperation, ValueError):
        return None


def _int_value(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _confidence(value: Any) -> float:
    if value is None:
        return 0.0
    confidence = float(value)
    if confidence < 0.0:
        return 0.0
    if confidence > 1.0:
        return 1.0
    return confidence


def _format_confidence(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")
