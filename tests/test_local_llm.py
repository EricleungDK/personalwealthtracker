import json
from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from personal_wealth_tracker.config import AppConfig, CategoryRegistry, LocalLLMSettings
from personal_wealth_tracker.local_llm import OllamaSuggester, apply_suggestions, local_consensus
from personal_wealth_tracker.models import Authority, CategorizedTransaction, Transaction, Vote
from personal_wealth_tracker.suggester import (
    ConsensusSuggester,
    FakeSuggester,
    ScriptedVote,
    SuggesterContext,
)

GLOSSARY = {"Apple Cloud": "iCloud storage subscription.", "Traveling": "Trains, flights, hotels."}


def test_ollama_request_uses_chat_schema_glossary_and_warm_deterministic_options():
    transport = _Transport(chat=[_chat_reply("Train ticket.", "Traveling", 0.9, ["Apple Cloud"])])
    item = _categorized("tx1", description="RAW NORDEA SECRET CONTEXT", merchant="UNKNOWN TRAIN")

    OllamaSuggester(_settings(), transport=transport).suggest([item], _context())

    url, payload, timeout = transport.requests[-1]
    assert url == "http://localhost:11434/api/chat"
    assert timeout == 180.0
    assert payload["model"] == "gemma4:12b"
    assert payload["stream"] is False
    assert payload["think"] is False
    assert payload["keep_alive"] == "30m"
    assert payload["options"] == {"temperature": 0}
    schema = payload["format"]
    assert list(schema["properties"])[:2] == ["reason", "category"]
    assert schema["properties"]["category"]["enum"] == ["Apple Cloud", "Traveling", "NONE"]
    assert set(schema["required"]) >= {"reason", "category", "confidence"}
    system, user = payload["messages"]
    assert system["role"] == "system"
    assert "Traveling: Trains, flights, hotels." in system["content"]
    assert "Apple Cloud: iCloud storage subscription." in system["content"]
    assert user["role"] == "user"
    row = json.loads(user["content"])
    assert row["merchant_identity"] == "UNKNOWN TRAIN"
    assert row["amount"] == "-42.50"
    assert "RAW NORDEA" not in user["content"]


def test_ollama_prompt_carries_memory_neighbours_and_reviewed_policy():
    transport = _Transport(chat=[_chat_reply("Seen before.", "Traveling", 0.9)])
    context = _context(
        memory_examples=(("UNKNOWN TRAINS", "Traveling"), ("ZZZ OTHER", "Apple Cloud")),
        reviewed_policy="Prefer NONE for private transfers.",
    )

    OllamaSuggester(_settings(), transport=transport).suggest(
        [_categorized("tx1", merchant="UNKNOWN TRAIN")], context
    )

    _, payload, _ = transport.requests[-1]
    row = json.loads(payload["messages"][1]["content"])
    assert row["memory_neighbours"] == [
        {"merchant_identity": "UNKNOWN TRAINS", "category": "Traveling"}
    ]
    assert "Prefer NONE for private transfers." in payload["messages"][0]["content"]


def test_ollama_parses_category_none_and_invalid_responses():
    transport = _Transport(
        chat=[
            _chat_reply("Train ticket.", "Traveling", 0.9, ["Apple Cloud", "Rent"]),
            _chat_reply("No merchant context.", "NONE", 0.3),
            {"message": {"content": "{not json"}},
            _chat_reply("Parent row.", "Living expenses", 0.8),
        ]
    )
    rows = [_categorized(f"tx{index}", merchant=f"SHOP {index}") for index in range(4)]

    category, none, bad_json, off_leaf = OllamaSuggester(_settings(), transport=transport).suggest(
        rows, _context()
    )

    assert (category.category, category.confidence) == ("Traveling", 0.9)
    assert category.alternatives == ("Apple Cloud",)
    assert category.evidence == "Train ticket."
    assert category.source == "gemma4:12b"
    assert category.failure is None
    assert (none.category, none.failure, none.evidence) == (None, None, "No merchant context.")
    assert bad_json.failure == "invalid_response"
    assert "tx2" in bad_json.evidence
    assert off_leaf.failure == "invalid_response"
    assert "Living expenses" in off_leaf.evidence


