from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import replace
from urllib.error import URLError
from urllib.request import Request, urlopen

from .config import AppConfig, LocalLLMSettings
from .models import CategorizedTransaction, LocalLLMDiagnostics, Vote
from .suggester import (
    INVALID_RESPONSE,
    PROVIDER_FAILURE,
    Suggester,
    SuggesterContext,
    Suggestion,
    row_merchant_identity,
)
from .trust_policy import stamp_authority

NONE_CATEGORY = "NONE"
TAGS_TIMEOUT_SECONDS = 10.0
SYSTEM_PROMPT = (
    "You categorise one personal bank transaction into one leaf category of a "
    "monthly wealth tracker. Answer NONE when no leaf clearly fits. Write the "
    "reason first, then the category."
)

Transport = Callable[[str, dict | None, float], dict]
_PROVIDER_ERRORS = (OSError, TimeoutError, URLError, json.JSONDecodeError)


def http_json_transport(url: str, payload: dict | None, timeout: float) -> dict:
    """POST `payload` as JSON (GET when None) and decode the JSON reply."""
    request = Request(
        url,
        data=None if payload is None else json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="GET" if payload is None else "POST",
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class OllamaSuggester:
    def __init__(self, settings: LocalLLMSettings, transport: Transport = http_json_transport):
        self.settings = settings
        self.transport = transport

    def suggest(
        self, rows: Sequence[CategorizedTransaction], context: SuggesterContext
    ) -> list[Suggestion]:
        if not rows:
            return []
        model, unavailable = self._installed_model()
        if model is None:
            return [_failure(item, PROVIDER_FAILURE, unavailable, "ollama") for item in rows]
        system_prompt = _system_prompt(context)
        schema = _response_schema(tuple(context.leaf_glossary))
        return [self._suggest_row(item, model, system_prompt, schema, context) for item in rows]

    def _installed_model(self) -> tuple[str | None, str]:
        settings = self.settings
        try:
            payload = self.transport(f"{settings.endpoint}/api/tags", None, TAGS_TIMEOUT_SECONDS)
        except _PROVIDER_ERRORS as exc:
            return None, f"Ollama is unavailable at {settings.endpoint}: {exc}"
        names = {
            str(model.get("name", ""))
            for model in payload.get("models", [])
            if isinstance(model, dict)
        }
        for model in (settings.model, settings.fallback_model):
            if model and model in names:
                return model, ""
        return None, (
            f"Ollama is available at {settings.endpoint}, but neither "
            f"{settings.model!r} nor fallback {settings.fallback_model!r} is installed."
        )

    def _suggest_row(
        self,
        item: CategorizedTransaction,
        model: str,
        system_prompt: str,
        schema: dict,
        context: SuggesterContext,
    ) -> Suggestion:
        transaction_id = item.transaction.transaction_id
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": _row_prompt(item, context, self.settings.include_raw_description),
            },
        ]
        try:
            model, payload = self._chat_with_fallback(model, messages, schema)
        except _PROVIDER_ERRORS as exc:
            return _failure(
                item,
                PROVIDER_FAILURE,
                f"Local LLM provider call for {transaction_id} failed: {exc}",
                model,
            )
        try:
            return _parse_reply(item, payload, tuple(context.leaf_glossary), model)
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            return _failure(
                item,
                INVALID_RESPONSE,
                f"Local LLM response for {transaction_id} was ignored: {exc}",
                model,
            )

    def _chat_with_fallback(self, model: str, messages: list, schema: dict) -> tuple[str, dict]:
        try:
            return model, self._chat(model, messages, schema)
        except _PROVIDER_ERRORS:
            fallback = self.settings.fallback_model
            if not fallback or model == fallback:
                raise
            return fallback, self._chat(fallback, messages, schema)

    def _chat(self, model: str, messages: list, schema: dict) -> dict:
        settings = self.settings
        return self.transport(
            f"{settings.endpoint}/api/chat",
            {
                "model": model,
                "messages": messages,
                "stream": False,
                "think": False,
                "format": schema,
                "keep_alive": settings.keep_alive,
                "options": {"temperature": 0},
            },
            settings.timeout_seconds,
        )


