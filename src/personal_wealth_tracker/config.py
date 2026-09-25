from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from .models import CategoryRegistryAddition


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
class ProxySplitAllocation:
    role: str
    category: str
    base_amount: Decimal


@dataclass(frozen=True)
class ProxySplitRule:
    name: str
    match_keywords: tuple[str, ...]
    direction: str | None
    conversion_rate: Decimal
    allocations: tuple[ProxySplitAllocation, ...]
    monthly_limit: int | None = 1


@dataclass(frozen=True)
class CategoryRegistry:
    leaf_categories: tuple[str, ...] = ()
    parent_categories: tuple[str, ...] = ()
    new_leaf_parent_categories: tuple[str, ...] = ()
    children_by_parent: dict[str, tuple[str, ...]] = field(default_factory=dict)
    category_type_by_label: dict[str, str] = field(default_factory=dict)
    leaf_glossary: dict[str, str] = field(default_factory=dict)

    def is_leaf_category(self, label: str) -> bool:
        return label in self.leaf_categories

    def is_parent_category(self, label: str) -> bool:
        return label in self.parent_categories

    def allows_new_leaf_children(self, label: str) -> bool:
        return label in self.new_leaf_parent_categories


@dataclass(frozen=True)
class LocalLLMSettings:
    provider: str = "ollama"
    endpoint: str = "http://localhost:11434"
    model: str = "gemma4:12b"
    fallback_model: str = "gemma4:e4b"
    timeout_seconds: float = 180.0
    keep_alive: str = "30m"
    include_raw_description: bool = False


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
    carry_forward_rows: frozenset[str] = frozenset()
    recurring_rules: tuple[RecurringRule, ...] = ()
    proxy_split_rules: tuple[ProxySplitRule, ...] = ()
    category_registry: CategoryRegistry = field(default_factory=CategoryRegistry)
    local_llm: LocalLLMSettings = field(default_factory=LocalLLMSettings)


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
    local_llm = settings.get("local_llm", {})
    category_registry = _category_registry(categories)

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
        categories=category_registry.leaf_categories,
        aliases={str(k): str(v) for k, v in categories.get("aliases", {}).items()},
        category_registry=category_registry,
        historical_mappings={
            str(k): str(v) for k, v in rules_doc.get("historical_mappings", {}).items()
        },
        rules=rules,
        fixed_rows=frozenset(str(row) for row in rules_doc.get("fixed_rows", [])),
        carry_forward_rows=frozenset(
            str(row) for row in rules_doc.get("carry_forward_rows", [])
        ),
        recurring_rules=recurring_rules,
        proxy_split_rules=_proxy_split_rules(rules_doc, category_registry),
        local_llm=_local_llm_settings(local_llm),
    )


def _local_llm_settings(doc: Any) -> LocalLLMSettings:
    if doc is None:
        doc = {}
    if not isinstance(doc, dict):
        raise ValueError("Expected local_llm settings to be a mapping.")
    return LocalLLMSettings(
        provider=str(doc.get("provider", "ollama")),
        endpoint=str(doc.get("endpoint", "http://localhost:11434")).rstrip("/"),
        model=str(doc.get("model", "gemma4:12b")),
        fallback_model=str(doc.get("fallback_model", "gemma4:e4b")),
        timeout_seconds=float(doc.get("timeout_seconds", 180.0)),
        keep_alive=str(doc.get("keep_alive", "30m")),
        include_raw_description=bool(doc.get("include_raw_description", False)),
    )


def _proxy_split_rules(
    rules_doc: dict[str, Any],
    category_registry: CategoryRegistry,
) -> tuple[ProxySplitRule, ...]:
    rules: list[ProxySplitRule] = []
    for index, item in enumerate(rules_doc.get("proxy_split_rules", []), start=1):
        if not isinstance(item, dict):
            raise ValueError(f"proxy_split_rules entry {index} must be a mapping.")
        name = str(item.get("name", "")).strip()
        if not name:
            raise ValueError(f"proxy_split_rules entry {index} must include a name.")
        keywords = tuple(str(keyword) for keyword in item.get("match_keywords", []))
        if not keywords:
            raise ValueError(f"proxy_split_rules {name!r} must include match_keywords.")
        conversion_rate = _positive_decimal(
            item.get("conversion_rate"),
            f"proxy_split_rules {name!r} conversion_rate",
        )
        monthly_limit = item.get("monthly_limit", 1)
        if monthly_limit is not None:
            monthly_limit = int(monthly_limit)
            if monthly_limit <= 0:
                raise ValueError(f"proxy_split_rules {name!r} monthly_limit must be positive.")
        allocations = _proxy_split_allocations(name, item.get("allocations"), category_registry)
        rules.append(
            ProxySplitRule(
                name=name,
                match_keywords=keywords,
                direction=item.get("direction"),
                conversion_rate=conversion_rate,
                allocations=allocations,
                monthly_limit=monthly_limit,
            )
        )
    return tuple(rules)


