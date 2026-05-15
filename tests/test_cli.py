from pathlib import Path

import pytest

from personal_wealth_tracker.cli import main
from personal_wealth_tracker.models import RunResult


def test_cli_passes_statement_format_to_pipeline(monkeypatch, tmp_path):
    captured = {}

    def fake_run_pipeline(**kwargs):
        captured.update(kwargs)
        return RunResult(
            mode="dry-run",
            target_year=2026,
            target_month="Apr",
            statement_parser="nordea-csv",
            transactions=[],
            categorized_transactions=[],
            updates=[],
            structure_changes=[],
            report_path=tmp_path / "report.md",
            audit_path=tmp_path / "audit.jsonl",
            categorized_csv_path=tmp_path / "categorized.csv",
            review_csv_path=tmp_path / "review.csv",
        )

    monkeypatch.setattr("personal_wealth_tracker.cli.run_pipeline", fake_run_pipeline)

    exit_code = main(
        [
            "--tracker",
            "tracker.xlsx",
            "--statement",
            "statement.csv",
            "--statement-format",
            "nordea-csv",
            "--year",
            "2026",
            "--month",
            "Apr",
        ]
    )

    assert exit_code == 0
    assert captured["statement_format"] == "nordea-csv"


def test_cli_defaults_statement_format_to_auto(monkeypatch, tmp_path):
    captured = {}

    def fake_run_pipeline(**kwargs):
        captured.update(kwargs)
        return RunResult(
            mode="dry-run",
            target_year=2026,
            target_month="Apr",
            statement_parser="nordea-pdf",
            transactions=[],
            categorized_transactions=[],
            updates=[],
            structure_changes=[],
            report_path=tmp_path / "report.md",
            audit_path=tmp_path / "audit.jsonl",
            categorized_csv_path=tmp_path / "categorized.csv",
            review_csv_path=tmp_path / "review.csv",
        )

    monkeypatch.setattr("personal_wealth_tracker.cli.run_pipeline", fake_run_pipeline)

    exit_code = main(
        [
            "--tracker",
            "tracker.xlsx",
            "--statement",
            "statement.pdf",
            "--year",
            "2026",
            "--month",
            "Apr",
        ]
    )

    assert exit_code == 0
    assert captured["statement_format"] == "auto"


def test_cli_rejects_invalid_statement_format():
    with pytest.raises(SystemExit):
        main(
            [
                "--tracker",
                "tracker.xlsx",
                "--statement",
                "statement.csv",
                "--statement-format",
                "generic-csv",
                "--year",
                "2026",
                "--month",
                "Apr",
            ]
        )