def test_ollama_uses_installed_fallback_when_configured_model_is_missing():
    transport = _Transport(
        tags=["gemma4:e4b"], chat=[_chat_reply("Train ticket.", "Traveling", 0.9)]
    )

    (suggestion,) = OllamaSuggester(_settings(), transport=transport).suggest(
        [_categorized("tx1")], _context()
    )

    assert transport.requests[0][0] == "http://localhost:11434/api/tags"
    assert transport.requests[0][2] == 10.0
    assert transport.requests[-1][1]["model"] == "gemma4:e4b"
    assert suggestion.source == "gemma4:e4b"


def test_ollama_without_installed_model_fails_every_row_as_provider_failure():
    transport = _Transport(tags=["llama3:8b"], chat=[])

    suggestions = OllamaSuggester(_settings(), transport=transport).suggest(
        [_categorized("tx1"), _categorized("tx2")], _context()
    )

    assert [suggestion.failure for suggestion in suggestions] == [
        "provider_failure",
        "provider_failure",
    ]
    assert "neither 'gemma4:12b' nor fallback 'gemma4:e4b'" in suggestions[0].evidence
    assert len(transport.requests) == 1


def test_ollama_unreachable_fails_rows_as_provider_failure():
    transport = _Transport(tags=OSError("connection refused"), chat=[])

    (suggestion,) = OllamaSuggester(_settings(), transport=transport).suggest(
        [_categorized("tx1")], _context()
    )

    assert suggestion.failure == "provider_failure"
    assert "Ollama is unavailable at http://localhost:11434" in suggestion.evidence


def test_ollama_primary_timeout_retries_fallback_model_for_same_row():
    transport = _Transport(
        tags=["gemma4:12b", "gemma4:e4b"],
        chat=[TimeoutError("timed out"), _chat_reply("Train ticket.", "Traveling", 0.9)],
    )

    (suggestion,) = OllamaSuggester(_settings(), transport=transport).suggest(
        [_categorized("tx1")], _context()
    )

    assert [request[1]["model"] for request in transport.requests[1:]] == [
        "gemma4:12b",
        "gemma4:e4b",
    ]
    assert suggestion.category == "Traveling"
    assert suggestion.source == "gemma4:e4b"


def test_ollama_call_timeout_on_last_model_is_a_provider_failure():
    transport = _Transport(tags=["gemma4:e4b"], chat=[TimeoutError("timed out")])

    (suggestion,) = OllamaSuggester(_settings(), transport=transport).suggest(
        [_categorized("tx1")], _context()
    )

    assert suggestion.failure == "provider_failure"
    assert "timed out" in suggestion.evidence


def test_category_suggestion_updates_unmatched_review_row():
    suggester = FakeSuggester(
        {
            "UNKNOWN TRAVEL": ScriptedVote(
                "Traveling", 0.68, "Travel merchant.", alternatives=("Apple Cloud",)
            )
        }
    )

    categorized, diagnostics = apply_suggestions(
        [_categorized("tx1", merchant="UNKNOWN TRAVEL")], _config(), suggester, _context()
    )

    result = categorized[0]
    assert result.suggested_category == "Traveling"
    assert result.categorization_method == "local_llm_gemma"
    assert result.confidence == 0.68
    assert result.votes == (Vote(category="Traveling", confidence=0.68, source="fake"),)
    assert result.authority is Authority.review
    assert result.authority_reason == "1 of 2 required model votes agree."
    assert "Travel merchant." in result.reason
    assert "Alternatives: Apple Cloud." in result.reason
    assert diagnostics.eligible_count == 1
    assert diagnostics.attempted_count == 1
    assert diagnostics.existing_leaf_suggestions == 1
    assert diagnostics.active_model == "fake"
    assert diagnostics.warnings == ()


def test_none_answer_keeps_row_review_required_without_category():
    categorized, diagnostics = apply_suggestions(
        [_categorized("tx1", merchant="UNKNOWN SHOP")],
        _config(),
        FakeSuggester({"UNKNOWN SHOP": ScriptedVote(None, 0.2, "Insufficient merchant context.")}),
        _context(),
    )

    result = categorized[0]
    assert result.suggested_category is None
    assert result.categorization_method == "local_llm_gemma_no_suggestion"
    assert result.authority is Authority.review
    assert result.authority_reason == "No category suggested."
    assert "Insufficient merchant context." in result.reason
    assert diagnostics.no_suggestion_count == 1


