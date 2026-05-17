from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .category_memory import import_reviewed_decisions
from .cleanup import run_currency_label_cleanup
from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Update a personal wealth tracker from a statement."
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
    parser.add_argument(
        "--output-dir", type=Path, default=Path("reports"), help="Report output directory."
    )
    parser.add_argument(
        "--category-memory-dir",
        type=Path,
        default=Path("data/category_memory"),
        help="Private generated category memory directory.",
    )
    parser.add_argument(
        "--review-decisions",
        type=Path,
        help="Reviewed XLSX decisions to apply by exact transaction ID.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Write eligible values to a copied workbook. Dry-run is the default.",
    )
    return parser


def build_category_memory_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
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
    return parser


def build_cleanup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
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


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if argv and argv[0] == "learn-category-memory":
        args = build_category_memory_parser().parse_args(argv[1:])
        try:
            result = import_reviewed_decisions(args.decisions, args.memory_dir)
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

    args = build_parser().parse_args(argv)
    try:
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
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Mode: {result.mode}")
    print(f"Statement parser: {result.statement_parser}")
    print(f"Transactions processed: {len(result.transactions)}")
    print(f"Report: {result.report_path}")
    print(f"Audit log: {result.audit_path}")
    if result.output_workbook_path:
        print(f"Output workbook: {result.output_workbook_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
