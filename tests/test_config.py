from pathlib import Path
from decimal import Decimal
import difflib
import subprocess

import pytest

from personal_wealth_tracker.config import (
    TrustPolicySettings,
    load_config,
    pending_category_registry_additions,
    persist_category_registry_additions,
)
from personal_wealth_tracker.models import CategoryRegistryAddition


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


def test_load_config_defaults_local_llm_provider_settings(tmp_path):
    _write(tmp_path / "settings.yaml", "tracker:\n  currency: DKK\nstatement:\n  currency: DKK\n")
    _write(
        tmp_path / "categories.yaml",
        "categories:\n  - Public Category\naliases: {}\n",
    )
    _write(tmp_path / "rules.yaml", "{}\n")

    config = load_config(tmp_path)

    assert config.local_llm.provider == "ollama"
    assert config.local_llm.endpoint == "http://localhost:11434"
    assert config.local_llm.model == "gemma4:26b"
    assert config.local_llm.second_model == "gemma4:12b"
    assert config.local_llm.fallback_model == "qwen3:14b"
    assert config.local_llm.timeout_seconds == 180.0
    assert config.local_llm.keep_alive == "30m"
    assert config.local_llm.include_raw_description is False


def test_load_config_supports_local_llm_provider_overrides(tmp_path):
    _write(
        tmp_path / "settings.yaml",
        """
tracker:
  currency: DKK
statement:
  currency: DKK
local_llm:
  provider: ollama
  endpoint: "http://127.0.0.1:11435"
  model: "gemma4:e2b"
  second_model: "qwen3:14b"
  fallback_model: "gemma4:e4b"
  timeout_seconds: 5
  keep_alive: "5m"
  include_raw_description: true
""",
    )
    _write(
        tmp_path / "categories.yaml",
        "categories:\n  - Public Category\naliases: {}\n",
    )
    _write(tmp_path / "rules.yaml", "{}\n")

    config = load_config(tmp_path)

    assert config.local_llm.provider == "ollama"
    assert config.local_llm.endpoint == "http://127.0.0.1:11435"
    assert config.local_llm.model == "gemma4:e2b"
    assert config.local_llm.second_model == "qwen3:14b"
    assert config.local_llm.fallback_model == "gemma4:e4b"
    assert config.local_llm.timeout_seconds == 5.0
    assert config.local_llm.keep_alive == "5m"
    assert config.local_llm.include_raw_description is True


def test_load_config_defaults_trust_policy_settings(tmp_path):
    _write(tmp_path / "settings.yaml", "tracker:\n  currency: DKK\nstatement:\n  currency: DKK\n")
    _write(tmp_path / "categories.yaml", "categories:\n  - Public Category\naliases: {}\n")
    _write(tmp_path / "rules.yaml", "{}\n")

    config = load_config(tmp_path)

    assert config.trust_policy == TrustPolicySettings()


def test_load_config_reads_trust_policy_from_settings(tmp_path):
    _write(
        tmp_path / "settings.yaml",
        """
tracker:
  currency: DKK
statement:
  currency: DKK
confidence_thresholds:
  auto_write: 0.9
trust_policy:
  auto_max_amount: 250.50
  min_agreement: 3
  never_auto_categories:
    - Public Category
""",
    )
    _write(tmp_path / "categories.yaml", "categories:\n  - Public Category\naliases: {}\n")
    _write(tmp_path / "rules.yaml", "{}\n")

    config = load_config(tmp_path)

    assert config.trust_policy == TrustPolicySettings(
        auto_max_amount=Decimal("250.50"),
        min_agreement=3,
        min_confidence=0.9,
        never_auto_categories=frozenset({"Public Category"}),
    )


def test_example_settings_set_default_trust_policy(example_config_dir):
    config = load_config(example_config_dir)

    assert config.trust_policy == TrustPolicySettings()


def test_load_config_reads_ignored_guidance_alias_file(tmp_path):
    _write(tmp_path / "settings.yaml", "tracker:\n  currency: DKK\nstatement:\n  currency: DKK\n")
    _write(tmp_path / "categories.yaml", "categories:\n  - Lunch\n  - Public Category\naliases: {}\n")
    _write(tmp_path / "rules.yaml", "{}\n")
    _write(
        tmp_path / "guidance_aliases.local.yaml",
        "CANTEEN NORTH: Lunch\nCANTEEN SOUTH: Lunch\n",
    )

    config = load_config(tmp_path)

    assert config.guidance_aliases == {"CANTEEN NORTH": "Lunch", "CANTEEN SOUTH": "Lunch"}


