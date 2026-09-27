from pathlib import Path

from openpyxl import load_workbook

from personal_wealth_tracker.cli import main
from personal_wealth_tracker.pipeline import run_pipeline
from personal_wealth_tracker.setup_workspace import initialize_local_workspace
from personal_wealth_tracker.template_workbook import (
    TEMPLATE_METADATA_SHEET,
    TEMPLATE_WORKBOOK_ID,
    validate_template_workbook,
)


def test_setup_workspace_creates_public_template_config_profile_and_private_dirs(tmp_path):
    workspace = tmp_path / "wealth"

    result = initialize_local_workspace(
        workspace,
        tracker_currency="SEK",
        start_year=2027,
    )

    assert result.workspace_dir == workspace
    assert (workspace / "config" / "settings.yaml").exists()
    assert (workspace / "config" / "categories.yaml").exists()
    assert (workspace / "config" / "rules.yaml").exists()
    assert (workspace / "profiles" / "default.local.yaml").exists()
    assert (workspace / "templates" / "local-wealth-tracker-template.xlsx").exists()
    assert (workspace / "examples" / "synthetic-nordea-transactions.csv").exists()
    for relative_dir in (
        "data/raw_statements",
        "data/watched_folder",
        "data/category_memory",
        "data/importer_profiles",
        "data/processed",
        "data/backups",
        "reports",
        "logs",
    ):
        assert (workspace / relative_dir).is_dir()

    metadata = validate_template_workbook(
        workspace / "templates" / "local-wealth-tracker-template.xlsx"
    )
    assert metadata.template_id == TEMPLATE_WORKBOOK_ID
    assert metadata.tracker_currency == "SEK"

    workbook = load_workbook(workspace / "templates" / "local-wealth-tracker-template.xlsx")
    try:
        assert workbook[TEMPLATE_METADATA_SHEET]["B5"].value == "SEK"
    finally:
        workbook.close()

    settings = (workspace / "config" / "settings.yaml").read_text(encoding="utf-8")
    categories = (workspace / "config" / "categories.yaml").read_text(encoding="utf-8")
    profile = (workspace / "profiles" / "default.local.yaml").read_text(encoding="utf-8")

    assert 'currency: "SEK"' in settings
    assert "Groceries (monthly)" in categories
    assert "Parent B" not in categories
    assert "JEPI" not in categories
    assert 'tracker_workbook: "templates/local-wealth-tracker-template.xlsx"' in profile
    assert 'importer_profiles_dir: "data/importer_profiles"' in profile
    assert 'category_memory_dir: "data/category_memory"' in profile


def test_setup_workspace_is_idempotent_without_force_and_can_overwrite_with_force(tmp_path):
    workspace = tmp_path / "wealth"
    initialize_local_workspace(workspace, tracker_currency="DKK", start_year=2026)

    settings_path = workspace / "config" / "settings.yaml"
    settings_path.write_text("user edited settings\n", encoding="utf-8")

    result = initialize_local_workspace(workspace, tracker_currency="EUR", start_year=2028)

    assert settings_path.read_text(encoding="utf-8") == "user edited settings\n"
    assert settings_path in result.skipped_existing_files

    forced = initialize_local_workspace(
        workspace,
        tracker_currency="EUR",
        start_year=2028,
        force=True,
    )

    assert 'currency: "EUR"' in settings_path.read_text(encoding="utf-8")
    assert settings_path in forced.written_files


def test_setup_workspace_accepts_supported_profile_path_overrides(tmp_path):
    workspace = tmp_path / "wealth"

    initialize_local_workspace(
        workspace,
        tracker_currency="DKK",
        start_year=2026,
        profile_paths={
            "reports_dir": "local_outputs/reports",
            "category_memory_dir": "private_state/category_memory",
            "importer_profiles_dir": "private_state/importer_profiles",
        },
    )

    profile = (workspace / "profiles" / "default.local.yaml").read_text(encoding="utf-8")
    assert 'reports_dir: "local_outputs/reports"' in profile
    assert 'category_memory_dir: "private_state/category_memory"' in profile
    assert 'importer_profiles_dir: "private_state/importer_profiles"' in profile
    assert (workspace / "local_outputs" / "reports").is_dir()
    assert (workspace / "private_state" / "category_memory").is_dir()
    assert (workspace / "private_state" / "importer_profiles").is_dir()


