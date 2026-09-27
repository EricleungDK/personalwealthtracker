from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from .category_memory import import_reviewed_decisions
from .cleanup import run_currency_label_cleanup
from .importer_profiles import (
    export_importer_profile,
    learn_importer_profile,
    reset_importer_profile,
)
from .models import Authority, RunResult
from .pipeline import exception_sheet_path, run_monthly, run_pipeline
from .setup_workspace import initialize_local_workspace
from .statement_import_assistant import run_statement_import_assistant
from .template_workbook import create_template_workbook, customize_template_workbook
from .workbook import rows_in_review


SUBCOMMANDS = (
    ("monthly", "Main flow: categorise the newest statement and commit the month."),
    ("learn-category-memory", "Import reviewed decisions into Category Memory by hand."),
    ("cleanup-currency-labels", "One-off workbook currency label cleanup."),
    ("import-statement", "Review artifact for an unknown statement format."),
    ("importer-profile", "Learn, export or reset private Importer Profiles."),
    ("template-workbook", "Create or customize the synthetic Template Workbook."),
    ("setup", "Initialize a local workspace from the public template."),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wealth-tracker",
        description=(
            "Update a personal wealth tracker from a statement. Without a subcommand this "
            "runs one explicit month (the per-month command below)."
        ),
        epilog="subcommands (run `wealth-tracker <subcommand> --help`):\n"
        + "\n".join(f"  {name:<25}{summary}" for name, summary in SUBCOMMANDS),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--tracker", required=True, type=Path, help="Path to the tracker workbook.")
    parser.add_argument(
        "--statement", required=True, type=Path, help="Path to the Nordea statement."
    )
    parser.add_argument(
        "--statement-format",
        choices=("auto", "nordea-csv", "nordea-pdf"),
        default="auto",
        help="Statement parser selection. Auto infers from .csv or .pdf extension.",
    )
    parser.add_argument("--year", required=True, type=int, help="Target tracker year.")
    parser.add_argument("--month", required=True, help="Target tracker month, e.g. Feb.")
    parser.add_argument("--config-dir", type=Path, default=Path("config"), help="Config directory.")
    _add_profile_path_args(parser)
    parser.add_argument(
        "--review-decisions",
        type=Path,
        help="Reviewed XLSX decisions to apply by exact transaction ID.",
    )
    parser.add_argument(
        "--local-llm-suggestions",
        action="store_true",
        help="Ask the two local Ollama models (Consensus); `monthly` always does.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help=(
            "Write the month to a copied workbook when no rows remain in review. "
            "Dry-run is the default."
        ),
    )
    return parser


def build_monthly_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wealth-tracker monthly",
        description=(
            "Categorise the newest statement export for its month; commit when no rows "
            "remain in review, otherwise write the Exception Sheet."
        )
    )
    parser.add_argument(
        "--tracker",
        type=Path,
        help="Path to the tracker workbook (default: profile, else 'Net Worth Tracker.xlsx').",
    )
    parser.add_argument(
        "--statements-dir",
        type=Path,
        help=(
            "Raw statements folder; the newest CSV is used "
            "(default: profile, else data/raw_statements)."
        ),
    )
    parser.add_argument("--config-dir", type=Path, default=Path("config"), help="Config directory.")
    _add_profile_path_args(parser)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the Exception Sheet and Audit without memory or workbook writes.",
    )
    return parser


def build_category_memory_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wealth-tracker learn-category-memory",
        description="Import confirmed reviewed decisions into category memory."
    )
    parser.add_argument(
        "--decisions",
        required=True,
        type=Path,
        help="Reviewed decision CSV or XLSX.",
    )
    parser.add_argument(
        "--memory-dir",
        type=Path,
        default=Path("data/category_memory"),
        help="Private category memory directory.",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path("config"),
        help="Config directory containing the YAML category registry.",
    )
    return parser