def test_low_confidence_category_keeps_original_row_and_warns():
    original = _categorized("tx1", merchant="AMBIGUOUS SHOP")

    categorized, diagnostics = apply_suggestions(
        [original],
        _config(),
        FakeSuggester({"AMBIGUOUS SHOP": ScriptedVote("Traveling", 0.40, "Weak travel signal.")}),
        _context(),
    )

    assert categorized == [original]
    assert diagnostics.low_confidence_response_count == 1
    assert "below the review threshold 0.60" in diagnostics.warnings[0]


def test_invalid_and_provider_failures_keep_original_rows_and_are_counted():
    rows = [_categorized("tx-bad", merchant="SHOP A"), _categorized("tx-down", merchant="SHOP B")]
    transport = _Transport(chat=[{"message": {"content": "{not json"}}, OSError("reset")])
    settings = _settings(fallback_model="")

    categorized, diagnostics = apply_suggestions(
        rows, _config(), OllamaSuggester(settings, transport=transport), _context()
    )

    assert categorized == rows
    assert diagnostics.attempted_count == 1
    assert diagnostics.invalid_response_count == 1
    assert diagnostics.provider_failure_count == 1
    assert len(diagnostics.warnings) == 2


def test_fallback_model_answers_are_reported_as_a_warning():
    transport = _Transport(tags=["gemma4:e4b"], chat=[_chat_reply("Train.", "Traveling", 0.9)])

    _, diagnostics = apply_suggestions(
        [_categorized("tx1")],
        _config(),
        OllamaSuggester(_settings(), transport=transport),
        _context(),
    )

    assert diagnostics.active_model == "gemma4:e4b"
    assert diagnostics.warnings == (
        "Configured local LLM model 'gemma4:12b' was unavailable; used fallback 'gemma4:e4b'.",
    )


def test_fallback_warning_names_the_consensus_voter_that_was_unavailable():
    settings = LocalLLMSettings()
    transport = _Transport(
        tags=["gemma4:26b", "qwen3:14b"],
        chat=[_chat_reply("Train.", "Traveling", 0.9), _chat_reply("Rail.", "Traveling", 0.8)],
    )

    _, diagnostics = apply_suggestions(
        [_categorized("tx1")],
        replace(_config(), local_llm=settings),
        local_consensus(settings, transport=transport),
        _context(),
    )

    assert diagnostics.warnings == (
        "Configured local LLM model 'gemma4:12b' was unavailable; used fallback 'qwen3:14b'.",
    )


def test_fallback_warning_survives_mixed_primary_and_fallback_answers():
    transport = _Transport(
        tags=["gemma4:12b", "gemma4:e4b"],
        chat=[
            _chat_reply("Train.", "Traveling", 0.9),
            TimeoutError("timed out"),
            _chat_reply("Cloud.", "Apple Cloud", 0.9),
        ],
    )

    _, diagnostics = apply_suggestions(
        [_categorized("tx1", merchant="SHOP A"), _categorized("tx2", merchant="SHOP B")],
        _config(),
        OllamaSuggester(_settings(), transport=transport),
        _context(),
    )

    assert diagnostics.active_model == "gemma4:12b"
    assert "used fallback 'gemma4:e4b'" in diagnostics.warnings[0]


def test_memory_neighbours_are_nearest_identities_only():
    context = _context(
        memory_examples=(("NETTO 123", "Groceries"), ("NETTO", "Groceries"), ("ZZZ BAR", "Bar"))
    )

    assert context.memory_neighbours("NETTO 12") == (
        ("NETTO 123", "Groceries"),
        ("NETTO", "Groceries"),
    )
    assert context.memory_neighbours("UNRELATED MERCHANT") == ()


