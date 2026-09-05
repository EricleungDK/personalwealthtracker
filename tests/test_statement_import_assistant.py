import csv
import json
from pathlib import Path

from personal_wealth_tracker.statement_import_assistant import (
    run_statement_import_assistant,
)


def test_unknown_import_without_model_writes_untrusted_review_artifact(tmp_path):
    statement = tmp_path / "unknown-statement.txt"
    statement.write_text("mystery row one\nmystery row two\n", encoding="utf-8")

    result = run_statement_import_assistant(
        source_path=statement,
        output_dir=tmp_path / "reports",
        year=2026,
        month="Apr",
        tracker_currency="DKK",
    )

    assert result.trusted_transactions == ()
    assert result.review_artifact_path.exists()
    assert len(result.rows) == 2
    assert all(row.review_required for row in result.rows)
    assert all(not row.eligible_for_workbook_write for row in result.rows)
    assert {warning for row in result.rows for warning in row.validation_warnings} >= {
        "missing_date",
        "invalid_amount",
    }

    rows = _read_csv(result.review_artifact_path)
    assert rows[0]["source_row"] == "1"
    assert rows[0]["provenance"] == "deterministic_raw_row"
    assert rows[0]["review_required"] == "yes"
    assert rows[0]["eligible_for_workbook_write"] == "no"


def test_mocked_model_output_rows_remain_untrusted_and_validation_warnings_are_visible(
    tmp_path,
):
    statement = tmp_path / "unknown-statement.txt"
    statement.write_text("Date | Amount | Currency | Description\n...", encoding="utf-8")
    client = _FakeImportClient(
        {
            "transactions": [
                {
                    "source_row": 2,
                    "date": "2026-04-03",
                    "amount": "-42.50",
                    "currency": "DKK",
                    "description": "Synthetic groceries",
                    "direction": "expense",
                    "confidence": 0.82,
                },
                {
                    "source_row": 3,
                    "date": "",
                    "amount": "not-a-number",
                    "currency": "EUR",
                    "description": "Broken row",
                    "direction": "expense",
                    "confidence": 0.24,
                },
                {
                    "source_row": 4,
                    "date": "2026-05-01",
                    "amount": "-10.00",
                    "currency": "DKK",
                    "description": "Wrong month",
                    "direction": "expense",
                    "confidence": 0.7,
                },
            ]
        }
    )

    result = run_statement_import_assistant(
        source_path=statement,
        output_dir=tmp_path / "reports",
        year=2026,
        month="Apr",
        tracker_currency="DKK",
        local_model=True,
        client=client,
    )

    assert result.trusted_transactions == ()
    assert [row.provenance for row in result.rows] == [
        "model_assisted_untrusted",
        "model_assisted_untrusted",
        "model_assisted_untrusted",
    ]
    assert all(row.review_required for row in result.rows)
    assert all(not row.eligible_for_workbook_write for row in result.rows)
    assert result.rows[0].validation_warnings == ()
    assert set(result.rows[1].validation_warnings) >= {
        "missing_date",
        "invalid_amount",
        "unsupported_currency",
    }
    assert "out_of_period" in result.rows[2].validation_warnings
    assert {
        diagnostic.code for diagnostic in result.diagnostics
    } >= {
        "missing_date",
        "invalid_amount",
        "unsupported_currency",
        "out_of_period",
    }

    rows = _read_csv(result.review_artifact_path)
    assert rows[0]["date"] == "2026-04-03"
    assert rows[0]["amount"] == "-42.50"
    assert rows[0]["currency"] == "DKK"
    assert rows[0]["description"] == "Synthetic groceries"
    assert rows[0]["confidence"] == "0.82"


def test_duplicate_rows_and_changed_layout_are_visible_in_diagnostics(tmp_path):
    statement = tmp_path / "unknown-statement.txt"
    statement.write_text(
        "date;amount;currency;description\n"
        "2026-04-03;-42.50;DKK;Duplicate\n"
        "2026-04-03;-42.50;DKK;Duplicate\n"
        "changed layout row\n",
        encoding="utf-8",
    )
    client = _FakeImportClient(
        {
            "transactions": [
                {
                    "source_row": 2,
                    "date": "2026-04-03",
                    "amount": "-42.50",
                    "currency": "DKK",
                    "description": "Duplicate",
                    "direction": "expense",
                    "confidence": 0.9,
                },
                {
                    "source_row": 3,
                    "date": "2026-04-03",
                    "amount": "-42.50",
                    "currency": "DKK",
                    "description": "Duplicate",
                    "direction": "expense",
                    "confidence": 0.9,
                },
            ]
        }
    )

    result = run_statement_import_assistant(
        source_path=statement,
        output_dir=tmp_path / "reports",
        year=2026,
        month="Apr",
        tracker_currency="DKK",
        local_model=True,
        client=client,
    )

    codes = [diagnostic.code for diagnostic in result.diagnostics]
    assert "changed_layout" in codes
    assert "duplicate_row" in codes


def test_unavailable_model_falls_back_to_deterministic_review_artifact(tmp_path):
    statement = tmp_path / "unknown-statement.txt"
    statement.write_text("raw row\n", encoding="utf-8")

    result = run_statement_import_assistant(
        source_path=statement,
        output_dir=tmp_path / "reports",
        year=2026,
        month="Apr",
        tracker_currency="DKK",
        local_model=True,
        client=_UnavailableImportClient(),
    )

    assert result.review_artifact_path.exists()
    assert result.trusted_transactions == ()
    assert result.rows[0].provenance == "deterministic_raw_row"
    assert result.diagnostics[0].code == "provider_unavailable"


class _FakeImportClient:
    def __init__(self, payload):
        self.payload = payload

    def check_availability(self):
        return True

    def extract_transactions(self, _source_text: str) -> str:
        return json.dumps(self.payload)


class _UnavailableImportClient:
    def check_availability(self):
        return False


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
