from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from difflib import get_close_matches
from typing import Protocol

from .category_memory import CategoryMemory, normalize_merchant_identity
from .config import AppConfig
from .models import CategorizedTransaction

MEMORY_NEIGHBOUR_LIMIT = 5
INVALID_RESPONSE = "invalid_response"
PROVIDER_FAILURE = "provider_failure"


@dataclass(frozen=True)
class Suggestion:
    """One Suggester answer for one row; `category=None` means NONE."""

    transaction_id: str
    category: str | None
    confidence: float
    alternatives: tuple[str, ...]
    evidence: str
    source: str
    failure: str | None = None


@dataclass(frozen=True)
class SuggesterContext:
    leaf_glossary: dict[str, str]
    guidance_aliases: dict[str, str] = field(default_factory=dict)
    memory_examples: tuple[tuple[str, str], ...] = ()
    reviewed_policy: str = ""

    def memory_neighbours(self, merchant_identity: str) -> tuple[tuple[str, str], ...]:
        category_by_identity = dict(self.memory_examples)
        closest = get_close_matches(
            merchant_identity, category_by_identity, n=MEMORY_NEIGHBOUR_LIMIT, cutoff=0.6
        )
        return tuple((identity, category_by_identity[identity]) for identity in closest)


class Suggester(Protocol):
    def suggest(
        self, rows: Sequence[CategorizedTransaction], context: SuggesterContext
    ) -> list[Suggestion]: ...


def build_suggester_context(
    config: AppConfig,
    memory: CategoryMemory,
    reviewed_policy: str = "",
) -> SuggesterContext:
    glossary = config.category_registry.leaf_glossary or {
        category: "" for category in config.categories
    }
    return SuggesterContext(
        leaf_glossary=dict(glossary),
        memory_examples=tuple(
            (mapping.merchant_identity, mapping.category) for mapping in memory.mappings
        ),
        reviewed_policy=reviewed_policy,
    )


def row_merchant_identity(item: CategorizedTransaction) -> str:
    transaction = item.transaction
    return normalize_merchant_identity(transaction.merchant or transaction.description)


@dataclass(frozen=True)
class ScriptedVote:
    category: str | None
    confidence: float
    evidence: str = "Scripted vote."
    alternatives: tuple[str, ...] = ()


class FakeSuggester:
    """Scripted votes by merchant identity for tests; unscripted rows answer NONE."""

    def __init__(self, votes: Mapping[str, ScriptedVote], source: str = "fake"):
        self.votes = dict(votes)
        self.source = source
        self.calls: list[tuple[tuple[CategorizedTransaction, ...], SuggesterContext]] = []

    def suggest(
        self, rows: Sequence[CategorizedTransaction], context: SuggesterContext
    ) -> list[Suggestion]:
        self.calls.append((tuple(rows), context))
        suggestions = []
        for item in rows:
            vote = self.votes.get(row_merchant_identity(item), ScriptedVote(None, 0.0))
            suggestions.append(
                Suggestion(
                    transaction_id=item.transaction.transaction_id,
                    category=vote.category,
                    confidence=vote.confidence,
                    alternatives=vote.alternatives,
                    evidence=vote.evidence,
                    source=self.source,
                )
            )
        return suggestions