def test_suggester_runs_on_low_confidence_rule_and_recurring_review_rows():
    rule = _categorized(
        "tx-rule",
        merchant="UNKNOWN TRAVEL",
        suggested_category="Apple Cloud",
        confidence=0.7,
        method="rule",
        reason="Keyword rule match.",
    )
    recurring = _categorized(
        "tx-recurring",
        merchant="UNKNOWN CLOUD",
        suggested_category="Traveling",
        confidence=0.8,
        method="recurring",
        reason="Recurring amount/date rule match.",
    )
    suggester = FakeSuggester(
        {
            "UNKNOWN TRAVEL": ScriptedVote("Traveling", 0.66, "Travel merchant."),
            "UNKNOWN CLOUD": ScriptedVote("Apple Cloud", 0.64, "Cloud subscription."),
        }
    )

    categorized, _ = apply_suggestions([rule, recurring], _config(), suggester, _context())

    assert [item.suggested_category for item in categorized] == ["Traveling", "Apple Cloud"]
    assert "Original rule: Apple Cloud, confidence 0.70" in categorized[0].reason
    assert "Original recurring: Traveling, confidence 0.80" in categorized[1].reason


def test_suggestion_reaches_auto_when_policy_agreement_is_met():
    config = replace(_config(), trust_policy=replace(_config().trust_policy, min_agreement=1))

    categorized, _ = apply_suggestions(
        [_categorized("tx1", merchant="UNKNOWN TRAVEL")],
        config,
        FakeSuggester({"UNKNOWN TRAVEL": ScriptedVote("Traveling", 0.9, "Travel merchant.")}),
        _context(),
    )

    assert categorized[0].authority is Authority.auto
    assert categorized[0].authority_reason == "1 model votes agree."


def test_consensus_of_two_agreeing_voters_grants_auto():
    categorized, _ = apply_suggestions(
        [_categorized("tx1", merchant="UNKNOWN TRAVEL")],
        _config(),
        _consensus(
            {"UNKNOWN TRAVEL": ScriptedVote("Traveling", 0.9, "Train ticket.")},
            {"UNKNOWN TRAVEL": ScriptedVote("Traveling", 0.8, "Travel merchant.")},
        ),
        _context(),
    )

    assert categorized[0].suggested_category == "Traveling"
    assert categorized[0].votes == (
        Vote(category="Traveling", confidence=0.9, source="gemma4:26b"),
        Vote(category="Traveling", confidence=0.8, source="gemma4:12b"),
    )
    assert categorized[0].authority is Authority.auto
    assert categorized[0].authority_reason == "2 model votes agree."


def test_consensus_is_kept_when_any_voter_clears_the_review_threshold():
    categorized, diagnostics = apply_suggestions(
        [_categorized("tx1", merchant="UNKNOWN TRAVEL")],
        _config(),
        _consensus(
            {"UNKNOWN TRAVEL": ScriptedVote("Traveling", 0.5)},
            {"UNKNOWN TRAVEL": ScriptedVote("Traveling", 0.9)},
        ),
        _context(),
    )

    assert categorized[0].authority is Authority.auto
    assert diagnostics.low_confidence_response_count == 0


@pytest.mark.parametrize(
    ("primary", "second", "category", "reason"),
    [
        (
            ScriptedVote("Traveling", 0.9),
            ScriptedVote("Apple Cloud", 0.8),
            "Traveling",
            "Alternatives: Apple Cloud.",
        ),
        (ScriptedVote(None, 0.9), ScriptedVote("Apple Cloud", 0.8), "Apple Cloud", "Local model"),
        (ScriptedVote("Groceries", 0.9), ScriptedVote("Traveling", 0.8), "Traveling", "Local model"),
        (ScriptedVote("Groceries", 0.9), ScriptedVote("Groceries", 0.8), None, "answered NONE"),
    ],
)
def test_consensus_without_two_matching_leaf_votes_goes_to_review(
    primary, second, category, reason
):
    categorized, _ = apply_suggestions(
        [_categorized("tx1", merchant="UNKNOWN TRAVEL")],
        _config(),
        _consensus({"UNKNOWN TRAVEL": primary}, {"UNKNOWN TRAVEL": second}),
        _context(),
    )

    assert categorized[0].suggested_category == category
    assert reason in categorized[0].reason
    assert categorized[0].authority is Authority.review


