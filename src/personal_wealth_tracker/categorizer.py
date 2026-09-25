from __future__ import annotations

from dataclasses import replace
from decimal import Decimal, ROUND_HALF_UP

from .category_memory import HUMAN_PROVENANCE, CategoryMemory, match_category_memory
from .config import AppConfig, ProxySplitAllocation, ProxySplitRule, RecurringRule, Rule
from .models import CategorizedTransaction, Transaction
from .trust_policy import apply_trust_policy
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
    proxy_split_results = _proxy_split_results_by_transaction(transactions, config)
    categorized: list[CategorizedTransaction] = []
    for transaction in transactions:
        split_items = proxy_split_results.get(transaction.transaction_id)
        if split_items is not None:
            categorized.extend(split_items)
            continue
        categorized.append(_categorize(transaction, config, category_memory))
    return apply_trust_policy(categorized, config)


def _proxy_split_results_by_transaction(
    transactions: list[Transaction], config: AppConfig
) -> dict[str, list[CategorizedTransaction]]:
    results: dict[str, list[CategorizedTransaction]] = {}
    assigned_transaction_ids: set[str] = set()
    for rule in config.proxy_split_rules:
        candidates = [
            transaction
            for transaction in transactions
            if transaction.transaction_id not in assigned_transaction_ids
            and _matches_proxy_split_rule(transaction, rule)
        ]
        if not candidates:
            continue

        allocation_total = _allocation_total(rule)
        eligible = [transaction for transaction in candidates if abs(transaction.amount) >= allocation_total]
        underfunded = [transaction for transaction in candidates if abs(transaction.amount) < allocation_total]

        if rule.monthly_limit is not None and len(eligible) > rule.monthly_limit:
            for transaction in eligible:
                results[transaction.transaction_id] = [
                    _blocked_proxy_split(
                        transaction,
                        rule,
                        "Multiple proxy split candidates matched this reporting month; review required.",
                    )
                ]
        else:
            for transaction in eligible:
                results[transaction.transaction_id] = _proxy_split_result(transaction, rule)

        for transaction in underfunded:
            results[transaction.transaction_id] = [
                _blocked_proxy_split(
                    transaction,
                    rule,
                    "Proxy split candidate below configured proxy split allocation total; review required.",
                )
            ]

        assigned_transaction_ids.update(transaction.transaction_id for transaction in candidates)
    return results


def _proxy_split_result(transaction: Transaction, rule: ProxySplitRule) -> list[CategorizedTransaction]:
    allocations = tuple(
        (allocation, _allocation_amount(allocation, rule))
        for allocation in rule.allocations
    )
    allocation_total = sum((amount for _, amount in allocations), Decimal("0.00"))
    residual = (abs(transaction.amount) - allocation_total).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    source_id = transaction.transaction_id
    split_items = [
        CategorizedTransaction(
            transaction=transaction,
            suggested_category=None,
            confidence=1.0,
            categorization_method="proxy_split_source",
            reason=f"Proxy split source for {rule.name}; excluded from workbook totals.",
            source_transaction_id=source_id,
            split_rule=rule.name,
            split_role="source",
        )
    ]
    for allocation, amount in allocations:
        split_items.append(
            CategorizedTransaction(
                transaction=_split_transaction(transaction, rule, allocation, amount),
                suggested_category=allocation.category,
                confidence=1.0,
                categorization_method="proxy_split_allocation",
                reason=(
                    "Proxy split allocation: "
                    f"{allocation.base_amount} * {rule.conversion_rate} = {amount} DKK."
                ),
                source_transaction_id=source_id,
                split_rule=rule.name,
                split_role=allocation.role,
                allocated_amount=amount,
            )
        )
    if residual >= Decimal("0.01"):
        split_items.append(
            CategorizedTransaction(
                transaction=_residual_transaction(transaction, rule, residual),
                suggested_category=None,
                confidence=0.0,
                categorization_method="proxy_split_residual",
                reason="Proxy split residual needs current-month review.",
                source_transaction_id=source_id,
                split_rule=rule.name,
                split_role="residual",
                residual_amount=residual,
            )
        )
    return split_items


def _allocation_total(rule: ProxySplitRule) -> Decimal:
    return sum(
        (_allocation_amount(allocation, rule) for allocation in rule.allocations),
        Decimal("0.00"),
    )


