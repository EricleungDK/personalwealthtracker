import csv
import json
from pathlib import Path

from personal_wealth_tracker.importer_profiles import (
    export_importer_profile,
    learn_importer_profile,
    reset_importer_profile,
)
from personal_wealth_tracker.statement_import_assistant import run_statement_import_assistant


def test_confirmed_import_review_creates_local_profile_without_raw_statement_dump(tmp_path):
    reviewed = tmp_path / "untrusted_import_review_2026_apr.csv"
    profiles_dir = tmp_path / "data" / "importer_profiles"
    _write_reviewed_import(
        reviewed,
        [
            {
                "source_row": "2",
                "date": "2026-04-03",
                "amount": "-42.50",
                "currency": "DKK",
                "description": "SYNTHETIC GROCER SECRET RAW DESCRIPTION",
                "direction": "expense",
                "provenance": "model_assisted_untrusted",
                "confidence": "0.82",
                "validation_warnings": "",
                "confirmed": "yes",
                "confirmed_category": "Groceries (monthly)",
            }
        ],
    )

    result = learn_importer_profile(
        reviewed_import_path=reviewed,
        profiles_dir=profiles_dir,
        profile_name="synthetic-bank",
        tracker_currency="DKK",
    )

    assert result.imported_count == 1
    assert result.skipped_unconfirmed_count == 0
    assert result.profile_path == profiles_dir / "synthetic-bank.importer_profile.json"
    payload = json.loads(result.profile_path.read_text(encoding="utf-8"))
    assert payload["profile_name"] == "synthetic-bank"
    assert payload["source_identity"]["review_artifact"] == reviewed.name
    assert payload["field_mappings"] == {
        "date": "date",
        "amount": "amount",
        "currency": "currency",
        "description": "description",
        "direction": "direction",
    }
    assert payload["validation_assumptions"]["tracker_currency"] == "DKK"
    assert payload["category_decisions"] == [
        {
            "description_identity": "SYNTHETIC GROCER SECRET RAW DESCRIPTION",
            "category": "Groceries (monthly)",
            "source_rows": [2],
            "decision_count": 1,
        }
    ]
    serialized = json.dumps(payload)
    assert "raw row" not in serialized.lower()
    assert "model_assisted_untrusted" not in serialized


def test_raw_model_suggestions_do_not_create_profile_without_confirmation(tmp_path):
    reviewed = tmp_path / "untrusted_import_review_2026_apr.csv"
    profiles_dir = tmp_path / "data" / "importer_profiles"
    _write_reviewed_import(
        reviewed,
        [
            {
                "source_row": "2",
                "date": "2026-04-03",
                "amount": "-42.50",
                "currency": "DKK",
                "description": "SYNTHETIC GROCER",
                "direction": "expense",
                "provenance": "model_assisted_untrusted",
                "confidence": "0.82",
                "validation_warnings": "",
                "confirmed": "",
                "confirmed_category": "Groceries (monthly)",
            }
        ],
    )

    result = learn_importer_profile(
        reviewed_import_path=reviewed,
        profiles_dir=profiles_dir,
        profile_name="synthetic-bank",
        tracker_currency="DKK",
    )

    assert result.imported_count == 0
    assert result.skipped_unconfirmed_count == 1
    assert not result.profile_path.exists()


