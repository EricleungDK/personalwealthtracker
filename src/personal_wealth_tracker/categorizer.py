from __future__ import annotations

from .category_memory import CategoryMemory, match_category_memory
from .config import AppConfig, RecurringRule, Rule
from .models import CategorizedTransaction, Transaction
from .utils import normalize_text


REFUND_KEYWORDS = (
    "REFUND",
    "REFUSION",
    "REFUNDER",
    "RETURN",
    "RETURNED",
    "RETUR",
    "TILBAGEBETALING",
    "TILBAGEFORT",
)
EXPENSE_CLAIMS_CATEGORY = "Expense claims"


def categorize_transactions(
    transactions: list[Transaction],
    config: AppConfig,
    category_memory: CategoryMemory | None = None,
) -> list[CategorizedTransaction]:
    return [_categorize(transaction, config, category_memory) for transaction in transactions]


def _categorize(
    transaction: Transaction, config: AppConfig, category_memory: CategoryMemory | None
) -> CategorizedTransaction:
    normalized_description = normalize_text(transaction.description)

    if category_memory is not None:
        memory_match = match_category_memory(transaction, category_memory)
        if memory_match:
            return _result(
                transaction,
                memory_match.category,
                0.97,
                "category_memory",
                False,
                "Confirmed category memory match.",
            )

    historical = _match_historical(normalized_description, config.historical_mappings)
    if historical:
        reason = (
            "Refund matched historical mapping; nets against category in reporting month."
            if _is_refund_like(transaction, normalized_description)
            else "Historical mapping match."
        )
        return _result(
            transaction,
            historical,
            0.98,
            "historical",
            False,
            reason,
        )

    recurring = _match_recurring(transaction, normalized_description, config.recurring_rules)
    if recurring:
        review_required = recurring.confidence < config.auto_write_threshold
        return _result(
            transaction,
            recurring.category,
            recurring.confidence,
            "recurring",
            review_required,
            "Recurring amount/date rule match.",
        )

    rule = _match_rule(transaction, normalized_description, config.rules)
    if rule:
        review_required = rule.confidence < config.auto_write_threshold
        if _is_refund_against_expense_rule(transaction, normalized_description, rule.direction):
            reason = "Refund matched expense keyword rule; nets against category in reporting month."
        elif rule.category == EXPENSE_CLAIMS_CATEGORY:
            reason = "Expense claim keyword rule match."
        else:
            reason = "Keyword rule match."
        return _result(
            transaction,
            rule.category,
            rule.confidence,
            "rule",
            review_required,
            reason,
        )

    if _is_refund_like(transaction, normalized_description):
        return _result(
            transaction,
            None,
            0.0,
            "unmatched",
            True,
            "Refund-like transaction needs review because no deterministic category matched.",
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
        if rule.direction and not _direction_matches(transaction, description, rule.direction):
            continue
        if any(normalize_text(keyword) in description for keyword in rule.match_keywords):
            return rule
    return None


def _match_recurring(
    transaction: Transaction,
    description: str,
    rules: tuple[RecurringRule, ...],
) -> RecurringRule | None:
    for rule in rules:
        if rule.direction and not _direction_matches(transaction, description, rule.direction):
            continue
        if rule.day_min is not None and transaction.date.day < rule.day_min:
            continue
        if rule.day_max is not None and transaction.date.day > rule.day_max:
            continue
        if rule.amount is not None:
            delta = abs(abs(transaction.amount) - rule.amount)
            if delta > rule.amount_tolerance:
                continue
        if rule.match_keywords and not any(
            normalize_text(keyword) in description for keyword in rule.match_keywords
        ):
            continue
        return rule
    return None


def _direction_matches(
    transaction: Transaction,
    description: str,
    rule_direction: str,
) -> bool:
    return (
        rule_direction == transaction.direction
        or _is_refund_against_expense_rule(transaction, description, rule_direction)
    )


def _is_refund_against_expense_rule(
    transaction: Transaction,
    description: str,
    rule_direction: str | None,
) -> bool:
    return rule_direction == "expense" and _is_refund_like(transaction, description)


def _is_refund_like(transaction: Transaction, description: str) -> bool:
    return transaction.direction == "income" and any(
        keyword in description for keyword in REFUND_KEYWORDS
    )


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
