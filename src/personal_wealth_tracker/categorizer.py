from __future__ import annotations

from .config import AppConfig, Rule
from .models import CategorizedTransaction, Transaction
from .utils import normalize_text


def categorize_transactions(
    transactions: list[Transaction], config: AppConfig
) -> list[CategorizedTransaction]:
    return [_categorize(transaction, config) for transaction in transactions]


def _categorize(transaction: Transaction, config: AppConfig) -> CategorizedTransaction:
    normalized_description = normalize_text(transaction.description)

    historical = _match_historical(normalized_description, config.historical_mappings)
    if historical:
        return _result(transaction, historical, 0.98, "historical", False, "Historical mapping match.")

    rule = _match_rule(transaction, normalized_description, config.rules)
    if rule:
        review_required = rule.confidence < config.auto_write_threshold
        return _result(
            transaction,
            rule.category,
            rule.confidence,
            "rule",
            review_required,
            "Keyword rule match.",
        )

    return _result(
        transaction,
        None,
        0.0,
        "unmatched",
        True,
        "No historical or keyword rule matched.",
    )


def _match_historical(description: str, mappings: dict[str, str]) -> str | None:
    for pattern, category in mappings.items():
        if normalize_text(pattern) in description:
            return category
    return None


def _match_rule(transaction: Transaction, description: str, rules: tuple[Rule, ...]) -> Rule | None:
    for rule in rules:
        if rule.direction and rule.direction != transaction.direction:
            continue
        if any(normalize_text(keyword) in description for keyword in rule.match_keywords):
            return rule
    return None


def _result(
    transaction: Transaction,
    category: str | None,
    confidence: float,
    method: str,
    review_required: bool,
    reason: str,
) -> CategorizedTransaction:
    return CategorizedTransaction(
        transaction=transaction,
        suggested_category=category,
        confidence=confidence,
        categorization_method=method,
        review_required=review_required,
        reason=reason,
    )