def build_cleanup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wealth-tracker cleanup-currency-labels",
        description="Run one-off tracker workbook cleanup tasks."
    )
    parser.add_argument("--tracker", required=True, type=Path, help="Path to the tracker workbook.")
    parser.add_argument(
        "--tracker-currency",
        default="DKK",
        help="Target tracker currency label for workbook text cleanup.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports"),
        help="Cleanup report output directory.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Write cleanup changes to a copied workbook. Dry-run is the default.",
    )
    return parser


def build_import_statement_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wealth-tracker import-statement",
        description="Create a review artifact for an unknown statement format."
    )
    parser.add_argument(
        "--statement",
        required=True,
        type=Path,
        help="Path to the unknown-format statement or export.",
    )
    parser.add_argument("--year", required=True, type=int, help="Target tracker year.")
    parser.add_argument("--month", required=True, help="Target tracker month, e.g. Feb.")
    parser.add_argument(
        "--tracker-currency",
        default="DKK",
        help="Expected tracker currency for import validation.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports"),
        help="Review artifact output directory.",
    )
    parser.add_argument(
        "--local-model",
        action="store_true",
        help="Request optional local model assistance. Without a model client this falls back.",
    )
    parser.add_argument(
        "--importer-profiles-dir",
        type=Path,
        default=Path("data/importer_profiles"),
        help="Private local Importer Profile directory for Educated Import Guesses.",
    )
    parser.add_argument(
        "--importer-profile",
        help="Importer Profile name to use for Educated Import Guesses.",
    )
    return parser


def build_importer_profile_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wealth-tracker importer-profile",
        description="Manage private local Importer Profiles."
    )
    subparsers = parser.add_subparsers(dest="profile_command", required=True)

    learn = subparsers.add_parser(
        "learn",
        help="Learn or update an Importer Profile from a confirmed import review CSV.",
    )
    learn.add_argument("--reviewed-import", required=True, type=Path)
    learn.add_argument("--profile-name", required=True)
    learn.add_argument(
        "--profiles-dir",
        type=Path,
        default=Path("data/importer_profiles"),
        help="Private local Importer Profile directory.",
    )
    learn.add_argument("--tracker-currency", default="DKK")

    export = subparsers.add_parser(
        "export",
        help="Explicitly export one Importer Profile to a chosen path.",
    )
    export.add_argument("--profile-name", required=True)
    export.add_argument("--output", required=True, type=Path)
    export.add_argument(
        "--profiles-dir",
        type=Path,
        default=Path("data/importer_profiles"),
        help="Private local Importer Profile directory.",
    )

    reset = subparsers.add_parser(
        "reset",
        help="Delete one private local Importer Profile.",
    )
    reset.add_argument("--profile-name", required=True)
    reset.add_argument(
        "--profiles-dir",
        type=Path,
        default=Path("data/importer_profiles"),
        help="Private local Importer Profile directory.",
    )
    return parser


def build_template_workbook_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wealth-tracker template-workbook",
        description="Create the public synthetic Template Workbook."
    )
    subparsers = parser.add_subparsers(dest="template_command", required=True)

    create = subparsers.add_parser(
        "create",
        help="Generate a versioned synthetic Template Workbook.",
    )
    create.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path for the generated template workbook.",
    )
    create.add_argument(
        "--tracker-currency",
        default="DKK",
        help="Tracker Currency to write into template metadata.",
    )
    create.add_argument(
        "--start-year",
        type=int,
        default=2026,
        help="Year for the initial Jan-Dec template period block.",
    )
    create.add_argument(
        "--sheet-name",
        default="Net worth",
        help="Worksheet name for the template tracker sheet.",
    )
    customize = subparsers.add_parser(
        "customize",
        help="Customize supported v1 template dimensions.",
    )
    customize.add_argument(
        "--template",
        required=True,
        type=Path,
        help="Source template workbook.",
    )
    customize.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path for the customized template workbook.",
    )
    customize.add_argument(
        "--tracker-currency",
        help="Optional Tracker Currency to write into template metadata.",
    )
    customize.add_argument(
        "--rename",
        action="append",
        default=[],
        metavar="OLD=NEW",
        help="Rename one existing category or section label. May be repeated.",
    )
    return parser