def test_load_config_without_guidance_alias_file_has_no_aliases(tmp_path):
    _write(tmp_path / "settings.yaml", "tracker:\n  currency: DKK\nstatement:\n  currency: DKK\n")
    _write(tmp_path / "categories.yaml", "categories:\n  - Public Category\naliases: {}\n")
    _write(tmp_path / "rules.yaml", "{}\n")

    assert load_config(tmp_path).guidance_aliases == {}


def test_load_config_rejects_guidance_alias_to_unknown_leaf(tmp_path):
    _write(tmp_path / "settings.yaml", "tracker:\n  currency: DKK\nstatement:\n  currency: DKK\n")
    _write(tmp_path / "categories.yaml", "categories:\n  - Lunch\naliases: {}\n")
    _write(tmp_path / "rules.yaml", "{}\n")
    _write(tmp_path / "guidance_aliases.local.yaml", "CANTEEN NORTH: Canteen\n")

    with pytest.raises(ValueError) as error:
        load_config(tmp_path)

    assert str(error.value) == (
        "guidance alias 'CANTEEN NORTH' targets 'Canteen', which is not a leaf category."
    )


def test_guidance_alias_example_is_synthetic_and_real_file_is_ignored(tmp_path):
    example = Path("config/guidance_aliases.local.example.yaml")
    for name in ("settings.yaml", "categories.yaml", "rules.yaml"):
        _write(tmp_path / name, Path("config", name).read_text(encoding="utf-8"))
    _write(tmp_path / "guidance_aliases.local.yaml", example.read_text(encoding="utf-8"))

    aliases = load_config(tmp_path).guidance_aliases

    assert aliases
    assert all("EXAMPLE" in pattern for pattern in aliases)
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", "config/guidance_aliases.local.yaml"], check=False
    )
    assert ignored.returncode == 0


def test_load_config_supports_private_proxy_split_rules(tmp_path):
    _write(tmp_path / "settings.yaml", "tracker:\n  currency: DKK\nstatement:\n  currency: DKK\n")
    _write(
        tmp_path / "categories.yaml",
        """
category_registry:
  - label: Living expenses
    type: parent
    allow_new_children: true
    children:
      - Parent A
      - Parent B
aliases: {}
""",
    )
    _write(tmp_path / "rules.yaml", "{}\n")
    _write(
        tmp_path / "rules.local.yaml",
        """
proxy_split_rules:
  - name: example_transfer
    match_keywords: [revolut]
    direction: expense
    conversion_rate: "0.82"
    monthly_limit: 1
    allocations:
      - role: parent_a
        category: Parent A
        base_amount: "8000"
      - role: parent_b
        category: Parent B
        base_amount: "4000"
""",
    )

    config = load_config(tmp_path)

    rule = config.proxy_split_rules[0]
    assert rule.name == "example_transfer"
    assert rule.match_keywords == ("revolut",)
    assert rule.direction == "expense"
    assert rule.conversion_rate == Decimal("0.82")
    assert rule.monthly_limit == 1
    assert [(item.role, item.category, item.base_amount) for item in rule.allocations] == [
        ("parent_a", "Parent A", Decimal("8000")),
        ("parent_b", "Parent B", Decimal("4000")),
    ]


def test_load_config_rejects_proxy_split_targets_that_are_not_leaf_categories(tmp_path):
    _write(tmp_path / "settings.yaml", "tracker:\n  currency: DKK\nstatement:\n  currency: DKK\n")
    _write(
        tmp_path / "categories.yaml",
        """
category_registry:
  - label: Living expenses
    type: parent
    allow_new_children: true
    children:
      - Parent A
aliases: {}
""",
    )
    _write(tmp_path / "rules.yaml", "{}\n")
    _write(
        tmp_path / "rules.local.yaml",
        """
proxy_split_rules:
  - name: example_transfer
    match_keywords: [revolut]
    direction: expense
    conversion_rate: "0.82"
    allocations:
      - role: parent_a
        category: Living expenses
        base_amount: "8000"
""",
    )

    with pytest.raises(ValueError, match="proxy_split_rules.*Living expenses.*leaf"):
        load_config(tmp_path)


def test_example_config_includes_card_refund_category_and_directional_rules(example_config_dir):
    config = load_config(example_config_dir)

    card_rules = [
        rule
        for rule in config.rules
        if "synthetic card" in {keyword.lower() for keyword in rule.match_keywords}
    ]

    assert "Card refund" in config.categories
    assert [(rule.category, rule.direction, rule.confidence) for rule in card_rules] == [
        ("Card refund", "income", 0.98),
        ("Credit card payment", "expense", 0.98),
    ]


