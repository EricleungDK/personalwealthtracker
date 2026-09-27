from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .template_workbook import create_template_workbook


@dataclass(frozen=True)
class SetupWorkspaceResult:
    workspace_dir: Path
    template_path: Path
    example_statement_path: Path
    created_dirs: tuple[Path, ...]
    written_files: tuple[Path, ...]
    skipped_existing_files: tuple[Path, ...]


def initialize_local_workspace(
    workspace_dir: Path,
    *,
    tracker_currency: str = "DKK",
    start_year: int = 2026,
    profile_paths: dict[str, str] | None = None,
    force: bool = False,
) -> SetupWorkspaceResult:
    workspace_dir = workspace_dir.expanduser()
    tracker_currency = tracker_currency.upper()
    resolved_profile_paths = _profile_paths(profile_paths)

    created_dirs: list[Path] = []
    written_files: list[Path] = []
    skipped_existing_files: list[Path] = []

    for relative_dir in _workspace_dirs():
        directory = workspace_dir / relative_dir
        directory.mkdir(parents=True, exist_ok=True)
        created_dirs.append(directory)
    for key, value in resolved_profile_paths.items():
        if not key.endswith("_dir"):
            continue
        directory = workspace_dir / value
        directory.mkdir(parents=True, exist_ok=True)
        if directory not in created_dirs:
            created_dirs.append(directory)

    template_path = workspace_dir / "templates" / "local-wealth-tracker-template.xlsx"
    if template_path.exists() and not force:
        skipped_existing_files.append(template_path)
    else:
        create_template_workbook(
            template_path,
            tracker_currency=tracker_currency,
            start_year=start_year,
        )
        written_files.append(template_path)

    example_statement_path = workspace_dir / "examples" / "synthetic-nordea-transactions.csv"
    _write_file(
        example_statement_path,
        _synthetic_nordea_csv(tracker_currency),
        force=force,
        written_files=written_files,
        skipped_existing_files=skipped_existing_files,
    )
    _write_file(
        workspace_dir / "config" / "settings.yaml",
        _settings_yaml(tracker_currency),
        force=force,
        written_files=written_files,
        skipped_existing_files=skipped_existing_files,
    )
    _write_file(
        workspace_dir / "config" / "categories.yaml",
        _categories_yaml(),
        force=force,
        written_files=written_files,
        skipped_existing_files=skipped_existing_files,
    )
    _write_file(
        workspace_dir / "config" / "rules.yaml",
        _rules_yaml(),
        force=force,
        written_files=written_files,
        skipped_existing_files=skipped_existing_files,
    )
    _write_file(
        workspace_dir / "profiles" / "default.local.yaml",
        _profile_yaml(tracker_currency, resolved_profile_paths),
        force=force,
        written_files=written_files,
        skipped_existing_files=skipped_existing_files,
    )

    return SetupWorkspaceResult(
        workspace_dir=workspace_dir,
        template_path=template_path,
        example_statement_path=example_statement_path,
        created_dirs=tuple(created_dirs),
        written_files=tuple(written_files),
        skipped_existing_files=tuple(skipped_existing_files),
    )


def _workspace_dirs() -> tuple[Path, ...]:
    return (
        Path("config"),
        Path("profiles"),
        Path("templates"),
        Path("examples"),
        Path("data/raw_statements"),
        Path("data/watched_folder"),
        Path("data/category_memory"),
        Path("data/importer_profiles"),
        Path("data/processed"),
        Path("data/backups"),
        Path("reports"),
        Path("logs"),
    )