def build_setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wealth-tracker setup",
        description="Initialize a local workspace from the public template."
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path("."),
        help="Directory to initialize.",
    )
    parser.add_argument(
        "--tracker-currency",
        default="DKK",
        help="Tracker Currency to write into sample config and template metadata.",
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=2026,
        help="Year for the initial Jan-Dec template period block.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing setup-managed files.",
    )
    parser.add_argument(
        "--reports-dir",
        help="Profile path override for report outputs, relative to the workspace.",
    )
    parser.add_argument(
        "--category-memory-dir",
        help="Profile path override for private Category Memory, relative to the workspace.",
    )
    parser.add_argument(
        "--importer-profiles-dir",
        help="Profile path override for private Importer Profiles, relative to the workspace.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if argv and argv[0] == "monthly":
        args = build_monthly_parser().parse_args(argv[1:])
        try:
            _apply_profile_paths(args, MONTHLY_PROFILE_PATHS)
            result = run_monthly(
                tracker_path=args.tracker,
                statements_dir=args.statements_dir,
                config_dir=args.config_dir,
                output_dir=args.output_dir,
                category_memory_dir=args.category_memory_dir,
                dry_run=args.dry_run,
                backups_dir=args.backups_dir,
                processed_dir=args.processed_dir,
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        _print_monthly_summary(result, args.output_dir)
        return 0

    if argv and argv[0] == "learn-category-memory":
        args = build_category_memory_parser().parse_args(argv[1:])
        try:
            result = import_reviewed_decisions(args.decisions, args.memory_dir, args.config_dir)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(f"Imported category memory decisions: {result.imported_count}")
        print(f"Skipped unconfirmed decisions: {result.skipped_unconfirmed_count}")
        print(f"Skipped unlearned decisions: {result.skipped_unlearned_count}")
        print(f"Skipped non-learnable decisions: {result.skipped_non_learnable_count}")
        print(f"Category memory: {result.memory_path}")
        return 0

    if argv and argv[0] == "cleanup-currency-labels":
        args = build_cleanup_parser().parse_args(argv[1:])
        result = run_currency_label_cleanup(
            tracker_path=args.tracker,
            tracker_currency=args.tracker_currency,
            output_dir=args.output_dir,
            commit=args.commit,
        )
        print(f"Mode: {result.mode}")
        print(f"Planned cleanup changes: {len(result.changes)}")
        print(f"Cleanup report: {result.report_path}")
        if result.output_workbook_path:
            print(f"Output workbook: {result.output_workbook_path}")
        return 0

    if argv and argv[0] == "import-statement":
        args = build_import_statement_parser().parse_args(argv[1:])
        result = run_statement_import_assistant(
            source_path=args.statement,
            output_dir=args.output_dir,
            year=args.year,
            month=args.month,
            tracker_currency=args.tracker_currency,
            local_model=args.local_model,
            profiles_dir=args.importer_profiles_dir,
            profile_name=args.importer_profile,
        )
        print("Mode: unknown-statement-import-review")
        print(f"Rows requiring review: {len(result.rows)}")
        print(f"Diagnostics: {len(result.diagnostics)}")
        print(f"Review artifact: {result.review_artifact_path}")
        return 0

    if argv and argv[0] == "importer-profile":
        args = build_importer_profile_parser().parse_args(argv[1:])
        if args.profile_command == "learn":
            result = learn_importer_profile(
                reviewed_import_path=args.reviewed_import,
                profiles_dir=args.profiles_dir,
                profile_name=args.profile_name,
                tracker_currency=args.tracker_currency,
            )
            print(f"Imported confirmed rows: {result.imported_count}")
            print(f"Skipped unconfirmed rows: {result.skipped_unconfirmed_count}")
            print(f"Importer Profile: {result.profile_path}")
            return 0
        if args.profile_command == "export":
            output_path = export_importer_profile(
                profiles_dir=args.profiles_dir,
                profile_name=args.profile_name,
                output_path=args.output,
            )
            print(f"Exported Importer Profile: {output_path}")
            return 0
        if args.profile_command == "reset":
            removed = reset_importer_profile(args.profiles_dir, args.profile_name)
            print(f"Importer Profile removed: {'yes' if removed else 'no'}")
            return 0

    if argv and argv[0] == "template-workbook":
        args = build_template_workbook_parser().parse_args(argv[1:])
        if args.template_command == "create":
            try:
                template_path = create_template_workbook(
                    args.output,
                    tracker_currency=args.tracker_currency,
                    start_year=args.start_year,
                    sheet_name=args.sheet_name,
                )
            except RuntimeError as exc:
                print(str(exc), file=sys.stderr)
                return 1
            print(f"Template workbook: {template_path}")
            return 0
        if args.template_command == "customize":
            try:
                customized_path = customize_template_workbook(
                    args.template,
                    args.output,
                    tracker_currency=args.tracker_currency,
                    label_renames=_parse_label_renames(args.rename),
                )
            except (RuntimeError, ValueError) as exc:
                print(str(exc), file=sys.stderr)
                return 1
            print(f"Customized template workbook: {customized_path}")
            return 0

    if argv and argv[0] == "setup":
        args = build_setup_parser().parse_args(argv[1:])
        try:
            result = initialize_local_workspace(
                args.workspace,
                tracker_currency=args.tracker_currency,
                start_year=args.start_year,
                profile_paths=_setup_profile_path_overrides(args),
                force=args.force,
            )
        except (RuntimeError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(f"Workspace: {result.workspace_dir}")
        print(f"Template workbook: {result.template_path}")
        print(f"Synthetic statement: {result.example_statement_path}")
        print(f"Files written: {len(result.written_files)}")
        print(f"Existing files preserved: {len(result.skipped_existing_files)}")
        return 0

    args = build_parser().parse_args(argv)
    try:
        _apply_profile_paths(args, PROFILE_PATHS)
        result = run_pipeline(
            tracker_path=args.tracker,
            statement_path=args.statement,
            config_dir=args.config_dir,
            year=args.year,
            month=args.month,
            output_dir=args.output_dir,
            category_memory_dir=args.category_memory_dir,
            commit=args.commit,
            statement_format=args.statement_format,
            review_decisions_path=args.review_decisions,
            local_llm_suggestions=args.local_llm_suggestions,
            backups_dir=args.backups_dir,
            processed_dir=args.processed_dir,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Mode: {result.mode}")
    print(f"Statement parser: {result.statement_parser}")
    print(f"Transactions processed: {len(result.transactions)}")
    print(f"Report: {result.report_path}")
    print(f"Audit log: {result.audit_path}")
    print(f"Rows in review: {result.review_count}")
    if result.review_xlsx_path:
        print(f"Exception sheet: {result.review_xlsx_path}")
    if result.output_workbook_path:
        print(f"Output workbook: {result.output_workbook_path}")
    return 0


def _print_monthly_summary(result: RunResult, output_dir: Path) -> None:
    review_rows = rows_in_review(result.categorized_transactions, result.updates)
    auto_count = sum(
        item.authority is Authority.auto for item in result.categorized_transactions
    )
    pending_amount = sum(abs(item.transaction.amount) for item in review_rows)
    currency = result.transactions[0].currency if result.transactions else ""
    exception_sheet = exception_sheet_path(output_dir, result.target_year, result.target_month)
    print(f"Mode: {result.mode}")
    print(f"Statement: {result.source_statement}")
    print(f"Month: {result.target_month} {result.target_year}")
    print(f"Auto rows: {auto_count}")
    print(f"Rows in review: {len(review_rows)}")
    print(f"Pending amount: {pending_amount:.2f} {currency}".rstrip())
    print(f"Report: {result.report_path}")
    print(f"Exception sheet: {exception_sheet}")
    if result.output_workbook_path:
        print(f"Output workbook: {result.output_workbook_path}")
        print("Next action: none; month committed.")
    elif review_rows and result.exception_sheet_unreviewed:
        print(
            f"Next action: Exception sheet not reviewed yet: {exception_sheet}; fill and save it "
            "(blank accepts, NONE rejects), then re-run `wealth-tracker monthly`."
        )
    elif review_rows:
        print(
            f"Next action: fill {exception_sheet} (blank accepts, NONE rejects), "
            "then re-run `wealth-tracker monthly`."
        )
    else:
        print("Next action: re-run `wealth-tracker monthly` without --dry-run to commit.")


DEFAULT_PROFILE = Path("profiles/default.local.yaml")

# CLI dest -> (profile_paths key, fallback when neither flag nor profile sets it)
PROFILE_PATHS = {
    "output_dir": ("reports_dir", Path("reports")),
    "category_memory_dir": ("category_memory_dir", Path("data/category_memory")),
    "backups_dir": ("backups_dir", Path("data/backups")),
    "processed_dir": ("processed_workbooks_dir", Path("data/processed")),
}
MONTHLY_PROFILE_PATHS = {
    "tracker": ("tracker_workbook", Path("Net Worth Tracker.xlsx")),
    "statements_dir": ("raw_statements_dir", Path("data/raw_statements")),
    **PROFILE_PATHS,
}


def _add_profile_path_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--profile",
        type=Path,
        help=(
            f"Profile whose profile_paths set the path defaults (default: {DEFAULT_PROFILE} "
            "when it exists). Paths are relative to the workspace that holds profiles/."
        ),
    )
    for flag, dest in (
        ("--output-dir", "output_dir"),
        ("--category-memory-dir", "category_memory_dir"),
        ("--backups-dir", "backups_dir"),
        ("--processed-dir", "processed_dir"),
    ):
        key, fallback = PROFILE_PATHS[dest]
        parser.add_argument(
            flag, dest=dest, type=Path, help=f"Default: profile {key}, else {fallback}."
        )


def _apply_profile_paths(
    args: argparse.Namespace, defaults: dict[str, tuple[str, Path]]
) -> None:
    """Fill unset path flags: explicit flag, then profile, then built-in fallback."""
    profile_paths = _load_profile_paths(args.profile)
    for dest, (key, fallback) in defaults.items():
        if getattr(args, dest) is None:
            setattr(args, dest, profile_paths.get(key, fallback))


def _load_profile_paths(profile: Path | None) -> dict[str, Path]:
    if profile is None:
        if not DEFAULT_PROFILE.exists():
            return {}
        profile = DEFAULT_PROFILE
    elif not profile.exists():
        raise ValueError(f"Profile not found: {profile}")
    document = yaml.safe_load(profile.read_text(encoding="utf-8")) or {}
    raw_paths = document.get("profile_paths") or {}
    if not isinstance(raw_paths, dict):
        raise ValueError(f"Profile {profile}: profile_paths must be a mapping.")
    workspace = profile.parent.parent if profile.parent.name == "profiles" else profile.parent
    return {key: workspace / str(value) for key, value in raw_paths.items()}


def _parse_label_renames(raw_renames: list[str]) -> dict[str, str]:
    renames: dict[str, str] = {}
    for raw_rename in raw_renames:
        if "=" not in raw_rename:
            raise ValueError(f"Template label rename {raw_rename!r} must use OLD=NEW.")
        old_label, new_label = raw_rename.split("=", 1)
        old_label = old_label.strip()
        new_label = new_label.strip()
        if not old_label or not new_label:
            raise ValueError(f"Template label rename {raw_rename!r} must use OLD=NEW.")
        renames[old_label] = new_label
    return renames


def _setup_profile_path_overrides(args: argparse.Namespace) -> dict[str, str]:
    overrides = {}
    if args.reports_dir:
        overrides["reports_dir"] = args.reports_dir
    if args.category_memory_dir:
        overrides["category_memory_dir"] = args.category_memory_dir
    if args.importer_profiles_dir:
        overrides["importer_profiles_dir"] = args.importer_profiles_dir
    return overrides


if __name__ == "__main__":
    raise SystemExit(main())