def _proxy_split_allocations(
    rule_name: str,
    raw_allocations: Any,
    category_registry: CategoryRegistry,
) -> tuple[ProxySplitAllocation, ...]:
    if not isinstance(raw_allocations, list) or not raw_allocations:
        raise ValueError(f"proxy_split_rules {rule_name!r} must include allocations.")
    allocations: list[ProxySplitAllocation] = []
    for index, item in enumerate(raw_allocations, start=1):
        if not isinstance(item, dict):
            raise ValueError(
                f"proxy_split_rules {rule_name!r} allocation {index} must be a mapping."
            )
        role = str(item.get("role", "")).strip()
        if not role:
            raise ValueError(
                f"proxy_split_rules {rule_name!r} allocation {index} must include a role."
            )
        category = str(item.get("category", "")).strip()
        if not category_registry.is_leaf_category(category):
            raise ValueError(
                f"proxy_split_rules {rule_name!r} allocation category {category!r} "
                "must be a leaf category."
            )
        allocations.append(
            ProxySplitAllocation(
                role=role,
                category=category,
                base_amount=_positive_decimal(
                    item.get("base_amount"),
                    f"proxy_split_rules {rule_name!r} allocation {role!r} base_amount",
                ),
            )
        )
    return tuple(allocations)


def _positive_decimal(value: Any, label: str) -> Decimal:
    if value is None:
        raise ValueError(f"{label} is required.")
    amount = Decimal(str(value))
    if amount <= 0:
        raise ValueError(f"{label} must be positive.")
    return amount


def register_category_registry_additions(
    config_dir: Path,
    additions: tuple[CategoryRegistryAddition, ...],
) -> tuple[CategoryRegistryAddition, ...]:
    if not additions:
        return ()

    path = config_dir / "categories.yaml"
    doc = _load_yaml(path)
    registry = _category_registry(doc)
    _validate_category_registry_additions(registry, additions)

    if "category_registry" not in doc:
        raise ValueError("New leaf category registration requires category_registry config.")
    nodes = doc["category_registry"]
    if not isinstance(nodes, list):
        raise ValueError("Expected category_registry to be a list.")

    for addition in additions:
        parent_node = _category_registry_parent_node(nodes, addition.parent_category)
        children = parent_node.setdefault("children", [])
        if not isinstance(children, list):
            raise ValueError(
                f"Expected children for category {addition.parent_category!r} to be a list."
            )
        children.append(addition.leaf_category)

    _write_yaml(path, doc)
    return additions


def _validate_category_registry_additions(
    registry: CategoryRegistry,
    additions: tuple[CategoryRegistryAddition, ...],
) -> None:
    seen = {
        label.strip().casefold(): label
        for label in registry.category_type_by_label
    }
    for addition in additions:
        if not registry.allows_new_leaf_children(addition.parent_category):
            raise ValueError(
                "Review decisions contain new_parent_category "
                f"{addition.parent_category!r}, which is not allowed to receive new leaf "
                "categories."
            )
        normalized = addition.leaf_category.strip().casefold()
        if not normalized:
            raise ValueError("Review decisions contain blank new_leaf_category.")
        existing = seen.get(normalized)
        if existing is not None:
            raise ValueError(
                "Duplicate category label after trimming/case-folding: "
                f"{existing!r} conflicts with {addition.leaf_category!r}."
            )
        seen[normalized] = addition.leaf_category


def _category_registry_parent_node(nodes: list[Any], parent_category: str) -> dict[str, Any]:
    for node in nodes:
        if isinstance(node, dict) and _category_label(node) == parent_category:
            return node
    raise ValueError(f"Category registry parent {parent_category!r} was not found.")


