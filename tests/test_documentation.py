from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_cli_reference_documents_csv_first_local_validation_workflow():
    reference = (REPO_ROOT / "docs" / "cli_reference.md").read_text(encoding="utf-8")

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
        assert phrase in reference


def test_readme_links_reference_docs_and_demo():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    for phrase in [
        "docs/cli_reference.md",
        "docs/monthly_workflow.md",
        "docs/assets/demo.gif",
        "scripts/record_demo.py",
    ]:
        assert phrase in readme
    assert (REPO_ROOT / "docs" / "assets" / "demo.gif").exists()
    assert (REPO_ROOT / "docs" / "assets" / "demo.mp4").exists()


def test_monthly_workflow_documents_operator_checklist():
    workflow = (REPO_ROOT / "docs" / "monthly_workflow.md").read_text(encoding="utf-8")

    required_phrases = [
        "Monthly Tracker Workflow",
        "project_overview.md",
        "uv run wealth-tracker monthly",
        "--dry-run",
        "review_required_<year>_<mon>.xlsx",
        "one Exception Sheet per month",
        "Blank `manual_category` accepts",
        "`NONE` rejects",
        "Atomic Month Commit",
        "Workbook not written",
        "`corrected_category`",
        "Without a running local model",
        "Categorization Quality",
        "learn-category-memory",
        "--commit",
        "cleanup-currency-labels",
        "Do not commit real bank statements",
        "Investment statements remain separate future PDF evidence",
    ]

    for phrase in required_phrases:
        assert phrase in workflow

    for stale_phrase in ["Run A CSV Dry Run", "Apply Monthly Review Decisions"]:
        assert stale_phrase not in workflow


def test_adrs_are_numbered_and_cross_linked():
    adr_dir = REPO_ROOT / "docs" / "adr"
    adrs = sorted(adr_dir.glob("[0-9][0-9][0-9][0-9]-*.md"))

    assert [int(adr.name[:4]) for adr in adrs] == list(range(1, len(adrs) + 1))
    hosted = adr_dir / "0005-hosted-judgment-deferred.md"
    assert "hosted judgment" in hosted.read_text(encoding="utf-8").lower()
    consensus_flow_adrs = adrs[:5]
    for adr in consensus_flow_adrs:
        text = adr.read_text(encoding="utf-8")
        for other in consensus_flow_adrs:
            if other != adr:
                assert f"]({other.name})" in text, f"{adr.name} does not link {other.name}"


def test_glossary_defines_local_consensus_flow_terms():
    domain_language = (REPO_ROOT / ".agent" / "System" / "domain_language.md").read_text(
        encoding="utf-8"
    )

    for term in [
        "Authority",
        "Trust Policy",
        "Suggester",
        "Consensus",
        "Exception Sheet",
        "Guidance Alias",
        "Atomic Month Commit",
        "Hosted Judgment",
    ]:
        assert domain_language.count(f"\n**{term}**:\n") == 1, term


def test_security_doc_keeps_hosted_judgment_off():
    security = (REPO_ROOT / ".agent" / "System" / "security_privacy.md").read_text(
        encoding="utf-8"
    )

    for phrase in [
        "Hosted Judgment is opt-in only and not enabled",
        "`outbound_redaction`",
        "tested but unused",
        "optional `hosted` extra",
        "docs/adr/0005-hosted-judgment-deferred.md",
    ]:
        assert phrase in security

    assert "must not auto-write workbook values" not in security


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
        "gemma4:26b",
        "gemma4:12b",
        "qwen3:14b",
        "180-second cold-start provider timeout",
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
        'model: "gemma4:26b"',
        'second_model: "gemma4:12b"',
        'fallback_model: "qwen3:14b"',
        "timeout_seconds: 180",
        'keep_alive: "30m"',
        "include_raw_description: false",
    ]:
        assert phrase in settings

    for phrase in [
        "Suggester port",
        "enum of leaves plus `NONE`",
        "Invalid JSON",
        "Provider failures",
    ]:
        assert phrase in data_contracts

    assert "raw Nordea descriptions are excluded" in security