def test_consensus_keeps_primary_vote_when_second_voter_skips_the_row():
    class _Silent:
        def suggest(self, rows, context):
            return []

    categorized, _ = apply_suggestions(
        [_categorized("tx1", merchant="UNKNOWN TRAVEL")],
        _config(),
        ConsensusSuggester(
            FakeSuggester({"UNKNOWN TRAVEL": ScriptedVote("Traveling", 0.9)}, source="gemma4:26b"),
            _Silent(),
        ),
        _context(),
    )

    assert categorized[0].votes == (
        Vote(category="Traveling", confidence=0.9, source="gemma4:26b"),
    )
    assert categorized[0].authority is Authority.review


@pytest.mark.parametrize(
    ("amount", "never_auto", "reason"),
    [
        ("-1000.01", frozenset(), "above the auto cap"),
        ("-42.50", frozenset({"Traveling"}), "never-auto"),
    ],
)
def test_agreeing_consensus_over_cap_or_never_auto_goes_to_review(amount, never_auto, reason):
    row = _categorized("tx1", merchant="UNKNOWN TRAVEL")
    row = replace(row, transaction=replace(row.transaction, amount=Decimal(amount)))
    config = replace(
        _config(), trust_policy=replace(_config().trust_policy, never_auto_categories=never_auto)
    )

    categorized, _ = apply_suggestions(
        [row],
        config,
        _consensus(
            {"UNKNOWN TRAVEL": ScriptedVote("Traveling", 0.9)},
            {"UNKNOWN TRAVEL": ScriptedVote("Traveling", 0.8)},
        ),
        _context(),
    )

    assert categorized[0].authority is Authority.review
    assert reason in categorized[0].authority_reason


def test_consensus_counts_only_answering_voters():
    categorized, _ = apply_suggestions(
        [_categorized("tx1", merchant="UNKNOWN TRAVEL")],
        _config(),
        ConsensusSuggester(
            OllamaSuggester(_settings(), transport=_Transport(chat=[], tags=[])),
            FakeSuggester({"UNKNOWN TRAVEL": ScriptedVote("Traveling", 0.9)}, source="gemma4:12b"),
        ),
        _context(),
    )

    assert categorized[0].votes == (
        Vote(category="Traveling", confidence=0.9, source="gemma4:12b"),
    )
    assert categorized[0].authority is Authority.review
    assert categorized[0].authority_reason == "1 of 2 required model votes agree."


def test_default_consensus_asks_primary_then_second_local_model():
    transport = _Transport(
        tags=["gemma4:26b", "gemma4:12b", "qwen3:14b"],
        chat=[_chat_reply("Train.", "Traveling", 0.9), _chat_reply("Rail.", "Traveling", 0.8)],
    )

    (suggestion,) = local_consensus(LocalLLMSettings(), transport=transport).suggest(
        [_categorized("tx1")], _context()
    )

    assert [payload["model"] for _, payload, _ in transport.requests if payload] == [
        "gemma4:26b",
        "gemma4:12b",
    ]
    assert suggestion.votes == (
        Vote(category="Traveling", confidence=0.9, source="gemma4:26b"),
        Vote(category="Traveling", confidence=0.8, source="gemma4:12b"),
    )


def test_vote_source_is_the_model_that_answered():
    transport = _Transport(
        tags=["gemma4:12b", "gemma4:e4b"],
        chat=[TimeoutError("timed out"), _chat_reply("Train ticket.", "Traveling", 0.9)],
    )

    categorized, _ = apply_suggestions(
        [_categorized("tx1")],
        _config(),
        OllamaSuggester(_settings(), transport=transport),
        _context(),
    )

    assert categorized[0].votes == (
        Vote(category="Traveling", confidence=0.9, source="gemma4:e4b"),
    )


def test_suggester_skips_confident_deterministic_rows_held_for_review_by_policy():
    rows = [
        _categorized(
            "tx-rent",
            suggested_category="Apple Cloud",
            confidence=0.95,
            method="rule",
            authority=Authority.review,
        )
    ]
    suggester = FakeSuggester({})

    categorized, diagnostics = apply_suggestions(rows, _config(), suggester, _context())

    assert categorized == rows
    assert diagnostics.eligible_count == 0
    assert suggester.calls[0][0] == ()


