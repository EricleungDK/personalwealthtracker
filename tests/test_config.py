from pathlib import Path

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


def _write(path: Path, content: str) -> None:
    path.write_text(content.lstrip(), encoding="utf-8")