def _write_yaml(path: Path, doc: dict[str, Any]) -> None:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required. Install dependencies with `uv sync`.") from exc

    path.write_text(
        yaml.safe_dump(doc, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _category_registry(doc: dict[str, Any]) -> CategoryRegistry:
    if "category_registry" in doc:
        return _tree_category_registry(doc["category_registry"])
    return _flat_category_registry(doc.get("categories", []))


def _flat_category_registry(items: Any) -> CategoryRegistry:
    if not isinstance(items, list):
        raise ValueError("Expected categories to be a list.")

    seen: dict[str, str] = {}
    leaves: list[str] = []
    type_by_label: dict[str, str] = {}
    for item in items:
        label = str(item)
        _record_category_label(label, seen)
        leaves.append(label)
        type_by_label[label] = "leaf"

    return CategoryRegistry(
        leaf_categories=tuple(leaves),
        category_type_by_label=type_by_label,
        leaf_glossary={label: "" for label in leaves},
    )


def _tree_category_registry(items: Any) -> CategoryRegistry:
    if not isinstance(items, list):
        raise ValueError("Expected category_registry to be a list.")

    seen: dict[str, str] = {}
    leaves: list[str] = []
    parents: list[str] = []
    new_leaf_parents: list[str] = []
    children_by_parent: dict[str, tuple[str, ...]] = {}
    type_by_label: dict[str, str] = {}
    glossary: dict[str, str] = {}

    for item in items:
        label = _category_label(item)
        node_type = _category_node_type(item)
        _record_category_label(label, seen)

        if node_type == "leaf":
            leaves.append(label)
            type_by_label[label] = "leaf"
            glossary[label] = _category_description(item)
            continue

        parents.append(label)
        type_by_label[label] = node_type
        child_labels = tuple(_tree_child_labels(item, seen, leaves, type_by_label, glossary))
        if child_labels:
            children_by_parent[label] = child_labels
        if node_type != "derived" and _allows_new_children(item):
            new_leaf_parents.append(label)

    return CategoryRegistry(
        leaf_categories=tuple(leaves),
        parent_categories=tuple(parents),
        new_leaf_parent_categories=tuple(new_leaf_parents),
        children_by_parent=children_by_parent,
        category_type_by_label=type_by_label,
        leaf_glossary=glossary,
    )


def _tree_child_labels(
    item: Any,
    seen: dict[str, str],
    leaves: list[str],
    type_by_label: dict[str, str],
    glossary: dict[str, str],
) -> list[str]:
    if not isinstance(item, dict):
        return []
    children = item.get("children", [])
    if children is None:
        return []
    if not isinstance(children, list):
        raise ValueError(f"Expected children for category {_category_label(item)!r} to be a list.")

    child_labels: list[str] = []
    for child in children:
        label = _category_label(child)
        if _category_node_type(child) != "leaf":
            raise ValueError(f"Category child {label!r} must be a leaf.")
        _record_category_label(label, seen)
        leaves.append(label)
        child_labels.append(label)
        type_by_label[label] = "leaf"
        glossary[label] = _category_description(child)
    return child_labels


def _category_label(item: Any) -> str:
    if isinstance(item, dict):
        if "label" not in item:
            raise ValueError("Category registry entries must include a label.")
        return str(item["label"])
    return str(item)


def _category_description(item: Any) -> str:
    if not isinstance(item, dict):
        return ""
    return str(item.get("description") or "").strip()


def _category_node_type(item: Any) -> str:
    if not isinstance(item, dict):
        return "leaf"
    raw_type = str(item.get("type", item.get("kind", ""))).strip().casefold()
    if not raw_type:
        raw_type = "parent" if "children" in item else "leaf"
    if raw_type == "section":
        return "parent"
    if raw_type not in {"leaf", "parent", "derived"}:
        raise ValueError(f"Unsupported category type {raw_type!r}.")
    if raw_type == "leaf" and item.get("children"):
        raise ValueError(f"Leaf category {_category_label(item)!r} cannot define children.")
    return raw_type


def _allows_new_children(item: Any) -> bool:
    return isinstance(item, dict) and bool(item.get("allow_new_children", False))


def _record_category_label(label: str, seen: dict[str, str]) -> None:
    normalized = label.strip().casefold()
    if not normalized:
        raise ValueError("Category label cannot be empty.")
    existing = seen.get(normalized)
    if existing is not None:
        raise ValueError(
            "Duplicate category label after trimming/case-folding: "
            f"{existing!r} conflicts with {label!r}."
        )
    seen[normalized] = label


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
    merged["proxy_split_rules"] = [
        *base.get("proxy_split_rules", []),
        *local.get("proxy_split_rules", []),
    ]
    merged["fixed_rows"] = sorted({*base.get("fixed_rows", []), *local.get("fixed_rows", [])})
    merged["carry_forward_rows"] = sorted(
        {*base.get("carry_forward_rows", []), *local.get("carry_forward_rows", [])}
    )
    return merged
