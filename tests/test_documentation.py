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
    ]

    for phrase in required_phrases:
        assert phrase in readme


def test_committed_csv_fixtures_are_redacted_and_do_not_require_real_csv_paths():
    fixture_paths = sorted((REPO_ROOT / "tests" / "fixtures").glob("*.csv"))

    assert fixture_paths
    for fixture_path in fixture_paths:
        assert "redacted" in fixture_path.name or "synthetic" in fixture_path.name

    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "*.csv" in gitignore
    assert "!tests/fixtures/**/*.csv" in gitignore