def test_setup_cli_creates_workspace_and_reports_paths(tmp_path, capsys):
    workspace = tmp_path / "wealth"

    exit_code = main(
        [
            "setup",
            "--workspace",
            str(workspace),
            "--tracker-currency",
            "NOK",
            "--start-year",
            "2029",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert f"Workspace: {workspace}" in captured.out
    assert "Template workbook:" in captured.out
    assert (workspace / "templates" / "local-wealth-tracker-template.xlsx").exists()
    assert 'currency: "NOK"' in (
        workspace / "config" / "settings.yaml"
    ).read_text(encoding="utf-8")


def test_setup_cli_accepts_supported_profile_path_overrides(tmp_path):
    workspace = tmp_path / "wealth"

    exit_code = main(
        [
            "setup",
            "--workspace",
            str(workspace),
            "--reports-dir",
            "local_outputs/reports",
            "--category-memory-dir",
            "private_state/category_memory",
            "--importer-profiles-dir",
            "private_state/importer_profiles",
        ]
    )

    assert exit_code == 0
    profile = (workspace / "profiles" / "default.local.yaml").read_text(encoding="utf-8")
    assert 'reports_dir: "local_outputs/reports"' in profile
    assert 'category_memory_dir: "private_state/category_memory"' in profile
    assert 'importer_profiles_dir: "private_state/importer_profiles"' in profile


def test_initialized_workspace_runs_synthetic_csv_dry_run(tmp_path):
    workspace = tmp_path / "wealth"
    initialize_local_workspace(workspace, tracker_currency="DKK", start_year=2026)

    result = run_pipeline(
        tracker_path=workspace / "templates" / "local-wealth-tracker-template.xlsx",
        statement_path=workspace / "examples" / "synthetic-nordea-transactions.csv",
        config_dir=workspace / "config",
        year=2026,
        month="Apr",
        output_dir=workspace / "reports",
        category_memory_dir=workspace / "data" / "category_memory",
        statement_format="auto",
    )

    assert result.mode == "dry-run"
    assert result.statement_parser == "nordea-csv"
    assert len(result.transactions) == 3
    assert result.report_path.exists()
    assert result.review_csv_path.exists()
    assert result.output_workbook_path is None
    assert {update.category for update in result.updates} >= {
        "Full-time job (net)",
        "Groceries (monthly)",
        "Mobile phone (monthly)",
    }


def test_initialized_workspace_report_reflects_configured_currency(tmp_path):
    workspace = tmp_path / "wealth"
    initialize_local_workspace(workspace, tracker_currency="NOK", start_year=2026)

    result = run_pipeline(
        tracker_path=workspace / "templates" / "local-wealth-tracker-template.xlsx",
        statement_path=workspace / "examples" / "synthetic-nordea-transactions.csv",
        config_dir=workspace / "config",
        year=2026,
        month="Apr",
        output_dir=workspace / "reports",
        category_memory_dir=workspace / "data" / "category_memory",
        statement_format="auto",
    )

    report = result.report_path.read_text(encoding="utf-8")
    assert "- Tracker Currency: NOK" in report
    assert "- Statement Currency: NOK" in report


def test_setup_settings_match_current_trust_policy_and_local_llm_defaults(tmp_path):
    from decimal import Decimal

    from personal_wealth_tracker.config import load_config

    initialize_local_workspace(tmp_path / "wealth")

    config = load_config(tmp_path / "wealth" / "config")

    assert config.local_llm.timeout_seconds == 180.0
    assert config.local_llm.keep_alive == "30m"
    assert config.trust_policy.auto_max_amount == Decimal(1000)
    assert config.trust_policy.min_agreement == 2
    assert config.trust_policy.never_auto_categories == frozenset(
        {"Rent (monthly)", "Full-time job (net)"}
    )
    profile = (tmp_path / "wealth" / "profiles" / "default.local.yaml").read_text(
        encoding="utf-8"
    )
    assert 'model_output_policy: "consensus_or_review"' in profile
