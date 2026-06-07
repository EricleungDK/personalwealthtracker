import json
from datetime import date
from decimal import Decimal

from personal_wealth_tracker.config import AppConfig, CategoryRegistry
from personal_wealth_tracker.local_llm import (
    OllamaLocalLLMClient,
    apply_local_llm_suggestions,
    build_local_llm_prompt,
)
from personal_wealth_tracker.models import (
    CategorizedTransaction,
    LocalLLMAvailability,
    Transaction,
)


def test_prompt_uses_minimized_transaction_context_and_yaml_leaf_categories():
    item = _categorized(
        "tx1",
        description="RAW NORDEA CARD PURCHASE SECRET CONTEXT",
        merchant="UNKNOWN SHOP",
    )

    prompt = build_local_llm_prompt(
        item,
        allowed_categories=("Apple Cloud", "Traveling"),
        config=_config().local_llm,
    )

    assert "UNKNOWN SHOP" in prompt
    assert "42.50" in prompt
    assert "2026-04-01" in prompt
    assert "expense" in prompt
    assert "Apple Cloud" in prompt
    assert "Traveling" in prompt
    assert "RAW NORDEA" not in prompt
    assert "SECRET CONTEXT" not in prompt


def test_prompt_does_not_require_model_to_echo_transaction_id():
    item = _categorized("stable-content-v2:abc123:001", merchant="UNKNOWN SHOP")

    prompt = build_local_llm_prompt(
        item,
        allowed_categories=("Apple Cloud", "Traveling"),
        config=_config().local_llm,
    )

    payload = json.loads(prompt)
    assert payload["transaction"]["transaction_id"] == "stable-content-v2:abc123:001"
    assert "transaction_id" not in payload["response_contract"]


def test_valid_existing_leaf_suggestion_updates_unmatched_review_row():
    client = _FakeClient(
        '{"transaction_id":"tx1","status":"category","suggested_category":"Traveling",'
        '"confidence":0.68,"rationale":"Merchant looks travel related."}'
    )

    categorized, diagnostics = apply_local_llm_suggestions(
        [_categorized("tx1", merchant="UNKNOWN TRAVEL")],
        _config(),
        client=client,
    )

    assert len(client.prompts) == 1
    result = categorized[0]
    assert result.suggested_category == "Traveling"
    assert result.categorization_method == "local_llm_gemma"
    assert result.confidence == 0.68
    assert result.review_required is True
    assert "Merchant looks travel related." in result.reason
    assert diagnostics.eligible_count == 1
    assert diagnostics.attempted_count == 1
    assert diagnostics.existing_leaf_suggestions == 1
    assert diagnostics.warnings == ()


def test_invalid_leaf_suggestion_keeps_unmatched_review_row_and_warns():
    original = _categorized("tx1", merchant="UNKNOWN SHOP")
    client = _FakeClient(
        '{"transaction_id":"tx1","status":"category","suggested_category":"Living expenses",'
        '"confidence":0.72,"rationale":"Parent row is invalid."}'
    )

    categorized, diagnostics = apply_local_llm_suggestions(
        [original],
        _config(),
        client=client,
    )

    assert categorized == [original]
    assert diagnostics.eligible_count == 1
    assert diagnostics.attempted_count == 1
    assert diagnostics.invalid_response_count == 1
    assert "outside the allowed YAML leaf categories" in diagnostics.warnings[0]


def test_invalid_json_and_missing_fields_keep_original_review_rows_and_warn():
    first = _categorized("tx-invalid-json", merchant="UNKNOWN 1")
    second = _categorized("tx-missing-fields", merchant="UNKNOWN 2")
    client = _QueueClient(
        [
            "{not json",
            '{"transaction_id":"tx-missing-fields","status":"category"}',
        ]
    )

    categorized, diagnostics = apply_local_llm_suggestions(
        [first, second],
        _config(),
        client=client,
    )

    assert categorized == [first, second]
    assert diagnostics.attempted_count == 2
    assert diagnostics.invalid_response_count == 2
    assert len(diagnostics.warnings) == 2


