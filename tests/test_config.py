from pathlib import Path

import pytest

from personal_wealth_tracker.config import load_config


def test_load_config_merges_ignored_local_rules(tmp_path):
    _write(tmp_path / "settings.yaml", "tracker:\n  currency: DKK\nstatement:\n  currency: DKK\n")
    _write(
        tmp_path / "categories.yaml",
        "categories:\n  - Public Category\n  - Private Category\naliases: {}\n",
    )
    _write(
        tmp_path / "rules.yaml",
        """
historical_mappings:
  PUBLIC: Public Category
rules:
  - category: Public Category
    match_keywords: [public]
    direction: expense
    confidence: 0.9
recurring_rules:
  - category: Public Category
    amount: "100.00"
    amount_tolerance: "1.00"
    day_min: 1
    day_max: 5
    match_keywords: [public recurring]
    direction: expense
    confidence: 0.9
fixed_rows:
  - Public Category
carry_forward_rows:
  - Public Carry Forward
""",
    )
    _write(
        tmp_path / "rules.local.yaml",
        """
historical_mappings:
  PRIVATE: Private Category
rules:
  - category: Private Category
    match_keywords: [private]
    direction: expense
    confidence: 0.95
recurring_rules:
  - category: Private Category
    amount: "200.00"
    amount_tolerance: "2.00"
    day_min: 10
    day_max: 15
    match_keywords: [private recurring]
    direction: expense
    confidence: 0.95
fixed_rows:
  - Private Category
carry_forward_rows:
  - Private Carry Forward
""",
    )

    config = load_config(tmp_path)

    assert config.historical_mappings["PUBLIC"] == "Public Category"
    assert config.historical_mappings["PRIVATE"] == "Private Category"
    assert [rule.category for rule in config.rules] == ["Public Category", "Private Category"]
    assert [rule.category for rule in config.recurring_rules] == [
        "Public Category",
        "Private Category",
    ]
    assert config.fixed_rows == frozenset({"Public Category", "Private Category"})
    assert config.carry_forward_rows == frozenset(
        {"Public Carry Forward", "Private Carry Forward"}
    )


def test_project_config_includes_mastercard_refund_category_and_directional_rules():
    config = load_config(Path("config"))

    mastercard_rules = [
        rule
        for rule in config.rules
        if "mastercard" in {keyword.lower() for keyword in rule.match_keywords}
    ]

    assert "Mastercard refund" in config.categories
    assert [(rule.category, rule.direction, rule.confidence) for rule in mastercard_rules] == [
        ("Mastercard refund", "income", 0.98),
        ("Nordea Credit Card", "expense", 0.98),
    ]


def test_project_config_exposes_parent_leaf_category_registry():
    config = load_config(Path("config"))

    assert "Rent (monthly)" in config.category_registry.leaf_categories
    assert "Parent B" in config.category_registry.leaf_categories
    assert "Shopping (monthly)" in config.category_registry.leaf_categories
    assert "Living expenses" in config.category_registry.parent_categories
    assert "Services" in config.category_registry.parent_categories
    assert "Insurance" in config.category_registry.parent_categories
    assert "Living expenses" in config.category_registry.new_leaf_parent_categories
    assert "Services" in config.category_registry.new_leaf_parent_categories
    assert "Insurance" in config.category_registry.new_leaf_parent_categories
    assert "Living expenses" not in config.categories
    assert "Insurance" not in config.categories
    assert "Taxes" not in config.categories


def test_load_config_supports_tree_shaped_category_registry(tmp_path):
    _write(tmp_path / "settings.yaml", "tracker:\n  currency: DKK\nstatement:\n  currency: DKK\n")
    _write(
        tmp_path / "categories.yaml",
        """
category_registry:
  - label: Living expenses
    type: parent
    allow_new_children: true
    children:
      - label: Rent
      - Shopping
  - label: Insurance
    type: parent
    allow_new_children: false
    children:
      - House insurance
  - label: Total net worth
    type: derived
aliases:
  Groceries: Shopping
""",
    )
    _write(tmp_path / "rules.yaml", "{}\n")

    config = load_config(tmp_path)

    assert config.category_registry.leaf_categories == (
        "Rent",
        "Shopping",
        "House insurance",
    )
    assert config.category_registry.parent_categories == (
        "Living expenses",
        "Insurance",
        "Total net worth",
    )
    assert config.category_registry.new_leaf_parent_categories == ("Living expenses",)
    assert config.category_registry.children_by_parent == {
        "Living expenses": ("Rent", "Shopping"),
        "Insurance": ("House insurance",),
    }
    assert config.categories == config.category_registry.leaf_categories
    assert config.aliases == {"Groceries": "Shopping"}
    assert config.category_registry.is_leaf_category("Shopping")
    assert not config.category_registry.is_leaf_category("Living expenses")
    assert config.category_registry.is_parent_category("Insurance")
    assert config.category_registry.allows_new_leaf_children("Living expenses")
    assert not config.category_registry.allows_new_leaf_children("Insurance")


def test_load_config_builds_leaf_registry_from_flat_categories_for_compatibility(tmp_path):
    _write(tmp_path / "settings.yaml", "tracker:\n  currency: DKK\nstatement:\n  currency: DKK\n")
    _write(
        tmp_path / "categories.yaml",
        """
categories:
  - Public Category
  - Private Category
aliases:
  Public: Public Category
""",
    )
    _write(tmp_path / "rules.yaml", "{}\n")

    config = load_config(tmp_path)

    assert config.category_registry.leaf_categories == (
        "Public Category",
        "Private Category",
    )
    assert config.category_registry.parent_categories == ()
    assert config.category_registry.new_leaf_parent_categories == ()
    assert config.categories == ("Public Category", "Private Category")
    assert config.aliases == {"Public": "Public Category"}


def test_load_config_rejects_duplicate_category_labels_case_insensitively(tmp_path):
    _write(tmp_path / "settings.yaml", "tracker:\n  currency: DKK\nstatement:\n  currency: DKK\n")
    _write(
        tmp_path / "categories.yaml",
        """
category_registry:
  - label: Living expenses
    type: parent
    allow_new_children: true
    children:
      - Shopping
      - " shopping "
aliases: {}
""",
    )
    _write(tmp_path / "rules.yaml", "{}\n")

    with pytest.raises(ValueError, match="Duplicate category label.*Shopping.*shopping"):
        load_config(tmp_path)


def test_load_config_preserves_exact_display_labels_without_creating_aliases(tmp_path):
    _write(tmp_path / "settings.yaml", "tracker:\n  currency: DKK\nstatement:\n  currency: DKK\n")
    _write(
        tmp_path / "categories.yaml",
        """
category_registry:
  - label: Services
    type: parent
    allow_new_children: true
    children:
      - " Apple Cloud "
      - label: "Fitness center membership (monthly)"
aliases:
  Fitness: "Fitness center membership (monthly)"
""",
    )
    _write(tmp_path / "rules.yaml", "{}\n")

    config = load_config(tmp_path)

    assert config.category_registry.leaf_categories == (
        " Apple Cloud ",
        "Fitness center membership (monthly)",
    )
    assert config.aliases == {"Fitness": "Fitness center membership (monthly)"}


def _write(path: Path, content: str) -> None:
    path.write_text(content.lstrip(), encoding="utf-8")