def _write_file(
    path: Path,
    content: str,
    *,
    force: bool,
    written_files: list[Path],
    skipped_existing_files: list[Path],
) -> None:
    if path.exists() and not force:
        skipped_existing_files.append(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    written_files.append(path)


def _profile_paths(overrides: dict[str, str] | None) -> dict[str, str]:
    paths = {
        "tracker_workbook": "templates/local-wealth-tracker-template.xlsx",
        "raw_statements_dir": "data/raw_statements",
        "watched_folder_dir": "data/watched_folder",
        "reports_dir": "reports",
        "processed_workbooks_dir": "data/processed",
        "backups_dir": "data/backups",
        "logs_dir": "logs",
        "category_memory_dir": "data/category_memory",
        "importer_profiles_dir": "data/importer_profiles",
        "local_rules_file": "config/rules.local.yaml",
        "proxy_split_rules_file": "config/rules.local.yaml",
    }
    if not overrides:
        return paths

    unknown_keys = sorted(set(overrides) - set(paths))
    if unknown_keys:
        raise ValueError(f"Unsupported profile path override(s): {', '.join(unknown_keys)}.")
    for key, value in overrides.items():
        value_path = Path(value)
        if value_path.is_absolute():
            raise ValueError(f"Profile path override {key!r} must be relative to the workspace.")
        paths[key] = value
    return paths


def _settings_yaml(tracker_currency: str) -> str:
    return f"""tracker:
  sheet_name: "Net worth"
  currency: "{tracker_currency}"
  category_column: 2
  year_header_row: 2
  month_header_row: 3

statement:
  provider: "nordea"
  parser: "nordea_account_statement"
  currency: "{tracker_currency}"

confidence_thresholds:
  auto_write: 0.85
  review_required: 0.60
  reject_below: 0.60

writer:
  overwrite_fixed_rows: false
  highlight_auto_filled_cells: false

local_llm:
  provider: "ollama"
  endpoint: "http://localhost:11434"
  model: "gemma4:26b"
  second_model: "gemma4:12b"
  fallback_model: "qwen3:14b"
  timeout_seconds: 180
  keep_alive: "30m"
  include_raw_description: false

trust_policy:
  auto_max_amount: 1000
  min_agreement: 2
  never_auto_categories:
    - "Rent (monthly)"
    - "Full-time job (net)"
"""


def _categories_yaml() -> str:
    return """category_registry:
  - label: Income (net)
    type: derived
  - Full-time job (net)
  - Other income
  - label: Cashflow
    type: derived
  - label: Living expenses
    type: parent
    allow_new_children: true
    children:
      - Rent (monthly)
      - Groceries (monthly)
      - Transportation
  - label: Services
    type: parent
    allow_new_children: true
    children:
      - Mobile phone (monthly)
      - Internet (monthly)
      - Cloud services
  - label: Insurance
    type: parent
    allow_new_children: true
    children:
      - Insurance (monthly)
  - label: Investments
    type: parent
    allow_new_children: true
    children:
      - Brokerage contributions
      - Pension contributions
  - label: Assets
    type: parent
    allow_new_children: true
    children:
      - Cash savings
      - Brokerage account
      - Pension account
  - label: Total net worth
    type: derived

aliases:
  Groceries: Groceries (monthly)
  Mobile phone: Mobile phone (monthly)
"""


def _rules_yaml() -> str:
    return """historical_mappings: {}

rules:
  - category: "Full-time job (net)"
    match_keywords: ["synthetic employer", "synthetic payroll"]
    direction: "income"
    confidence: 0.95
  - category: "Groceries (monthly)"
    match_keywords: ["synthetic grocer"]
    direction: "expense"
    confidence: 0.95
  - category: "Mobile phone (monthly)"
    match_keywords: ["synthetic telecom"]
    direction: "expense"
    confidence: 0.95

recurring_rules: []

fixed_rows: []

carry_forward_rows: []
"""


def _profile_yaml(tracker_currency: str, profile_paths: dict[str, str]) -> str:
    return f"""profile:
  name: "default"
  tracker_currency: "{tracker_currency}"

profile_paths:
  tracker_workbook: "{profile_paths["tracker_workbook"]}"
  raw_statements_dir: "{profile_paths["raw_statements_dir"]}"
  watched_folder_dir: "{profile_paths["watched_folder_dir"]}"
  reports_dir: "{profile_paths["reports_dir"]}"
  processed_workbooks_dir: "{profile_paths["processed_workbooks_dir"]}"
  backups_dir: "{profile_paths["backups_dir"]}"
  logs_dir: "{profile_paths["logs_dir"]}"
  category_memory_dir: "{profile_paths["category_memory_dir"]}"
  importer_profiles_dir: "{profile_paths["importer_profiles_dir"]}"
  local_rules_file: "{profile_paths["local_rules_file"]}"
  proxy_split_rules_file: "{profile_paths["proxy_split_rules_file"]}"

privacy:
  original_workbook_write_policy: "never_modify_directly"
  commit_target_policy: "copied_workbook_only"
  model_output_policy: "consensus_or_review"
  importer_profile_storage: "private_local_default"
"""


def _synthetic_nordea_csv(tracker_currency: str) -> str:
    return (
        "\ufeffBooking date;Amount;Balance;Currency;Name;Title;Sender;Recipient;Reconciled\n"
        f"2026/04/01;25000,00;25000,00;{tracker_currency};"
        "SYNTHETIC EMPLOYER;Synthetic payroll;;;Yes\n"
        f"2026/04/05;-450,25;24549,75;{tracker_currency};"
        "SYNTHETIC GROCER;Synthetic groceries;;;Yes\n"
        f"2026/04/08;-149,00;24400,75;{tracker_currency};"
        "SYNTHETIC TELECOM;Synthetic phone;;;Yes\n"
    )