def test_local_llm_runs_on_low_confidence_rule_and_recurring_review_rows():
    client = _QueueClient(
        [
            '{"transaction_id":"tx-rule","status":"category","suggested_category":"Traveling",'
            '"confidence":0.66,"rationale":"Travel merchant."}',
            (
                '{"transaction_id":"tx-recurring","status":"category",'
                '"suggested_category":"Apple Cloud","confidence":0.64,'
                '"rationale":"Cloud subscription."}'
            ),
        ]
    )
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

    categorized, diagnostics = apply_local_llm_suggestions(
        [rule, recurring],
        _config(),
        client=client,
    )

    assert [item.suggested_category for item in categorized] == ["Traveling", "Apple Cloud"]
    assert [item.categorization_method for item in categorized] == [
        "local_llm_gemma",
        "local_llm_gemma",
    ]
    assert all(item.review_required for item in categorized)
    assert "Original rule: Apple Cloud, confidence 0.70" in categorized[0].reason
    assert "Original recurring: Traveling, confidence 0.80" in categorized[1].reason
    assert diagnostics.eligible_count == 2
    assert diagnostics.attempted_count == 2
    assert diagnostics.existing_leaf_suggestions == 2


def test_local_llm_skips_authoritative_matches_and_proxy_split_lines():
    client = _QueueClient([])
    rows = [
        _categorized(
            "tx-rule",
            suggested_category="Apple Cloud",
            method="rule",
            review_required=False,
        ),
        _categorized(
            "tx-review",
            suggested_category="Traveling",
            method="monthly_review_decision",
            review_required=False,
        ),
        _categorized(
            "tx-memory",
            suggested_category="Apple Cloud",
            method="category_memory",
            review_required=False,
        ),
        _categorized(
            "tx-proxy",
            suggested_category="Traveling",
            method="proxy_split_allocation",
            review_required=False,
        ),
    ]

    categorized, diagnostics = apply_local_llm_suggestions(rows, _config(), client=client)

    assert categorized == rows
    assert diagnostics.eligible_count == 0
    assert diagnostics.attempted_count == 0
    assert client.prompts == []


def test_no_suggestion_keeps_transaction_review_required_without_category():
    client = _FakeClient(
        '{"transaction_id":"tx1","status":"no_suggestion",'
        '"confidence":0.2,"rationale":"Insufficient merchant context."}'
    )

    categorized, diagnostics = apply_local_llm_suggestions(
        [_categorized("tx1", merchant="UNKNOWN SHOP")],
        _config(),
        client=client,
    )

    result = categorized[0]
    assert result.suggested_category is None
    assert result.categorization_method == "local_llm_gemma_no_suggestion"
    assert result.confidence == 0.2
    assert result.review_required is True
    assert "Insufficient merchant context." in result.reason
    assert diagnostics.no_suggestion_count == 1


def test_new_leaf_candidate_is_a_review_hint_not_a_category():
    client = _FakeClient(
        '{"transaction_id":"tx1","status":"new_leaf_candidate",'
        '"new_leaf_candidate":"Pet Supplies","confidence":0.61,'
        '"rationale":"Merchant appears to need a missing pet category."}'
    )

    categorized, diagnostics = apply_local_llm_suggestions(
        [_categorized("tx1", merchant="PET SHOP")],
        _config(),
        client=client,
    )

    result = categorized[0]
    assert result.suggested_category is None
    assert result.categorization_method == "local_llm_gemma_new_leaf_candidate"
    assert result.confidence == 0.61
    assert result.review_required is True
    assert "Pet Supplies" in result.reason
    assert "missing pet category" in result.reason
    assert "Pet Supplies" not in _config().category_registry.leaf_categories
    assert diagnostics.new_leaf_candidate_count == 1


def test_provider_call_timeout_keeps_original_review_row_and_warns():
    original = _categorized("tx-timeout", merchant="UNKNOWN SHOP")
    client = _TimeoutClient()

    categorized, diagnostics = apply_local_llm_suggestions(
        [original],
        _config(),
        client=client,
    )

    assert categorized == [original]
    assert diagnostics.provider_failure_count == 1
    assert "timed out" in diagnostics.warnings[0]


