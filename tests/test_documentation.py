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


def test_proxy_split_transfer_documentation_is_in_sync():
    workflow = (REPO_ROOT / "docs" / "monthly_workflow.md").read_text(encoding="utf-8")
    overview = (REPO_ROOT / "docs" / "project_overview.md").read_text(encoding="utf-8")
    local_example = (REPO_ROOT / "config" / "rules.local.example.yaml").read_text(
        encoding="utf-8"
    )
    domain_language = (REPO_ROOT / ".agent" / "System" / "domain_language.md").read_text(
        encoding="utf-8"
    )
    data_contracts = (REPO_ROOT / ".agent" / "System" / "data_contracts.md").read_text(
        encoding="utf-8"
    )

    workflow_phrases = [
        "Proxy Split Transfer",
        "proxy_split_source",
        "proxy_split_allocation",
        "proxy_split_residual",
        "proxy_split_blocked",
        "Residual Review Line",
        "Review Required column order",
    ]
    for phrase in workflow_phrases:
        assert phrase in workflow

    overview_phrases = [
        "Proxy Split Transfer:",
        "Residual Review Line:",
        "rules.local.yaml",
    ]
    for phrase in overview_phrases:
        assert phrase in overview

    local_example_phrases = [
        "proxy_split_rules",
        "conversion_rate",
        "monthly_limit",
        "allocations",
    ]
    for phrase in local_example_phrases:
        assert phrase in local_example

    for phrase in ["**Proxy Split Transfer**", "**Residual Review Line**"]:
        assert phrase in domain_language

    for phrase in ["## Future Proxy Split Rules", "Review workbook rows for proxy split"]:
        assert phrase in data_contracts


def test_category_registry_leaf_lifecycle_documentation_is_in_sync():
    workflow = (REPO_ROOT / "docs" / "monthly_workflow.md").read_text(encoding="utf-8")
    overview = (REPO_ROOT / "docs" / "project_overview.md").read_text(encoding="utf-8")
    domain_language = (REPO_ROOT / ".agent" / "System" / "domain_language.md").read_text(
        encoding="utf-8"
    )
    data_contracts = (REPO_ROOT / ".agent" / "System" / "data_contracts.md").read_text(
        encoding="utf-8"
    )
    agent_context = (REPO_ROOT / ".agent" / "Tasks" / "context.md").read_text(
        encoding="utf-8"
    )

    workflow_phrases = [
        "Parent/Section Row",
        "Leaf Category Row",
        "`manual_category`",
        "`new_parent_category`",
        "`new_leaf_category`",
        "`learn_to_memory`",
        "Category Registry Updates",
        "--config-dir",
    ]
    for phrase in workflow_phrases:
        assert phrase in workflow

    overview_phrases = [
        "Parent/Section Row:",
        "Leaf Category Row:",
        "Category Registry:",
        "`new_parent_category`",
        "`new_leaf_category`",
    ]
    for phrase in overview_phrases:
        assert phrase in overview

    domain_phrases = [
        "**Parent/Section Row**",
        "**Leaf Category Row**",
        "**Category Registry**",
        "Category Memory can learn only Leaf Category Row targets that exist in the Category Registry",
    ]
    for phrase in domain_phrases:
        assert phrase in domain_language

    contract_phrases = [
        "## Review Workbook",
        "`manual_category`",
        "`new_parent_category`",
        "`new_leaf_category`",
        "`learn_to_memory`",
        "## Category Registry",
        "Category Memory learning validates against leaf categories",
    ]
    for phrase in contract_phrases:
        assert phrase in data_contracts

    context_phrases = [
        "Make YAML the durable category registry for parent/leaf semantics",
        "Category Memory may learn newly added categories only after leaf registry validation succeeds",
    ]
    for phrase in context_phrases:
        assert phrase in agent_context


def test_local_llm_mode_documentation_is_in_sync():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    workflow = (REPO_ROOT / "docs" / "monthly_workflow.md").read_text(encoding="utf-8")
    overview = (REPO_ROOT / "docs" / "project_overview.md").read_text(encoding="utf-8")
    settings = (REPO_ROOT / "config" / "settings.yaml").read_text(encoding="utf-8")
    data_contracts = (REPO_ROOT / ".agent" / "System" / "data_contracts.md").read_text(
        encoding="utf-8"
    )
    security = (REPO_ROOT / ".agent" / "System" / "security_privacy.md").read_text(
        encoding="utf-8"
    )

    shared_phrases = [
        "Local LLM Mode",
        "--local-llm-suggestions",
        "review-only",
        "gemma4:12b",
        "gemma4:e4b",
        "60-second provider timeout",
        "raw Nordea descriptions are excluded",
    ]
    for phrase in shared_phrases:
        assert phrase in workflow

    for phrase in [
        "--local-llm-suggestions",
        "local Ollama/Gemma review suggestions",
    ]:
        assert phrase in readme

    for phrase in [
        "Local LLM Mode:",
        "existing review workbook suggestion fields",
    ]:
        assert phrase in overview

    for phrase in [
        "local_llm:",
        'model: "gemma4:12b"',
        'fallback_model: "gemma4:e4b"',
        "timeout_seconds: 60",
        "include_raw_description: false",
    ]:
        assert phrase in settings

    for phrase in [
        "`status`: one of `category`, `no_suggestion`, `new_leaf_candidate`",
        "Invalid JSON",
        "Provider failures",
    ]:
        assert phrase in data_contracts

    assert "raw Nordea descriptions are excluded" in security
