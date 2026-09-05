from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from .category_memory import normalize_merchant_identity
from .utils import normalize_text


PROFILE_SUFFIX = ".importer_profile.json"
PROFILE_VERSION = 1
FIELD_MAPPINGS = {
    "date": "date",
    "amount": "amount",
    "currency": "currency",
    "description": "description",
    "direction": "direction",
}


@dataclass(frozen=True)
class ImporterProfileLearnResult:
    imported_count: int
    skipped_unconfirmed_count: int
    profile_path: Path


def learn_importer_profile(
    *,
    reviewed_import_path: Path,
    profiles_dir: Path,
    profile_name: str,
    tracker_currency: str,
) -> ImporterProfileLearnResult:
    profile_path = importer_profile_path(profiles_dir, profile_name)
    existing = _load_profile(profile_path, profile_name)
    rows, fieldnames = _read_reviewed_rows(reviewed_import_path)
    decisions = {
        item["description_identity"]: item
        for item in existing.get("category_decisions", [])
        if isinstance(item, dict) and item.get("description_identity")
    }

    imported_count = 0
    skipped_unconfirmed_count = 0
    warnings_seen: set[str] = set(existing.get("validation_assumptions", {}).get("warnings_seen", []))
    for row in rows:
        warnings_seen.update(_row_warnings(row.get("validation_warnings", "")))
        if not _is_confirmed(row.get("confirmed", "")):
            skipped_unconfirmed_count += 1
            continue
        category = (row.get("confirmed_category") or "").strip()
        description = (row.get("description") or "").strip()
        if not category or not description:
            skipped_unconfirmed_count += 1
            continue

        source_row = _int_value(row.get("source_row"), 0)
        description_identity = normalize_merchant_identity(description)
        existing_decision = decisions.get(description_identity)
        if existing_decision:
            source_rows = sorted(
                {
                    *(_int_value(value, 0) for value in existing_decision.get("source_rows", [])),
                    source_row,
                }
                - {0}
            )
            decisions[description_identity] = {
                "description_identity": description_identity,
                "category": category,
                "source_rows": source_rows,
                "decision_count": int(existing_decision.get("decision_count", 0)) + 1,
            }
        else:
            decisions[description_identity] = {
                "description_identity": description_identity,
                "category": category,
                "source_rows": [source_row] if source_row else [],
                "decision_count": 1,
            }
        imported_count += 1

    if imported_count == 0 and not profile_path.exists():
        return ImporterProfileLearnResult(
            imported_count=0,
            skipped_unconfirmed_count=skipped_unconfirmed_count,
            profile_path=profile_path,
        )

    profile = {
        "profile_version": PROFILE_VERSION,
        "profile_name": profile_name,
        "source_identity": {
            "review_artifact": reviewed_import_path.name,
            "review_artifact_schema": "untrusted_import_review_v1",
            "header_fingerprint": _header_fingerprint(fieldnames),
        },
        "field_mappings": FIELD_MAPPINGS,
        "validation_assumptions": {
            "tracker_currency": tracker_currency.upper(),
            "required_fields": list(FIELD_MAPPINGS),
            "warnings_seen": sorted(warnings_seen),
        },
        "confirmed_import_count": int(existing.get("confirmed_import_count", 0)) + imported_count,
        "category_decisions": sorted(
            decisions.values(),
            key=lambda item: str(item["description_identity"]),
        ),
    }
    profiles_dir.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return ImporterProfileLearnResult(
        imported_count=imported_count,
        skipped_unconfirmed_count=skipped_unconfirmed_count,
        profile_path=profile_path,
    )


def reset_importer_profile(profiles_dir: Path, profile_name: str) -> bool:
    profile_path = importer_profile_path(profiles_dir, profile_name)
    if not profile_path.exists():
        return False
    profile_path.unlink()
    return True


def export_importer_profile(
    *,
    profiles_dir: Path,
    profile_name: str,
    output_path: Path,
) -> Path:
    profile_path = importer_profile_path(profiles_dir, profile_name)
    if not profile_path.exists():
        raise ValueError(f"Importer Profile {profile_name!r} does not exist.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(profile_path, output_path)
    return output_path


def importer_profile_path(profiles_dir: Path, profile_name: str) -> Path:
    return profiles_dir / f"{_safe_profile_name(profile_name)}{PROFILE_SUFFIX}"


def _read_reviewed_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        return list(reader), fieldnames


def _load_profile(path: Path, profile_name: str) -> dict:
    if not path.exists():
        return {
            "profile_name": profile_name,
            "confirmed_import_count": 0,
            "category_decisions": [],
            "validation_assumptions": {"warnings_seen": []},
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Importer Profile {path} must contain a JSON object.")
    return payload


def _is_confirmed(value: str) -> bool:
    return normalize_text(value) in {"1", "TRUE", "YES", "Y"}


def _safe_profile_name(value: str) -> str:
    safe = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    if not safe:
        raise ValueError("Importer Profile name must contain at least one letter or number.")
    return safe


def _header_fingerprint(fieldnames: list[str]) -> str:
    payload = "\n".join(fieldnames)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _row_warnings(value: str) -> tuple[str, ...]:
    return tuple(item for item in value.split("|") if item)


def _int_value(value, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback
