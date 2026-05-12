import csv
import json
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook

from personal_wealth_tracker.categorizer import categorize_transactions
from personal_wealth_tracker.category_memory import import_reviewed_decisions, load_category_memory
from personal_wealth_tracker.cli import main
from personal_wealth_tracker.config import AppConfig
from personal_wealth_tracker.models import Transaction
from personal_wealth_tracker.pipeline import run_pipeline


FIXTURE = Path(__file__).parent / "fixtures" / "nordea_account_statement.redacted.pdf"


def test_import_confirmed_review_decision_into_category_memory(tmp_path):
    decisions_path = tmp_path / "reviewed_decisions.csv"
    memory_dir = tmp_path / "data" / "category_memory"
    _write_decisions(
        decisions_path,
        [
            {
                "transaction_id": "tx-netto-1",
                "date": "2026-04-12",
                "description": "NETTO 1234 KOBENHAVN",
                "amount": "-125.50",
                "direction": "expense",
                "confirmed_category": "Food& Drinks (monthly)",
                "confirmed": "yes",
            }
        ],
    )

    exit_code = main(
        [
            "learn-category-memory",
            "--decisions",
            str(decisions_path),
            "--memory-dir",
            str(memory_dir),
        ]
    )

    assert exit_code == 0
    memory_path = memory_dir / "category_memory.json"
    assert memory_path.exists()
    payload = json.loads(memory_path.read_text(encoding="utf-8"))
    assert payload["mappings"] == [
        {
            "merchant_identity": "NETTO KOBENHAVN",
            "category": "Food& Drinks (monthly)",
            "source_transaction_ids": ["tx-netto-1"],
        }
    ]


def test_console_entrypoint_imports_category_memory_when_argv_is_none(
    tmp_path, monkeypatch
):
    decisions_path = tmp_path / "reviewed_decisions.csv"
    memory_dir = tmp_path / "data" / "category_memory"
    _write_decisions(
        decisions_path,
        [
            {
                "transaction_id": "tx-netto-1",
                "date": "2026-04-12",
                "description": "NETTO 1234 KOBENHAVN",
                "amount": "-125.50",
                "direction": "expense",
                "confirmed_category": "Food& Drinks (monthly)",
                "confirmed": "yes",
            }
        ],
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "wealth-tracker",
            "learn-category-memory",
            "--decisions",
            str(decisions_path),
            "--memory-dir",
            str(memory_dir),
        ],
    )

    assert main() == 0
    assert (memory_dir / "category_memory.json").exists()


def test_category_memory_matches_future_transaction_by_normalized_merchant_identity(tmp_path):
    decisions_path = tmp_path / "reviewed_decisions.csv"
    memory_dir = tmp_path / "data" / "category_memory"
    _write_decisions(
        decisions_path,
        [
            {
                "transaction_id": "tx-netto-1",
                "date": "2026-04-12",
                "description": "NETTO 1234 KOBENHAVN",
                "amount": "-125.50",
                "direction": "expense",
                "confirmed_category": "Food& Drinks (monthly)",
                "confirmed": "yes",
            }
        ],
    )
    import_reviewed_decisions(decisions_path, memory_dir)

    result = categorize_transactions(
        [_transaction("NETTO 5678 KOBENHAVN", "-89.95")],
        _config(),
        category_memory=load_category_memory(memory_dir),
    )[0]

    assert result.suggested_category == "Food& Drinks (monthly)"
    assert result.categorization_method == "category_memory"
    assert result.review_required is False


def test_recurring_category_memory_hints_constrain_future_matches(tmp_path):
    decisions_path = tmp_path / "reviewed_decisions.csv"
    memory_dir = tmp_path / "data" / "category_memory"
    _write_decisions(
        decisions_path,
        [
            {
                "transaction_id": "tx-mobile-1",
                "date": "2026-04-28",
                "description": "PRIVATE TELECOM 4321",
                "amount": "-99.00",
                "direction": "expense",
                "confirmed_category": "Mobile phone (monthly)",
                "confirmed": "yes",
                "recurring": "yes",
                "amount_tolerance": "2.00",
                "day_min": "25",
                "day_max": "31",
            }
        ],
    )
    import_reviewed_decisions(decisions_path, memory_dir)
    memory = load_category_memory(memory_dir)

    matching = categorize_transactions(
        [_transaction("PRIVATE TELECOM 5555", "-100.50", date(2026, 5, 29))],
        _config(categories=("Mobile phone (monthly)",)),
        category_memory=memory,
    )[0]
    outside_hint = categorize_transactions(
        [_transaction("PRIVATE TELECOM 5555", "-100.50", date(2026, 5, 10))],
        _config(categories=("Mobile phone (monthly)",)),
        category_memory=memory,
    )[0]

    assert matching.suggested_category == "Mobile phone (monthly)"
    assert matching.categorization_method == "category_memory"
    assert outside_hint.suggested_category is None
    assert outside_hint.review_required is True


def test_import_rejects_incomplete_confirmed_rows_with_useful_message(tmp_path, capsys):
    decisions_path = tmp_path / "reviewed_decisions.csv"
    memory_dir = tmp_path / "data" / "category_memory"
    _write_decisions(
        decisions_path,
        [
            {
                "transaction_id": "tx-netto-1",
                "date": "2026-04-12",
                "description": "NETTO 1234 KOBENHAVN",
                "amount": "-125.50",
                "direction": "expense",
                "confirmed_category": "",
                "confirmed": "yes",
            }
        ],
    )

    exit_code = main(
        [
            "learn-category-memory",
            "--decisions",
            str(decisions_path),
            "--memory-dir",
            str(memory_dir),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "row 2" in captured.err
    assert "confirmed_category" in captured.err
    assert not (memory_dir / "category_memory.json").exists()


def test_import_rejects_invalid_recurring_hint_with_useful_message(tmp_path, capsys):
    decisions_path = tmp_path / "reviewed_decisions.csv"
    memory_dir = tmp_path / "data" / "category_memory"
    _write_decisions(
        decisions_path,
        [
            {
                "transaction_id": "tx-mobile-1",
                "date": "2026-04-28",
                "description": "PRIVATE TELECOM 4321",
                "amount": "-99.00",
                "direction": "expense",
                "confirmed_category": "Mobile phone (monthly)",
                "confirmed": "yes",
                "recurring": "yes",
                "amount_tolerance": "2.00",
                "day_min": "31",
                "day_max": "25",
            }
        ],
    )

    exit_code = main(
        [
            "learn-category-memory",
            "--decisions",
            str(decisions_path),
            "--memory-dir",
            str(memory_dir),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "row 2" in captured.err
    assert "day_min" in captured.err
    assert "day_max" in captured.err
    assert not (memory_dir / "category_memory.json").exists()


def test_import_does_not_learn_from_unconfirmed_rows(tmp_path, capsys):
    decisions_path = tmp_path / "reviewed_decisions.csv"
    memory_dir = tmp_path / "data" / "category_memory"
    _write_decisions(
        decisions_path,
        [
            {
                "transaction_id": "tx-auto-guess",
                "date": "2026-04-12",
                "description": "GUESSY MERCHANT 9999",
                "amount": "-125.50",
                "direction": "expense",
                "confirmed_category": "Shopping (monthly)",
                "confirmed": "no",
            }
        ],
    )

    exit_code = main(
        [
            "learn-category-memory",
            "--decisions",
            str(decisions_path),
            "--memory-dir",
            str(memory_dir),
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads((memory_dir / "category_memory.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert "Skipped unconfirmed decisions: 1" in captured.out
    assert payload["mappings"] == []


def test_import_preserves_existing_category_memory_mappings(tmp_path):
    memory_dir = tmp_path / "data" / "category_memory"
    first_decisions = tmp_path / "first_reviewed_decisions.csv"
    second_decisions = tmp_path / "second_reviewed_decisions.csv"
    _write_decisions(
        first_decisions,
        [
            {
                "transaction_id": "tx-netto-1",
                "date": "2026-04-12",
                "description": "NETTO 1234 KOBENHAVN",
                "amount": "-125.50",
                "direction": "expense",
                "confirmed_category": "Food& Drinks (monthly)",
                "confirmed": "yes",
            }
        ],
    )
    _write_decisions(
        second_decisions,
        [
            {
                "transaction_id": "tx-travel-1",
                "date": "2026-04-28",
                "description": "REDACTED FOREIGN CARD",
                "amount": "-86.10",
                "direction": "expense",
                "confirmed_category": "Traveling",
                "confirmed": "yes",
            }
        ],
    )

    import_reviewed_decisions(first_decisions, memory_dir)
    import_reviewed_decisions(second_decisions, memory_dir)

    memory = load_category_memory(memory_dir)
    assert [mapping.category for mapping in memory.mappings] == [
        "Food& Drinks (monthly)",
        "Traveling",
    ]


def test_pipeline_uses_existing_category_memory_for_future_dry_run_matches(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    memory_dir = tmp_path / "data" / "category_memory"
    _create_tracker(tracker)
    _create_pipeline_config(config_dir)
    _write_decisions(
        tmp_path / "reviewed_decisions.csv",
        [
            {
                "transaction_id": "tx-travel-reviewed",
                "date": "2026-03-28",
                "description": "REDACTED FOREIGN CARD 6,9700 NOK 123,45",
                "amount": "-86.10",
                "direction": "expense",
                "confirmed_category": "Traveling",
                "confirmed": "yes",
            }
        ],
    )
    import_reviewed_decisions(tmp_path / "reviewed_decisions.csv", memory_dir)

    result = run_pipeline(
        tracker_path=tracker,
        statement_path=FIXTURE,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "reports",
        category_memory_dir=memory_dir,
    )

    travel = [
        item for item in result.categorized_transactions if item.suggested_category == "Traveling"
    ]
    assert len(travel) == 1
    assert travel[0].categorization_method == "category_memory"
    assert travel[0].review_required is False


def _write_decisions(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def _config(categories=("Food& Drinks (monthly)",)) -> AppConfig:
    return AppConfig(
        sheet_name="Net worth",
        tracker_currency="DKK",
        category_column=2,
        year_header_row=2,
        month_header_row=3,
        statement_currency="DKK",
        auto_write_threshold=0.85,
        review_threshold=0.60,
        reject_threshold=0.60,
        overwrite_fixed_rows=False,
        highlight_auto_filled_cells=False,
        categories=categories,
        aliases={},
        historical_mappings={},
        rules=(),
        fixed_rows=frozenset(),
    )


def _transaction(
    description: str, amount: str, transaction_date: date = date(2026, 5, 2)
) -> Transaction:
    amount_value = Decimal(amount)
    return Transaction(
        transaction_id="future-tx",
        date=transaction_date,
        interest_date=None,
        description=description,
        amount=amount_value,
        currency="DKK",
        direction="income" if amount_value >= 0 else "expense",
    )


def _create_tracker(path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Net worth"
    sheet["C2"] = 2026
    sheet["C3"] = "Apr"
    sheet["B5"] = "Apple Cloud"
    sheet["B6"] = "Full-time job (net)"
    sheet["B7"] = "Traveling"
    workbook.save(path)
    workbook.close()


def _create_pipeline_config(config_dir: Path) -> None:
    config_dir.mkdir(parents=True)
    _write_text(
        config_dir / "settings.yaml",
        """
tracker:
  sheet_name: "Net worth"
  currency: "DKK"
  category_column: 2
  year_header_row: 2
  month_header_row: 3
statement:
  currency: "DKK"
confidence_thresholds:
  auto_write: 0.85
  review_required: 0.60
  reject_below: 0.60
writer:
  overwrite_fixed_rows: false
  highlight_auto_filled_cells: false
""",
    )
    _write_text(
        config_dir / "categories.yaml",
        """
categories:
  - "Apple Cloud"
  - "Full-time job (net)"
  - "Traveling"
aliases: {}
""",
    )
    _write_text(
        config_dir / "rules.yaml",
        """
historical_mappings:
  "APPLE.COM/BILL": "Apple Cloud"
rules:
  - category: "Full-time job (net)"
    match_keywords: ["salary"]
    direction: "income"
    confidence: 0.95
fixed_rows: []
""",
    )


def _write_text(path: Path, content: str) -> None:
    path.write_text(content.lstrip(), encoding="utf-8")
