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


def test_cli_reports_rows_in_review_and_exception_sheet(monkeypatch, tmp_path, capsys):
    def fake_run_pipeline(**_kwargs):
        return RunResult(
            mode="commit",
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
            review_xlsx_path=tmp_path / "review_required_2026_apr.xlsx",
            review_count=2,
        )

    monkeypatch.setattr("personal_wealth_tracker.cli.run_pipeline", fake_run_pipeline)

    exit_code = main(
        [
            "--tracker",
            "tracker.xlsx",
            "--statement",
            "statement.csv",
            "--year",
            "2026",
            "--month",
            "Apr",
            "--commit",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Rows in review: 2" in output
    assert f"Exception sheet: {tmp_path / 'review_required_2026_apr.xlsx'}" in output
    assert "Output workbook" not in output


def test_cli_passes_profile_and_flag_paths_to_pipeline(monkeypatch, tmp_path):
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
    monkeypatch.chdir(tmp_path)
    profile = tmp_path / "ws" / "profiles" / "mine.local.yaml"
    profile.parent.mkdir(parents=True)
    profile.write_text(
        'profile_paths:\n  reports_dir: "out/reports"\n  backups_dir: "out/bk"\n',
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--tracker", "tracker.xlsx", "--statement", "statement.csv",
            "--year", "2026", "--month", "Apr",
            "--profile", str(profile), "--processed-dir", "flag/proc",
        ]
    )

    assert exit_code == 0
    assert captured["output_dir"] == tmp_path / "ws" / "out" / "reports"
    assert captured["backups_dir"] == tmp_path / "ws" / "out" / "bk"
    assert captured["processed_dir"] == Path("flag/proc")
    assert captured["category_memory_dir"] == Path("data/category_memory")


def test_cli_rejects_missing_explicit_profile(capsys):
    exit_code = main(
        [
            "--tracker", "tracker.xlsx", "--statement", "statement.csv",
            "--year", "2026", "--month", "Apr", "--profile", "missing.yaml",
        ]
    )

    assert exit_code == 1
    assert "Profile not found: missing.yaml" in capsys.readouterr().err
