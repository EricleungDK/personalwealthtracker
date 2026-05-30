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


def test_cli_passes_review_decisions_to_pipeline(monkeypatch, tmp_path):
    captured = {}
    review_decisions = tmp_path / "review_required_2026_apr.xlsx"

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
            "--review-decisions",
            str(review_decisions),
        ]
    )

    assert exit_code == 0
    assert captured["review_decisions_path"] == review_decisions


def test_cli_passes_local_llm_opt_in_to_pipeline(monkeypatch, tmp_path):
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
            "--local-llm-suggestions",
        ]
    )

    assert exit_code == 0
    assert captured["local_llm_suggestions"] is True


def test_cli_disables_local_llm_mode_by_default(monkeypatch, tmp_path):
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
    assert captured["local_llm_suggestions"] is False


def test_cli_reports_pipeline_validation_errors_without_traceback(monkeypatch, capsys):
    def fake_run_pipeline(**_kwargs):
        raise ValueError(
            "Unsupported review decision transaction ID scheme 'stable-content-v1'; "
            "expected 'stable-content-v2'. Regenerate the review workbook from a fresh dry run."
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
            "--review-decisions",
            "reports/review_required_2026_apr.xlsx",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Unsupported review decision transaction ID scheme" in captured.err
    assert "Regenerate the review workbook" in captured.err
    assert "Traceback" not in captured.err
    assert captured.out == ""


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
