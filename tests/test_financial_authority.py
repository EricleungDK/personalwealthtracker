import pytest

from personal_wealth_tracker.pipeline import run_pipeline
from personal_wealth_tracker.setup_workspace import initialize_local_workspace
from personal_wealth_tracker.statement_import_assistant import run_statement_import_assistant


def test_unreviewed_unknown_import_artifact_is_not_trusted_monthly_evidence(tmp_path):
    workspace = tmp_path / "wealth"
    initialize_local_workspace(workspace, tracker_currency="DKK", start_year=2026)
    unknown_statement = workspace / "data" / "raw_statements" / "unknown.txt"
    unknown_statement.write_text("SYNTHETIC UNKNOWN ROW\n", encoding="utf-8")

    import_result = run_statement_import_assistant(
        source_path=unknown_statement,
        output_dir=workspace / "reports",
        year=2026,
        month="Apr",
        tracker_currency="DKK",
    )

    assert import_result.rows[0].review_required is True
    assert import_result.rows[0].eligible_for_workbook_write is False

    with pytest.raises(ValueError, match="missing required headers"):
        run_pipeline(
            tracker_path=workspace / "templates" / "local-wealth-tracker-template.xlsx",
            statement_path=import_result.review_artifact_path,
            config_dir=workspace / "config",
            year=2026,
            month="Apr",
            output_dir=workspace / "reports",
            category_memory_dir=workspace / "data" / "category_memory",
            statement_format="auto",
        )
