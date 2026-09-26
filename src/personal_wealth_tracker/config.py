from __future__ import annotations

import json
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
    model: str = "gemma4:26b"
    second_model: str = "gemma4:12b"
    fallback_model: str = "qwen3:14b"
    timeout_seconds: float = 180.0
    keep_alive: str = "30m"
    include_raw_description: bool = False


DEFAULT_NEVER_AUTO_CATEGORIES = frozenset(
    {
        "Rent (monthly)",
        "Parent B",
        "Parent A",
        "Home insurance (yearly)",
        "Liability insurance (yearly)",
        "Pension A",
        "Pension B",
        "Stock investment plan",
        "Full-time job (net)",
    }
)


@dataclass(frozen=True)
class TrustPolicySettings:
    auto_max_amount: Decimal = Decimal(1000)
    min_agreement: int = 2
    min_confidence: float = 0.85
    never_auto_categories: frozenset[str] = DEFAULT_NEVER_AUTO_CATEGORIES


@dataclass(frozen=True)
class AppConfig:
    sheet_name: str
    tracker_currency: str
    category_column: int
    year_header_row: int
    month_header_row: int
    statement_currency: str
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
    trust_policy: TrustPolicySettings = field(default_factory=TrustPolicySettings)
    guidance_aliases: dict[str, str] = field(default_factory=dict)


def _load_yaml(path: Path) -> dict[str, Any]:
    return _yaml_mapping(path.read_text(encoding="utf-8"), path)


def _yaml_mapping(text: str, source: object) -> dict[str, Any]:
    loaded = _parse_yaml(text, source) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected mapping in {source}")
    return loaded


def _parse_yaml(text: str, source: object) -> Any:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required. Install dependencies with `uv sync`.") from exc

    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {source}: {exc}") from exc


def _load_optional_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _load_yaml(path)


def load_config(
    config_dir: Path,
    category_registry_additions: tuple[CategoryRegistryAddition, ...] = (),
) -> AppConfig:
    """Config from `config_dir`, with pending new leaves registered in memory only."""
    settings = _load_yaml(config_dir / "settings.yaml")
    categories_path = config_dir / "categories.yaml"
    categories_text = categories_path.read_text(encoding="utf-8")
    if category_registry_additions:
        categories_text = _categories_text_with_additions(
            categories_text, category_registry_additions
        )
    categories = _yaml_mapping(categories_text, categories_path)
    rules_doc = _merge_rules_docs(
        _load_yaml(config_dir / "rules.yaml"),
        _load_optional_yaml(config_dir / "rules.local.yaml"),
    )

    tracker = settings.get("tracker", {})
    statement = settings.get("statement", {})
    thresholds = settings.get("confidence_thresholds", {})
    writer = settings.get("writer", {})
    local_llm = settings.get("local_llm", {})
    trust_policy = settings.get("trust_policy") or {}
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
        guidance_aliases=_guidance_aliases(
            _load_optional_yaml(config_dir / "guidance_aliases.local.yaml"),
            category_registry,
        ),
        trust_policy=TrustPolicySettings(
            auto_max_amount=Decimal(str(trust_policy.get("auto_max_amount", "1000"))),
            min_agreement=int(trust_policy.get("min_agreement", 2)),
            min_confidence=float(thresholds.get("auto_write", 0.85)),
            never_auto_categories=frozenset(
                str(category)
                for category in trust_policy.get(
                    "never_auto_categories", DEFAULT_NEVER_AUTO_CATEGORIES
                )
            ),
        ),
    )


def _local_llm_settings(doc: Any) -> LocalLLMSettings:
    if doc is None:
        doc = {}
    if not isinstance(doc, dict):
        raise ValueError("Expected local_llm settings to be a mapping.")
    return LocalLLMSettings(
        provider=str(doc.get("provider", "ollama")),
        endpoint=str(doc.get("endpoint", "http://localhost:11434")).rstrip("/"),
        model=str(doc.get("model", "gemma4:26b")),
        second_model=str(doc.get("second_model", "gemma4:12b")),
        fallback_model=str(doc.get("fallback_model", "qwen3:14b")),
        timeout_seconds=float(doc.get("timeout_seconds", 180.0)),
        keep_alive=str(doc.get("keep_alive", "30m")),
        include_raw_description=bool(doc.get("include_raw_description", False)),
    )


def _guidance_aliases(doc: dict[str, Any], registry: CategoryRegistry) -> dict[str, str]:
    aliases = {str(pattern): str(category) for pattern, category in doc.items()}
    for pattern, category in aliases.items():
        if not registry.is_leaf_category(category):
            raise ValueError(
                f"guidance alias {pattern!r} targets {category!r}, which is not a leaf category."
            )
    return aliases


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