def test_importer_profile_updates_existing_decisions_and_can_be_reset(tmp_path):
    reviewed = tmp_path / "untrusted_import_review_2026_apr.csv"
    profiles_dir = tmp_path / "data" / "importer_profiles"
    _write_reviewed_import(
        reviewed,
        [
            {
                "source_row": "2",
                "date": "2026-04-03",
                "amount": "-42.50",
                "currency": "DKK",
                "description": "SYNTHETIC GROCER",
                "direction": "expense",
                "provenance": "model_assisted_untrusted",
                "confidence": "0.82",
                "validation_warnings": "",
                "confirmed": "yes",
                "confirmed_category": "Groceries (monthly)",
            }
        ],
    )
    first = learn_importer_profile(
        reviewed_import_path=reviewed,
        profiles_dir=profiles_dir,
        profile_name="synthetic-bank",
        tracker_currency="DKK",
    )

    _write_reviewed_import(
        reviewed,
        [
            {
                "source_row": "8",
                "date": "2026-05-03",
                "amount": "-50.00",
                "currency": "DKK",
                "description": "SYNTHETIC GROCER",
                "direction": "expense",
                "provenance": "model_assisted_untrusted",
                "confidence": "0.9",
                "validation_warnings": "",
                "confirmed": "yes",
                "confirmed_category": "Food& Drinks (monthly)",
            }
        ],
    )
    second = learn_importer_profile(
        reviewed_import_path=reviewed,
        profiles_dir=profiles_dir,
        profile_name="synthetic-bank",
        tracker_currency="DKK",
    )

    payload = json.loads(second.profile_path.read_text(encoding="utf-8"))
    assert payload["confirmed_import_count"] == 2
    assert payload["category_decisions"] == [
        {
            "description_identity": "SYNTHETIC GROCER",
            "category": "Food& Drinks (monthly)",
            "source_rows": [2, 8],
            "decision_count": 2,
        }
    ]

    assert reset_importer_profile(profiles_dir, "synthetic-bank") is True
    assert not first.profile_path.exists()
    assert reset_importer_profile(profiles_dir, "synthetic-bank") is False


def test_importer_profile_export_is_explicit(tmp_path):
    reviewed = tmp_path / "untrusted_import_review_2026_apr.csv"
    profiles_dir = tmp_path / "data" / "importer_profiles"
    export_path = tmp_path / "exports" / "synthetic-bank.importer_profile.json"
    _write_reviewed_import(
        reviewed,
        [
            {
                "source_row": "2",
                "date": "2026-04-03",
                "amount": "-42.50",
                "currency": "DKK",
                "description": "SYNTHETIC GROCER",
                "direction": "expense",
                "provenance": "model_assisted_untrusted",
                "confidence": "0.82",
                "validation_warnings": "",
                "confirmed": "yes",
                "confirmed_category": "Groceries (monthly)",
            }
        ],
    )
    result = learn_importer_profile(
        reviewed_import_path=reviewed,
        profiles_dir=profiles_dir,
        profile_name="synthetic-bank",
        tracker_currency="DKK",
    )

    exported = export_importer_profile(
        profiles_dir=profiles_dir,
        profile_name="synthetic-bank",
        output_path=export_path,
    )

    assert exported == export_path
    assert exported.exists()
    assert exported.read_text(encoding="utf-8") == result.profile_path.read_text(
        encoding="utf-8"
    )


def test_importer_profile_produces_filterable_high_confidence_guess(tmp_path):
    profiles_dir = tmp_path / "data" / "importer_profiles"
    _learn_profile_decision(
        tmp_path,
        profiles_dir,
        source_row="2",
        description="SYNTHETIC GROCER",
        category="Groceries (monthly)",
    )
    _learn_profile_decision(
        tmp_path,
        profiles_dir,
        source_row="8",
        description="SYNTHETIC GROCER",
        category="Groceries (monthly)",
    )
    statement = tmp_path / "unknown.txt"
    statement.write_text("raw statement text\n", encoding="utf-8")

    result = run_statement_import_assistant(
        source_path=statement,
        output_dir=tmp_path / "reports",
        year=2026,
        month="Apr",
        tracker_currency="DKK",
        local_model=True,
        client=_FakeImportClient("SYNTHETIC GROCER"),
        profiles_dir=profiles_dir,
        profile_name="synthetic-bank",
    )

    row = result.rows[0]
    assert row.suggested_category == "Groceries (monthly)"
    assert row.guess_state == "high_confidence"
    assert row.guess_confidence == 0.85
    assert row.guess_profile == "synthetic-bank"
    assert row.source_format_changed is False
    assert row.review_required is True
    assert row.eligible_for_workbook_write is False

    csv_rows = _read_csv(result.review_artifact_path)
    assert csv_rows[0]["guess_state"] == "high_confidence"
    assert csv_rows[0]["suggested_category"] == "Groceries (monthly)"
    assert csv_rows[0]["confirmed"] == ""
    assert csv_rows[0]["confirmed_category"] == ""