def _blocked_proxy_split(
    transaction: Transaction, rule: ProxySplitRule, reason: str
) -> CategorizedTransaction:
    return CategorizedTransaction(
        transaction=transaction,
        suggested_category=None,
        confidence=0.0,
        categorization_method="proxy_split_blocked",
        reason=reason,
        source_transaction_id=transaction.transaction_id,
        split_rule=rule.name,
        split_role="source",
    )


def _matches_proxy_split_rule(transaction: Transaction, rule: ProxySplitRule) -> bool:
    normalized_description = normalize_text(transaction.description)
    if rule.direction and not _direction_matches(transaction, normalized_description, rule.direction):
        return False
    return any(normalize_text(keyword) in normalized_description for keyword in rule.match_keywords)


def _allocation_amount(allocation: ProxySplitAllocation, rule: ProxySplitRule) -> Decimal:
    return (allocation.base_amount * rule.conversion_rate).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def _residual_transaction(source: Transaction, rule: ProxySplitRule, amount: Decimal) -> Transaction:
    signed_amount = amount if source.amount >= 0 else -amount
    return replace(
        source,
        transaction_id=f"{source.transaction_id}:split:{rule.name}:residual",
        description=f"{source.description} [{rule.name}:residual]",
        amount=signed_amount,
        balance=None,
        original_amount=None,
        original_currency=None,
        details=(
            *source.details,
            f"proxy_split_source={source.transaction_id}",
            f"proxy_split_rule={rule.name}",
            "proxy_split_role=residual",
        ),
    )


def _split_transaction(
    source: Transaction,
    rule: ProxySplitRule,
    allocation: ProxySplitAllocation,
    amount: Decimal,
) -> Transaction:
    signed_amount = amount if source.amount >= 0 else -amount
    return replace(
        source,
        transaction_id=f"{source.transaction_id}:split:{rule.name}:{allocation.role}",
        description=f"{source.description} [{rule.name}:{allocation.role}]",
        amount=signed_amount,
        balance=None,
        original_amount=allocation.base_amount,
        original_currency=None,
        details=(
            *source.details,
            f"proxy_split_source={source.transaction_id}",
            f"proxy_split_rule={rule.name}",
            f"proxy_split_role={allocation.role}",
        ),
    )


def _categorize(
    transaction: Transaction, config: AppConfig, category_memory: CategoryMemory | None
) -> CategorizedTransaction:
    normalized_description = normalize_text(transaction.description)

    memory_match = (
        match_category_memory(transaction, category_memory) if category_memory else None
    )
    if memory_match and memory_match.provenance == HUMAN_PROVENANCE:
        return _result(
            transaction,
            memory_match.category,
            0.97,
            "category_memory",
            "Confirmed category memory match.",
        )

    guidance_alias = _match_pattern(normalized_description, config.guidance_aliases)
    if guidance_alias:
        reason = (
            "Refund matched guidance alias; nets against category in reporting month."
            if _is_refund_like(transaction, normalized_description)
            else "Guidance alias match."
        )
        return _result(transaction, guidance_alias, 0.97, "guidance_alias", reason)

    if memory_match:
        return _result(
            transaction,
            memory_match.category,
            0.97,
            "category_memory",
            "Trusted auto category memory match.",
        )

    historical = _match_pattern(normalized_description, config.historical_mappings)
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
            reason,
        )

    recurring = _match_recurring(transaction, normalized_description, config.recurring_rules)
    if recurring:
        return _result(
            transaction,
            recurring.category,
            recurring.confidence,
            "recurring",
            "Recurring amount/date rule match.",
        )

    rule = _match_rule(transaction, normalized_description, config.rules)
    if rule:
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
            reason,
        )

    if _is_refund_like(transaction, normalized_description):
        return _result(
            transaction,
            None,
            0.0,
            "unmatched",
            "Refund-like transaction needs review because no deterministic category matched.",
        )

    return _result(
        transaction,
        None,
        0.0,
        "unmatched",
        "No historical or keyword rule matched.",
    )


def _match_pattern(description: str, mappings: dict[str, str]) -> str | None:
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
    reason: str,
) -> CategorizedTransaction:
    return CategorizedTransaction(
        transaction=transaction,
        suggested_category=category,
        confidence=confidence,
        categorization_method=method,
        reason=reason,
    )
