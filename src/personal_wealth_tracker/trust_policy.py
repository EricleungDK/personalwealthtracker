from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal

from .config import AppConfig, TrustPolicySettings
from .models import Authority, CategorizedTransaction, Vote

TRUSTED_STATEMENT_ADAPTER = "trusted_statement_adapter"
MONTHLY_REVIEW_DECISION_TIER = "monthly_review_decision"
PROXY_SPLIT_SOURCE_TIER = "proxy_split_source"


@dataclass(frozen=True)
class Evidence:
    tier: str
    category: str | None
    confidence: float
    votes: tuple[Vote, ...] = ()
    provenance: str = TRUSTED_STATEMENT_ADAPTER
    new_leaf: bool = False

    @property
    def agreement(self) -> int:
        """Distinct models voting for the category; one model twice is one voter."""
        return len({vote.source for vote in self.votes if vote.category == self.category})


@dataclass(frozen=True)
class RowFacts:
    amount: Decimal


@dataclass(frozen=True)
class AuthorityDecision:
    authority: Authority
    reason: str


def decide_authority(
    evidence: Evidence, row: RowFacts, policy: TrustPolicySettings
) -> AuthorityDecision:
    if evidence.provenance != TRUSTED_STATEMENT_ADAPTER:
        return _review("Untrusted import rows are review-only.")
    if evidence.tier == MONTHLY_REVIEW_DECISION_TIER:
        return _auto("Monthly Review Decision.")
    if evidence.tier == PROXY_SPLIT_SOURCE_TIER:
        return _auto("Proxy split source is excluded from workbook totals.")
    if evidence.category is None:
        return _review("No category suggested.")
    if evidence.new_leaf:
        return _review(f"{evidence.category} is a proposed new leaf.")
    if evidence.category in policy.never_auto_categories:
        return _review(f"{evidence.category} is a never-auto category.")
    if abs(row.amount) > policy.auto_max_amount:
        return _review(f"Amount {abs(row.amount)} is above the auto cap {policy.auto_max_amount}.")
    if evidence.votes:
        if evidence.agreement < policy.min_agreement:
            return _review(
                f"{evidence.agreement} of {policy.min_agreement} required model votes agree."
            )
        return _auto(f"{evidence.agreement} model votes agree.")
    if evidence.confidence < policy.min_confidence:
        return _review(
            f"Confidence {evidence.confidence:.2f} is below the auto threshold "
            f"{policy.min_confidence:.2f}."
        )
    return _auto(f"Deterministic {evidence.tier} match.")


def apply_trust_policy(
    categorized: list[CategorizedTransaction], config: AppConfig
) -> list[CategorizedTransaction]:
    return [stamp_authority(item, config) for item in categorized]


def stamp_authority(item: CategorizedTransaction, config: AppConfig) -> CategorizedTransaction:
    decision = decide_authority(
        Evidence(
            tier=item.categorization_method,
            category=item.suggested_category,
            confidence=item.confidence,
            votes=item.votes,
            new_leaf=item.new_leaf_parent is not None,
        ),
        RowFacts(amount=item.transaction.amount),
        config.trust_policy,
    )
    return replace(item, authority=decision.authority, authority_reason=decision.reason)


def _auto(reason: str) -> AuthorityDecision:
    return AuthorityDecision(Authority.auto, reason)


def _review(reason: str) -> AuthorityDecision:
    return AuthorityDecision(Authority.review, reason)