def test_importer_profile_low_confidence_guess_remains_prominent_review_work(tmp_path):
    profiles_dir = tmp_path / "data" / "importer_profiles"
    _learn_profile_decision(
        tmp_path,
        profiles_dir,
        source_row="2",
        description="SYNTHETIC GROCER",
        category="Groceries (monthly)",
    )
    statement = tmp_path / "unknown.txt"
    statement.write_text("raw statement text\n", encoding="utf-8")

    result = run_statement_import_assistant(
        source_path=statement,
        output_dir=tmp_path / "reports",
        year=2026,
        month="Apr",
        tracker_currency="DKK",
        local_model=True,
        client=_FakeImportClient("SYNTHETIC GROCER"),
        profiles_dir=profiles_dir,
        profile_name="synthetic-bank",
    )

    assert result.rows[0].suggested_category == "Groceries (monthly)"
    assert result.rows[0].guess_state == "low_confidence"
    assert result.rows[0].guess_confidence == 0.65
    assert result.rows[0].review_required is True


def test_changed_layout_caps_importer_profile_guess_confidence(tmp_path):
    profiles_dir = tmp_path / "data" / "importer_profiles"
    _learn_profile_decision(
        tmp_path,
        profiles_dir,
        source_row="2",
        description="SYNTHETIC GROCER",
        category="Groceries (monthly)",
    )
    _learn_profile_decision(
        tmp_path,
        profiles_dir,
        source_row="8",
        description="SYNTHETIC GROCER",
        category="Groceries (monthly)",
    )
    statement = tmp_path / "unknown.txt"
    statement.write_text("date;amount;currency;description\nchanged layout row\n", encoding="utf-8")

    result = run_statement_import_assistant(
        source_path=statement,
        output_dir=tmp_path / "reports",
        year=2026,
        month="Apr",
        tracker_currency="DKK",
        local_model=True,
        client=_FakeImportClient("SYNTHETIC GROCER"),
        profiles_dir=profiles_dir,
        profile_name="synthetic-bank",
    )

    assert "changed_layout" in {diagnostic.code for diagnostic in result.diagnostics}
    assert result.rows[0].source_format_changed is True
    assert result.rows[0].guess_state == "low_confidence"
    assert result.rows[0].guess_confidence == 0.5


def _write_reviewed_import(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
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
        "validation_warnings",
        "confirmed",
        "confirmed_category",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            payload = {
                "review_required": "yes",
                "eligible_for_workbook_write": "no",
                **row,
            }
            writer.writerow(payload)


def _learn_profile_decision(
    tmp_path: Path,
    profiles_dir: Path,
    *,
    source_row: str,
    description: str,
    category: str,
) -> None:
    reviewed = tmp_path / f"reviewed_{source_row}.csv"
    _write_reviewed_import(
        reviewed,
        [
            {
                "source_row": source_row,
                "date": "2026-04-03",
                "amount": "-42.50",
                "currency": "DKK",
                "description": description,
                "direction": "expense",
                "provenance": "model_assisted_untrusted",
                "confidence": "0.82",
                "validation_warnings": "",
                "confirmed": "yes",
                "confirmed_category": category,
            }
        ],
    )
    learn_importer_profile(
        reviewed_import_path=reviewed,
        profiles_dir=profiles_dir,
        profile_name="synthetic-bank",
        tracker_currency="DKK",
    )


class _FakeImportClient:
    def __init__(self, description: str):
        self.description = description

    def check_availability(self):
        return True

    def extract_transactions(self, _source_text: str) -> str:
        return json.dumps(
            {
                "transactions": [
                    {
                        "source_row": 2,
                        "date": "2026-04-03",
                        "amount": "-42.50",
                        "currency": "DKK",
                        "description": self.description,
                        "direction": "expense",
                        "confidence": 0.82,
                    }
                ]
            }
        )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