def pending_category_registry_additions(
    config_dir: Path,
    additions: tuple[CategoryRegistryAddition, ...],
) -> tuple[CategoryRegistryAddition, ...]:
    """Validated new leaves not yet in categories.yaml; a leaf already under its parent is dropped."""
    if not additions:
        return ()

    registry = _category_registry(_load_yaml(config_dir / "categories.yaml"))
    pending = tuple(
        addition
        for addition in additions
        if addition.leaf_category
        not in registry.children_by_parent.get(addition.parent_category, ())
    )
    _validate_category_registry_additions(registry, pending)
    return pending


def persist_category_registry_additions(
    config_dir: Path,
    additions: tuple[CategoryRegistryAddition, ...],
) -> None:
    """Insert each new leaf under its parent's `children:`, leaving every other byte untouched."""
    if not additions:
        return
    path = config_dir / "categories.yaml"
    path.write_bytes(
        _categories_text_with_additions(path.read_bytes().decode("utf-8"), additions).encode(
            "utf-8"
        )
    )


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


def _categories_text_with_additions(
    text: str,
    additions: tuple[CategoryRegistryAddition, ...],
) -> str:
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines(keepends=True)
    for addition in additions:
        lines = _insert_leaf_lines(lines, addition, newline)
    edited = "".join(lines)
    registry = _category_registry(_yaml_mapping(edited, "categories.yaml"))
    for addition in additions:
        if addition.leaf_category not in registry.children_by_parent.get(
            addition.parent_category, ()
        ):
            raise ValueError(
                f"Could not register {addition.leaf_category!r} under "
                f"{addition.parent_category!r} in categories.yaml."
            )
    return edited


def _insert_leaf_lines(
    lines: list[str],
    addition: CategoryRegistryAddition,
    newline: str,
) -> list[str]:
    parent_row, key_column = _category_registry_parent_line(lines, addition.parent_category)
    block_end = _block_end(lines, parent_row + 1, key_column - 1)
    children_row = next(
        (
            row
            for row in range(parent_row + 1, block_end)
            if _indent(lines[row]) == key_column and lines[row].lstrip().startswith("children:")
        ),
        None,
    )
    lines = list(lines)
    if children_row is None:
        insert_at = _last_content_row(lines, parent_row, block_end) + 1
        lines.insert(insert_at, " " * key_column + "children:" + newline)
        children_row, block_end = insert_at, insert_at + 1
    else:
        inline = lines[children_row].split("children:", 1)[1].split("#", 1)[0].strip()
        if inline == "[]":
            lines[children_row] = " " * key_column + "children:" + newline
        elif inline:
            raise ValueError(
                f"Children of category {addition.parent_category!r} must be a block list "
                "to register a new leaf."
            )

    first_child = next(
        (row for row in range(children_row + 1, block_end) if _is_content(lines[row])), None
    )
    dash_column = key_column if first_child is None else _indent(lines[first_child])
    list_end = _list_end(lines, children_row + 1, block_end, dash_column)
    insert_at = _last_content_row(lines, children_row, list_end) + 1
    if insert_at == len(lines) and not lines[-1].endswith("\n"):
        lines[-1] += newline
    description = json.dumps(addition.description, ensure_ascii=False)
    lines[insert_at:insert_at] = [
        f"{' ' * dash_column}- label: {_yaml_scalar(addition.leaf_category)}{newline}",
        f"{' ' * (dash_column + 2)}description: {description}{newline}",
    ]
    return lines


def _category_registry_parent_line(lines: list[str], parent_category: str) -> tuple[int, int]:
    """Row of the `- label: <parent>` entry and the column of its keys."""
    for row, line in enumerate(lines):
        if not line.lstrip().startswith("- label:"):
            continue
        try:
            (entry,) = _parse_yaml(line.strip(), "categories.yaml entry")
        except (TypeError, ValueError):
            continue
        if _category_label(entry) == parent_category:
            return row, _indent(line) + 2
    raise ValueError(f"Category registry parent {parent_category!r} was not found.")


def _block_end(lines: list[str], start: int, parent_indent: int) -> int:
    """First content row at or left of `parent_indent`, i.e. the end of the nested block."""
    for row in range(start, len(lines)):
        if _is_content(lines[row]) and _indent(lines[row]) <= parent_indent:
            return row
    return len(lines)


def _list_end(lines: list[str], start: int, end: int, dash_column: int) -> int:
    for row in range(start, end):
        line = lines[row]
        if not _is_content(line):
            continue
        if _indent(line) < dash_column or (
            _indent(line) == dash_column and not line.lstrip().startswith("-")
        ):
            return row
    return end


def _last_content_row(lines: list[str], start: int, end: int) -> int:
    return max((row for row in range(start, end) if _is_content(lines[row])), default=start)


def _is_content(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith("#")


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _yaml_scalar(value: str) -> str:
    plain = value.strip() == value and not any(char in value for char in ":#'\"{}[],&*!|>%@`")
    if plain and _parse_yaml(value, "categories.yaml label") == value:
        return value
    return json.dumps(value, ensure_ascii=False)


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