def test_public_private_package_boundary_documentation_is_in_sync():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    boundary = (REPO_ROOT / "docs" / "public_private_boundary.md").read_text(
        encoding="utf-8"
    )
    security = (REPO_ROOT / ".agent" / "System" / "security_privacy.md").read_text(
        encoding="utf-8"
    )
    profile_example = (REPO_ROOT / "config" / "profile.example.yaml").read_text(
        encoding="utf-8"
    )
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")

    boundary_phrases = [
        "Public Package Responsibilities",
        "Private Profile Responsibilities",
        "Local Wealth-Tracker Agent",
        "not an autonomous finance authority",
        "sample public configuration",
        "data/raw_statements/",
        "data/category_memory/",
        "data/importer_profiles/",
        "data/processed/",
        "data/backups/",
        "reports/",
        "logs/",
        "config/*.local.yaml",
        "profiles/*.local.yaml",
        "Category Memory",
        "Importer Profiles",
        "proxy split rules",
    ]
    for phrase in boundary_phrases:
        assert phrase in boundary

    for phrase in [
        "docs/public_private_boundary.md",
        "public/private boundary",
    ]:
        assert phrase in readme

    for phrase in [
        "Public package artifacts",
        "Private profile artifacts",
        "Importer Profiles",
        "not an autonomous finance authority",
    ]:
        assert phrase in security

    for phrase in [
        "profile_paths:",
        "tracker_workbook:",
        "raw_statements_dir:",
        "reports_dir:",
        "processed_workbooks_dir:",
        "backups_dir:",
        "category_memory_dir:",
        "importer_profiles_dir:",
        "local_rules_file:",
        "proxy_split_rules_file:",
    ]:
        assert phrase in profile_example

    ignored_private_paths = [
        "data/raw_statements/",
        "data/category_memory/",
        "data/importer_profiles/",
        "data/processed/",
        "data/backups/",
        "reports/",
        "logs/",
        "config/*.local.yaml",
        "profiles/*.local.yaml",
    ]
    for path in ignored_private_paths:
        assert path in gitignore


def test_template_workbook_documentation_is_in_sync():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    overview = (REPO_ROOT / "docs" / "project_overview.md").read_text(encoding="utf-8")
    template_doc = (REPO_ROOT / "docs" / "template_workbook.md").read_text(
        encoding="utf-8"
    )

    required_phrases = [
        "Template Workbook",
        "local-wealth-tracker-template",
        "template_version",
        "synthetic_template",
        "Net worth",
        "Template Metadata",
        "Tracker Currency",
        "Groceries (monthly)",
        "Local Wealth-Tracker Agent",
        "no real values",
        "no private categories",
        "no personal sheet names",
        "template-workbook customize",
        "Supported V1 Customization",
        "Unsupported formula changes",
        "Formula and layout customization are out of scope for v1",
    ]
    for phrase in required_phrases:
        assert phrase in template_doc

    for phrase in [
        "docs/template_workbook.md",
        "Template Workbook",
        "template-workbook customize",
    ]:
        assert phrase in readme
        assert phrase in overview


def test_public_package_workflow_documentation_is_in_sync():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    overview = (REPO_ROOT / "docs" / "project_overview.md").read_text(encoding="utf-8")
    guide = (REPO_ROOT / "docs" / "public_package_workflow.md").read_text(
        encoding="utf-8"
    )

    required_phrases = [
        "Public Package Workflow",
        "uv sync --extra dev",
        "wealth-tracker setup",
        "templates/local-wealth-tracker-template.xlsx",
        "examples/synthetic-nordea-transactions.csv",
        "wealth-tracker template-workbook customize",
        "wealth-tracker import-statement",
        "wealth-tracker importer-profile learn",
        "wealth-tracker learn-category-memory",
        "--commit",
        "Trusted Statement Adapter",
        "Statement Import Assistant",
        "Importer Profile",
        "public/private boundary",
        "extensible adapters plus model-assisted review flows",
        "not guaranteed trusted parsing of every financial document",
        "desktop app",
        "SaaS",
        "required remote LLMs",
        "autonomous finance decisions",
        "direct original-workbook edits",
        "arbitrary formula/layout editing",
        "live FX",
        "bank APIs",
        "scheduler",
        "cloud sync",
        "public shipping of private data",
    ]
    for phrase in required_phrases:
        assert phrase in guide

    for phrase in [
        "docs/public_package_workflow.md",
        "Public Package Workflow",
    ]:
        assert phrase in readme
        assert phrase in overview
