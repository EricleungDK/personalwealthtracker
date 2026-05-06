from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Update a personal wealth tracker from a statement.")
    parser.add_argument("--tracker", required=True, type=Path, help="Path to the tracker workbook.")
    parser.add_argument("--statement", required=True, type=Path, help="Path to the Nordea PDF statement.")
    parser.add_argument("--year", required=True, type=int, help="Target tracker year.")
    parser.add_argument("--month", required=True, help="Target tracker month, e.g. Feb.")
    parser.add_argument("--config-dir", type=Path, default=Path("config"), help="Config directory.")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"), help="Report output directory.")
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Write eligible values to a copied workbook. Dry-run is the default.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_pipeline(
        tracker_path=args.tracker,
        statement_path=args.statement,
        config_dir=args.config_dir,
        year=args.year,
        month=args.month,
        output_dir=args.output_dir,
        commit=args.commit,
    )

    print(f"Mode: {result.mode}")
    print(f"Transactions processed: {len(result.transactions)}")
    print(f"Report: {result.report_path}")
    print(f"Audit log: {result.audit_path}")
    if result.output_workbook_path:
        print(f"Output workbook: {result.output_workbook_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
