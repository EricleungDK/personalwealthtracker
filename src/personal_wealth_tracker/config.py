from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Rule:
    category: str
    match_keywords: tuple[str, ...]
    direction: str | None
    confidence: float


@dataclass(frozen=True)
class RecurringRule:
    category: str
    amount: Decimal | None
    amount_tolerance: Decimal
    day_min: int | None
    day_max: int | None
    match_keywords: tuple[str, ...]
    direction: str | None
    confidence: float


@dataclass(frozen=True)
class AppConfig:
    sheet_name: str
    tracker_currency: str
    category_column: int
    year_header_row: int
    month_header_row: int
    statement_currency: str
    auto_write_threshold: float
    review_threshold: float
    reject_threshold: float
    overwrite_fixed_rows: bool
    highlight_auto_filled_cells: bool
    categories: tuple[str, ...]
    aliases: dict[str, str]
    historical_mappings: dict[str, str]
    rules: tuple[Rule, ...]
    fixed_rows: frozenset[str]
    recurring_rules: tuple[RecurringRule, ...] = ()


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required. Install dependencies with `uv sync`.") from exc

    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected mapping in {path}")
    return loaded


def _load_optional_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _load_yaml(path)


def load_config(config_dir: Path) -> AppConfig:
    settings = _load_yaml(config_dir / "settings.yaml")
    categories = _load_yaml(config_dir / "categories.yaml")
    rules_doc = _merge_rules_docs(
        _load_yaml(config_dir / "rules.yaml"),
        _load_optional_yaml(config_dir / "rules.local.yaml"),
    )

    tracker = settings.get("tracker", {})
    statement = settings.get("statement", {})
    thresholds = settings.get("confidence_thresholds", {})
    writer = settings.get("writer", {})

    rules = tuple(
        Rule(
            category=str(item["category"]),
            match_keywords=tuple(str(keyword) for keyword in item.get("match_keywords", [])),
            direction=item.get("direction"),
            confidence=float(item.get("confidence", 0.8)),
        )
        for item in rules_doc.get("rules", [])
    )
    recurring_rules = tuple(
        RecurringRule(
            category=str(item["category"]),
            amount=Decimal(str(item["amount"])) if item.get("amount") is not None else None,
            amount_tolerance=Decimal(str(item.get("amount_tolerance", "0.00"))),
            day_min=int(item["day_min"]) if item.get("day_min") is not None else None,
            day_max=int(item["day_max"]) if item.get("day_max") is not None else None,
            match_keywords=tuple(str(keyword) for keyword in item.get("match_keywords", [])),
            direction=item.get("direction"),
            confidence=float(item.get("confidence", 0.9)),
        )
        for item in rules_doc.get("recurring_rules", [])
    )

    return AppConfig(
        sheet_name=str(tracker.get("sheet_name", "Net worth")),
        tracker_currency=str(tracker.get("currency", "DKK")),
        category_column=int(tracker.get("category_column", 2)),
        year_header_row=int(tracker.get("year_header_row", 2)),
        month_header_row=int(tracker.get("month_header_row", 3)),
        statement_currency=str(statement.get("currency", "DKK")),
        auto_write_threshold=float(thresholds.get("auto_write", 0.85)),
        review_threshold=float(thresholds.get("review_required", 0.60)),
        reject_threshold=float(thresholds.get("reject_below", 0.60)),
        overwrite_fixed_rows=bool(writer.get("overwrite_fixed_rows", False)),
        highlight_auto_filled_cells=bool(writer.get("highlight_auto_filled_cells", False)),
        categories=tuple(str(category) for category in categories.get("categories", [])),
        aliases={str(k): str(v) for k, v in categories.get("aliases", {}).items()},
        historical_mappings={
            str(k): str(v) for k, v in rules_doc.get("historical_mappings", {}).items()
        },
        rules=rules,
        fixed_rows=frozenset(str(row) for row in rules_doc.get("fixed_rows", [])),
        recurring_rules=recurring_rules,
    )


def _merge_rules_docs(base: dict[str, Any], local: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    merged["historical_mappings"] = {
        **base.get("historical_mappings", {}),
        **local.get("historical_mappings", {}),
    }
    merged["rules"] = [*base.get("rules", []), *local.get("rules", [])]
    merged["recurring_rules"] = [
        *base.get("recurring_rules", []),
        *local.get("recurring_rules", []),
    ]
    merged["fixed_rows"] = sorted({*base.get("fixed_rows", []), *local.get("fixed_rows", [])})
    return merged