def test_suggester_skips_authoritative_matches_and_proxy_split_lines():
    rows = [
        _categorized(
            "tx-rule",
            suggested_category="Apple Cloud",
            confidence=0.95,
            method="rule",
            authority=Authority.auto,
        ),
        _categorized(
            "tx-review",
            suggested_category="Traveling",
            method="monthly_review_decision",
            authority=Authority.auto,
        ),
        _categorized(
            "tx-memory",
            suggested_category="Apple Cloud",
            method="category_memory",
            authority=Authority.auto,
        ),
        _categorized(
            "tx-proxy",
            suggested_category="Traveling",
            method="proxy_split_allocation",
            authority=Authority.auto,
        ),
    ]
    suggester = FakeSuggester({})

    categorized, diagnostics = apply_suggestions(rows, _config(), suggester, _context())

    assert categorized == rows
    assert diagnostics.eligible_count == 0
    assert suggester.calls[0][0] == ()


def _consensus(primary_votes, second_votes) -> ConsensusSuggester:
    return ConsensusSuggester(
        FakeSuggester(primary_votes, source="gemma4:26b"),
        FakeSuggester(second_votes, source="gemma4:12b"),
    )


def _settings(**overrides) -> LocalLLMSettings:
    return LocalLLMSettings(**{"model": "gemma4:12b", "fallback_model": "gemma4:e4b", **overrides})


def _context(**overrides) -> SuggesterContext:
    return SuggesterContext(leaf_glossary=GLOSSARY, **overrides)


def _chat_reply(reason, category, confidence, alternatives=()):
    return {
        "message": {
            "content": json.dumps(
                {
                    "reason": reason,
                    "category": category,
                    "confidence": confidence,
                    "alternatives": list(alternatives),
                }
            )
        }
    }


class _Transport:
    """Stub HTTP transport: answers /api/tags and scripted /api/chat replies."""

    def __init__(self, chat, tags=("gemma4:12b",)):
        self.tags = tags
        self.chat = list(chat)
        self.requests = []

    def __call__(self, url, payload, timeout):
        self.requests.append((url, payload, timeout))
        if url.endswith("/api/tags"):
            if isinstance(self.tags, Exception):
                raise self.tags
            return {"models": [{"name": name} for name in self.tags]}
        reply = self.chat.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def _config() -> AppConfig:
    return AppConfig(
        sheet_name="Net worth",
        tracker_currency="DKK",
        category_column=2,
        year_header_row=2,
        month_header_row=3,
        statement_currency="DKK",
        review_threshold=0.60,
        reject_threshold=0.60,
        overwrite_fixed_rows=False,
        highlight_auto_filled_cells=False,
        categories=("Apple Cloud", "Traveling"),
        aliases={},
        historical_mappings={},
        rules=(),
        fixed_rows=frozenset(),
        local_llm=_settings(),
        category_registry=CategoryRegistry(
            leaf_categories=("Apple Cloud", "Traveling"),
            parent_categories=("Living expenses", "Income (net)"),
            category_type_by_label={
                "Apple Cloud": "leaf",
                "Traveling": "leaf",
                "Living expenses": "parent",
                "Income (net)": "derived",
            },
        ),
    )


def _categorized(
    transaction_id: str,
    description: str = "UNKNOWN SHOP",
    merchant: str | None = None,
    suggested_category: str | None = None,
    confidence: float = 0.0,
    method: str = "unmatched",
    authority: Authority = Authority.review,
    reason: str = "No historical or keyword rule matched.",
) -> CategorizedTransaction:
    return CategorizedTransaction(
        transaction=Transaction(
            transaction_id=transaction_id,
            date=date(2026, 4, 1),
            interest_date=None,
            description=description,
            amount=Decimal("-42.50"),
            currency="DKK",
            direction="expense",
            merchant=merchant,
        ),
        suggested_category=suggested_category,
        confidence=confidence,
        categorization_method=method,
        authority=authority,
        reason=reason,
    )