def _system_prompt(context: SuggesterContext) -> str:
    glossary = "\n".join(
        f"- {leaf}: {description}" if description else f"- {leaf}"
        for leaf, description in context.leaf_glossary.items()
    )
    sections = [SYSTEM_PROMPT, f"Leaf categories:\n{glossary}"]
    if context.guidance_aliases:
        aliases = "\n".join(
            f"- {pattern} -> {leaf}" for pattern, leaf in context.guidance_aliases.items()
        )
        sections.append(f"Operator guidance:\n{aliases}")
    if context.reviewed_policy:
        sections.append(f"Reviewed policy:\n{context.reviewed_policy}")
    return "\n\n".join(sections)


def _response_schema(leaves: tuple[str, ...]) -> dict:
    return {
        "type": "object",
        "properties": {
            "reason": {"type": "string"},
            "category": {"type": "string", "enum": [*leaves, NONE_CATEGORY]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "alternatives": {"type": "array", "items": {"type": "string", "enum": list(leaves)}},
        },
        "required": ["reason", "category", "confidence", "alternatives"],
    }


def _row_prompt(
    item: CategorizedTransaction, context: SuggesterContext, include_raw_description: bool
) -> str:
    transaction = item.transaction
    merchant_identity = row_merchant_identity(item)
    row: dict = {
        "merchant_identity": merchant_identity,
        "amount": str(transaction.amount),
        "date": transaction.date.isoformat(),
        "direction": transaction.direction,
        "memory_neighbours": [
            {"merchant_identity": identity, "category": category}
            for identity, category in context.memory_neighbours(merchant_identity)
        ],
    }
    if item.suggested_category and item.categorization_method in {"rule", "recurring"}:
        row["current_suggestion"] = {
            "category": item.suggested_category,
            "method": item.categorization_method,
            "confidence": item.confidence,
        }
    if include_raw_description:
        row["raw_description"] = transaction.description
    return json.dumps(row, ensure_ascii=False)


def _parse_reply(
    item: CategorizedTransaction, payload: dict, leaves: tuple[str, ...], model: str
) -> Suggestion:
    reply = json.loads(payload["message"]["content"])
    if not isinstance(reply, dict):
        raise ValueError("structured response must be a JSON object")
    reason = str(reply.get("reason", "")).strip()
    if not reason:
        raise ValueError("response reason is required")
    category = str(reply.get("category", "")).strip()
    if category != NONE_CATEGORY and category not in leaves:
        raise ValueError(f"category {category!r} is outside the allowed YAML leaf categories")
    confidence = float(reply["confidence"]) if "confidence" in reply else -1.0
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("response confidence must be between 0.0 and 1.0")
    alternatives = tuple(
        alternative
        for alternative in reply.get("alternatives") or ()
        if alternative in leaves and alternative != category
    )
    return Suggestion(
        transaction_id=item.transaction.transaction_id,
        category=None if category == NONE_CATEGORY else category,
        confidence=confidence,
        alternatives=alternatives,
        evidence=reason,
        source=model,
    )


def _failure(item: CategorizedTransaction, failure: str, evidence: str, source: str) -> Suggestion:
    return Suggestion(
        transaction_id=item.transaction.transaction_id,
        category=None,
        confidence=0.0,
        alternatives=(),
        evidence=evidence,
        source=source,
        failure=failure,
    )


def disabled_diagnostics(config: LocalLLMSettings) -> LocalLLMDiagnostics:
    return _diagnostics(config, enabled=False)


def apply_suggestions(
    categorized: list[CategorizedTransaction],
    config: AppConfig,
    suggester: Suggester,
    context: SuggesterContext,
) -> tuple[list[CategorizedTransaction], LocalLLMDiagnostics]:
    settings = config.local_llm
    eligible_indexes = _eligible_indexes(categorized, config.trust_policy.min_confidence)
    suggestions = suggester.suggest([categorized[index] for index in eligible_indexes], context)
    by_transaction_id = {suggestion.transaction_id: suggestion for suggestion in suggestions}

    updated = list(categorized)
    warnings: list[str] = []
    counts = dict.fromkeys(
        ("attempted", "category", "none", "low_confidence", INVALID_RESPONSE, PROVIDER_FAILURE),
        0,
    )
    active_model = None
    for index in eligible_indexes:
        item = updated[index]
        suggestion = by_transaction_id.get(item.transaction.transaction_id)
        if suggestion is None:
            continue
        if suggestion.failure:
            counts[suggestion.failure] += 1
            if suggestion.failure == INVALID_RESPONSE:
                counts["attempted"] += 1
            if suggestion.evidence not in warnings:
                warnings.append(suggestion.evidence)
            continue
        counts["attempted"] += 1
        active_model = active_model or suggestion.source
        vote = Vote(suggestion.category, suggestion.confidence, suggestion.source)
        if suggestion.category is None:
            counts["none"] += 1
            updated[index] = replace(
                item,
                votes=(vote,),
                confidence=suggestion.confidence,
                categorization_method="local_llm_gemma_no_suggestion",
                reason=(
                    f"Local model answered NONE: {suggestion.evidence} "
                    f"{_original_classification(item)}"
                ),
            )
        elif suggestion.confidence < config.review_threshold:
            counts["low_confidence"] += 1
            warnings.append(
                "Local LLM response for "
                f"{item.transaction.transaction_id} was ignored: confidence "
                f"{suggestion.confidence:.2f} is below the review threshold "
                f"{config.review_threshold:.2f}."
            )
            continue
        else:
            counts["category"] += 1
            updated[index] = replace(
                item,
                votes=(vote,),
                suggested_category=suggestion.category,
                confidence=suggestion.confidence,
                categorization_method="local_llm_gemma",
                reason=_suggestion_reason(suggestion, item),
            )
        updated[index] = stamp_authority(updated[index], config)

    if active_model and active_model != settings.model and active_model == settings.fallback_model:
        warnings.insert(
            0,
            f"Configured local LLM model {settings.model!r} was unavailable; "
            f"used fallback {active_model!r}.",
        )
    diagnostics = _diagnostics(
        settings,
        enabled=True,
        active_model=active_model,
        eligible_count=len(eligible_indexes),
        provider_failure_count=counts[PROVIDER_FAILURE],
        warnings=tuple(warnings),
    )
    return updated, replace(
        diagnostics,
        attempted_count=counts["attempted"],
        existing_leaf_suggestions=counts["category"],
        no_suggestion_count=counts["none"],
        low_confidence_response_count=counts["low_confidence"],
        invalid_response_count=counts[INVALID_RESPONSE],
    )


def _original_classification(item: CategorizedTransaction) -> str:
    return (
        f"Original {item.categorization_method}: "
        f"{item.suggested_category or 'Unmatched'}, "
        f"confidence {item.confidence:.2f}, {item.reason}"
    )


def _eligible_indexes(
    categorized: list[CategorizedTransaction], min_confidence: float
) -> list[int]:
    return [
        index
        for index, item in enumerate(categorized)
        if item.categorization_method in {"unmatched", "rule", "recurring"}
        and item.confidence < min_confidence
    ]


def _suggestion_reason(suggestion: Suggestion, item: CategorizedTransaction) -> str:
    alternatives = (
        f" Alternatives: {', '.join(suggestion.alternatives)}." if suggestion.alternatives else ""
    )
    return (
        f"Local model suggested {suggestion.category}: {suggestion.evidence}{alternatives} "
        f"{_original_classification(item)}"
    )


def _diagnostics(
    config: LocalLLMSettings,
    enabled: bool,
    active_model: str | None = None,
    eligible_count: int = 0,
    provider_failure_count: int = 0,
    warnings: tuple[str, ...] = (),
) -> LocalLLMDiagnostics:
    return LocalLLMDiagnostics(
        enabled=enabled,
        provider=config.provider,
        endpoint=config.endpoint,
        model=config.model,
        fallback_model=config.fallback_model,
        active_model=active_model,
        eligible_count=eligible_count,
        provider_failure_count=provider_failure_count,
        warnings=warnings,
    )
