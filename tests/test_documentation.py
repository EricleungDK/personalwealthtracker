from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_readme_documents_csv_first_local_validation_workflow():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    required_phrases = [
        "Nordea CSV is the preferred bank cashflow input",
        "PDF remains supported as a fallback/legacy input",
        "--statement-format auto",
        "--statement-format nordea-csv",
        "Real CSV exports are ignored by Git and must not be committed",
        "local smoke validation",
        "Investment statements remain separate future PDF evidence",
        "docs/monthly_workflow.md",
    ]

    for phrase in required_phrases:
        assert phrase in readme


def test_monthly_workflow_documents_operator_checklist():
    workflow = (REPO_ROOT / "docs" / "monthly_workflow.md").read_text(encoding="utf-8")

    required_phrases = [
        "Monthly Tracker Workflow",
        "project_overview.md",
        "Run A CSV Dry Run",
        "--statement-format auto",
        "review_required_<year>_<month>.csv",
        "review_required_<year>_<month>.xlsx",
        "Categorization Quality",
        "learn-category-memory",
        "review_required_2026_apr.xlsx",
        "learn_to_memory",
        "--commit",
        "cleanup-currency-labels",
        "Do not commit real bank statements",
        "Investment statements remain separate future PDF evidence",
    ]

    for phrase in required_phrases:
        assert phrase in workflow


def test_committed_csv_fixtures_are_redacted_and_do_not_require_real_csv_paths():
    fixture_paths = sorted((REPO_ROOT / "tests" / "fixtures").glob("*.csv"))

    assert fixture_paths
    for fixture_path in fixture_paths:
        assert "redacted" in fixture_path.name or "synthetic" in fixture_path.name

    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "*.csv" in gitignore
    assert "!tests/fixtures/**/*.csv" in gitignore


def test_project_overview_documents_maps_components_scripts_and_terms():
    overview = (REPO_ROOT / "docs" / "project_overview.md").read_text(encoding="utf-8")

    required_phrases = [
        "Project Overview",
        "```mermaid",
        "Project Map",
        "Monthly Run Flow",
        "Main Components",
        "Outputs And Decision Files",
        "Scripts And Tests",
        "Documentation Map",
        "Glossary",
        "src/personal_wealth_tracker",
        "scripts/generate_redacted_nordea_fixture.py",
        "review_required_<period>.xlsx",
        "Category Memory",
        "Monthly Review Decisions",
        "CLI: Command-line interface",
        "Mermaid: A text format for diagrams inside Markdown",
        "monthly_workflow.md",
    ]

    for phrase in required_phrases:
        assert phrase in overview

    assert overview.count("```mermaid") >= 4