def test_example_config_exposes_parent_leaf_category_registry(example_config_dir):
    config = load_config(example_config_dir)

    assert "Rent (monthly)" in config.category_registry.leaf_categories
    assert "Groceries (monthly)" in config.category_registry.leaf_categories
    assert "Living expenses" in config.category_registry.parent_categories
    assert "Services" in config.category_registry.parent_categories
    assert "Insurance" in config.category_registry.parent_categories
    assert "Living expenses" in config.category_registry.new_leaf_parent_categories
    assert "Services" in config.category_registry.new_leaf_parent_categories
    assert "Insurance" in config.category_registry.new_leaf_parent_categories
    assert "Living expenses" not in config.categories
    assert "Insurance" not in config.categories
    assert "Cashflow" not in config.categories


def test_example_config_describes_every_leaf_category(example_config_dir):
    config = load_config(example_config_dir)

    glossary = config.category_registry.leaf_glossary

    assert set(glossary) == set(config.category_registry.leaf_categories)
    assert [leaf for leaf, description in glossary.items() if not description.strip()] == []


def test_example_config_stays_described_after_registering_new_leaves(example_config_dir):
    config_dir = example_config_dir
    categories_yaml = config_dir / "categories.yaml"
    before = categories_yaml.read_text(encoding="utf-8")
    additions = (
        CategoryRegistryAddition(
            "Services", "Claude subscription", ("tx-1",), "Claude subscription billing."
        ),
        CategoryRegistryAddition(
            "Living expenses", "Pet: supplies", ("tx-2",), "Added in monthly review Aug 2026."
        ),
    )

    persist_category_registry_additions(
        config_dir, pending_category_registry_additions(config_dir, additions)
    )

    after = categories_yaml.read_text(encoding="utf-8")
    diff = list(difflib.ndiff(before.splitlines(), after.splitlines()))
    assert [line for line in diff if line.startswith("- ")] == []
    assert [line[2:] for line in diff if line.startswith("+ ")] == [
        '  - label: "Pet: supplies"',
        '    description: "Added in monthly review Aug 2026."',
        "  - label: Claude subscription",
        '    description: "Claude subscription billing."',
    ]
    config = load_config(config_dir)
    glossary = config.category_registry.leaf_glossary
    assert set(glossary) == set(config.category_registry.leaf_categories)
    assert [leaf for leaf, description in glossary.items() if not description.strip()] == []
    assert config.category_registry.children_by_parent["Services"][-1] == "Claude subscription"
    assert pending_category_registry_additions(config_dir, additions) == ()


def test_registering_new_leaf_keeps_crlf_line_endings_and_fills_empty_children(tmp_path):
    categories_yaml = tmp_path / "categories.yaml"
    categories_yaml.write_bytes(
        b"category_registry:\r\n"
        b'  - label: "Plan #1"  # comment\r\n'
        b"  - label: Services\r\n"
        b"    allow_new_children: true\r\n"
        b"    children: []\r\n"
        b"aliases: {}\r\n"
    )

    persist_category_registry_additions(
        tmp_path,
        (CategoryRegistryAddition("Services", "Claude subscription", ("tx-1",), "Billing."),),
    )

    assert categories_yaml.read_bytes() == (
        b"category_registry:\r\n"
        b'  - label: "Plan #1"  # comment\r\n'
        b"  - label: Services\r\n"
        b"    allow_new_children: true\r\n"
        b"    children:\r\n"
        b"    - label: Claude subscription\r\n"
        b'      description: "Billing."\r\n'
        b"aliases: {}\r\n"
    )


def test_example_config_has_no_generic_subscriptions_leaf(example_config_dir):
    registry = load_config(example_config_dir).category_registry

    for leaf in ("Restaurants", "Entertainment"):
        assert registry.is_leaf_category(leaf)
    assert not registry.is_leaf_category("Subscriptions")
    assert registry.allows_new_leaf_children("Services")
    assert "Streaming subscription" in registry.children_by_parent["Services"]
    assert "Restaurants" in registry.children_by_parent["Living expenses"]
    assert "Groceries (monthly)" in registry.children_by_parent["Living expenses"]


def test_load_config_exposes_leaf_glossary_with_blank_missing_descriptions(tmp_path):
    _write(tmp_path / "settings.yaml", "tracker:\n  currency: DKK\nstatement:\n  currency: DKK\n")
    _write(
        tmp_path / "categories.yaml",
        """
category_registry:
  - label: Living expenses
    type: parent
    children:
      - label: Rent
        description: Monthly housing rent.
      - Shopping
  - label: Salary
    description: Net pay from employer.
  - label: Total net worth
    type: derived
aliases: {}
""",
    )
    _write(tmp_path / "rules.yaml", "{}\n")

    config = load_config(tmp_path)

    assert config.category_registry.leaf_glossary == {
        "Rent": "Monthly housing rent.",
        "Shopping": "",
        "Salary": "Net pay from employer.",
    }


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