def test_primary_call_timeout_retries_fallback_model_for_same_row():
    client = _FallbackAfterTimeoutClient(
        fallback_response=(
            '{"status":"category","suggested_category":"Traveling",'
            '"confidence":0.62,"rationale":"Fallback model found a travel hint."}'
        )
    )

    categorized, diagnostics = apply_local_llm_suggestions(
        [_categorized("tx1", merchant="UNKNOWN TRAVEL")],
        _config(),
        client=client,
    )

    assert client.models == ["gemma4:12b", "gemma4:e4b"]
    assert categorized[0].suggested_category == "Traveling"
    assert categorized[0].categorization_method == "local_llm_gemma"
    assert diagnostics.attempted_count == 2
    assert diagnostics.existing_leaf_suggestions == 1
    assert diagnostics.provider_failure_count == 0
    assert "using fallback 'gemma4:e4b'" in diagnostics.warnings[0]


def test_ollama_client_availability_uses_http_tags_and_fallback_model(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        return _HTTPResponse('{"models":[{"name":"gemma4:e4b"}]}')

    monkeypatch.setattr("personal_wealth_tracker.local_llm.urlopen", fake_urlopen)

    availability = OllamaLocalLLMClient().check_availability(_config().local_llm)

    assert captured == {"url": "http://localhost:11434/api/tags", "timeout": 60.0}
    assert availability.available is True
    assert availability.model == "gemma4:e4b"
    assert "fallback" in availability.warning


def test_ollama_client_generate_posts_to_http_api(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["timeout"] = timeout
        captured["payload"] = request.data.decode("utf-8")
        return _HTTPResponse('{"response":"{\\"status\\":\\"no_suggestion\\"}"}')

    monkeypatch.setattr("personal_wealth_tracker.local_llm.urlopen", fake_urlopen)

    response = OllamaLocalLLMClient().generate(
        _config().local_llm,
        model="gemma4:e4b",
        prompt="review prompt",
    )

    assert captured["url"] == "http://localhost:11434/api/generate"
    assert captured["method"] == "POST"
    assert captured["timeout"] == 60.0
    assert '"model": "gemma4:e4b"' in captured["payload"]
    assert '"stream": false' in captured["payload"]
    assert '"format": "json"' in captured["payload"]
    assert '"num_predict": 512' in captured["payload"]
    assert response == '{"status":"no_suggestion"}'


def _config() -> AppConfig:
    return AppConfig(
        sheet_name="Net worth",
        tracker_currency="DKK",
        category_column=2,
        year_header_row=2,
        month_header_row=3,
        statement_currency="DKK",
        auto_write_threshold=0.85,
        review_threshold=0.60,
        reject_threshold=0.60,
        overwrite_fixed_rows=False,
        highlight_auto_filled_cells=False,
        categories=("Apple Cloud", "Traveling"),
        aliases={},
        historical_mappings={},
        rules=(),
        fixed_rows=frozenset(),
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
    review_required: bool = True,
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
        review_required=review_required,
        reason=reason,
    )


class _FakeClient:
    def __init__(self, response: str):
        self.response = response
        self.prompts: list[str] = []

    def check_availability(self, config):
        return LocalLLMAvailability(available=True, model=config.model)

    def generate(self, config, model, prompt):
        self.prompts.append(prompt)
        return self.response


class _QueueClient:
    def __init__(self, responses: list[str]):
        self.responses = list(responses)
        self.prompts: list[str] = []

    def check_availability(self, config):
        return LocalLLMAvailability(available=True, model=config.model)

    def generate(self, config, model, prompt):
        self.prompts.append(prompt)
        if not self.responses:
            raise AssertionError("unexpected local LLM call")
        return self.responses.pop(0)


class _TimeoutClient:
    def check_availability(self, config):
        return LocalLLMAvailability(available=True, model=config.model)

    def generate(self, config, model, prompt):
        raise TimeoutError("timed out")


class _FallbackAfterTimeoutClient:
    def __init__(self, fallback_response: str):
        self.fallback_response = fallback_response
        self.models: list[str] = []

    def check_availability(self, config):
        return LocalLLMAvailability(available=True, model=config.model)

    def generate(self, config, model, prompt):
        self.models.append(model)
        if model == config.model:
            raise TimeoutError("timed out")
        return self.fallback_response


class _HTTPResponse:
    def __init__(self, body: str):
        self.body = body.encode("utf-8")

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False
