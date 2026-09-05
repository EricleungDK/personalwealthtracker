from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, replace
from urllib.error import URLError
from urllib.request import Request, urlopen

from .category_memory import normalize_merchant_identity
from .config import AppConfig, LocalLLMSettings
from .models import CategorizedTransaction, LocalLLMAvailability, LocalLLMDiagnostics


class OllamaLocalLLMClient:
    def check_availability(self, config: LocalLLMSettings) -> LocalLLMAvailability:
        request = Request(f"{config.endpoint}/api/tags", method="GET")
        try:
            with urlopen(request, timeout=config.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, TimeoutError, URLError, json.JSONDecodeError) as exc:
            return LocalLLMAvailability(
                available=False,
                model=None,
                warning=f"Ollama is unavailable at {config.endpoint}: {exc}",
            )

        names = {
            str(model.get("name", ""))
            for model in payload.get("models", [])
            if isinstance(model, dict)
        }
        if config.model in names:
            return LocalLLMAvailability(available=True, model=config.model)
        if config.fallback_model in names:
            return LocalLLMAvailability(
                available=True,
                model=config.fallback_model,
                warning=(
                    f"Configured local LLM model {config.model!r} was not found; "
                    f"using fallback {config.fallback_model!r}."
                ),
            )
        return LocalLLMAvailability(
            available=False,
            model=None,
            warning=(
                f"Ollama is available at {config.endpoint}, but neither "
                f"{config.model!r} nor fallback {config.fallback_model!r} is installed."
            ),
        )

    def generate(self, config: LocalLLMSettings, model: str, prompt: str) -> str:
        request = Request(
            f"{config.endpoint}/api/generate",
            data=json.dumps(
                {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0, "num_predict": 512},
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=config.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return str(payload.get("response", ""))


@dataclass(frozen=True)
class _ParsedSuggestion:
    status: str
    suggested_category: str | None
    new_leaf_candidate: str | None
    confidence: float
    rationale: str


def disabled_diagnostics(config: LocalLLMSettings) -> LocalLLMDiagnostics:
    return _diagnostics(config, enabled=False)


def build_local_llm_prompt(
    item: CategorizedTransaction,
    allowed_categories: tuple[str, ...],
    config: LocalLLMSettings,
    reviewed_policy: str = "",
) -> str:
    transaction = item.transaction
    prompt = {
        "task": "Suggest a review-only category for this personal tracker transaction.",
        "response_contract": {
            "status": "category | no_suggestion | new_leaf_candidate",
            "suggested_category": "Required only for status=category.",
            "confidence": "Number from 0.0 to 1.0.",
            "rationale": "Short explanation for manual review.",
        },
        "allowed_categories": list(allowed_categories),
        "transaction": {
            "transaction_id": transaction.transaction_id,
            "merchant_identity": normalize_merchant_identity(
                transaction.merchant or transaction.description
            ),
            "amount": str(transaction.amount),
            "date": transaction.date.isoformat(),
            "direction": transaction.direction,
        },
    }
    if item.suggested_category and item.categorization_method in {"rule", "recurring"}:
        prompt["current_suggestion"] = {
            "suggested_category": item.suggested_category,
            "method": item.categorization_method,
            "confidence": item.confidence,
            "reason": item.reason,
        }
    if reviewed_policy:
        prompt["reviewed_policy"] = reviewed_policy
    if config.include_raw_description:
        prompt["transaction"]["raw_description"] = transaction.description
    return json.dumps(prompt, ensure_ascii=False, sort_keys=True)


def apply_local_llm_suggestions(
    categorized: list[CategorizedTransaction],
    config: AppConfig,
    client: object | None = None,
    reviewed_policy: str = "",
) -> tuple[list[CategorizedTransaction], LocalLLMDiagnostics]:
    client = client or OllamaLocalLLMClient()
    settings = config.local_llm
    eligible_indexes = _eligible_indexes(categorized)
    availability = client.check_availability(settings)
    diagnostics = _diagnostics(
        settings,
        enabled=True,
        active_model=availability.model,
        eligible_count=len(eligible_indexes),
        provider_failure_count=0 if availability.available else 1,
        warnings=tuple(message for message in (availability.warning,) if message),
    )
    if not availability.available:
        return categorized, diagnostics

    updated = list(categorized)
    warnings = list(diagnostics.warnings)
    attempted_count = 0
    existing_leaf_suggestions = 0
    no_suggestion_count = 0
    new_leaf_candidate_count = 0
    low_confidence_response_count = 0
    invalid_response_count = 0
    provider_failure_count = diagnostics.provider_failure_count
    allowed_categories = _allowed_categories(config)
    allowed_category_set = set(allowed_categories)
    for index in eligible_indexes:
        item = updated[index]
        prompt = build_local_llm_prompt(
            item,
            allowed_categories,
            settings,
            reviewed_policy=reviewed_policy,
        )

        def generate_model(model: str) -> str:
            nonlocal attempted_count
            attempted_count += 1
            return client.generate(settings, model, prompt)

        try:
            raw_response = _generate_with_fallback(
                generate_model,
                settings,
                availability.model or settings.model,
                item.transaction.transaction_id,
                warnings,
            )
            parsed = _parse_response(
                raw_response,
                item.transaction.transaction_id,
                allowed_category_set,
            )
        except (OSError, TimeoutError, URLError) as exc:
            provider_failure_count += 1
            warnings.append(
                f"Local LLM provider call for {item.transaction.transaction_id} failed: {exc}"
            )
            continue
        except (json.JSONDecodeError, ValueError) as exc:
            invalid_response_count += 1
            warnings.append(
                f"Local LLM response for {item.transaction.transaction_id} was ignored: {exc}"
            )
            continue
        if _is_low_confidence_suggestion(parsed, config.review_threshold):
            low_confidence_response_count += 1
            warnings.append(
                "Local LLM response for "
                f"{item.transaction.transaction_id} was ignored: confidence "
                f"{parsed.confidence:.2f} is below the review threshold "
                f"{config.review_threshold:.2f}."
            )
            continue
        if parsed.status == "category":
            existing_leaf_suggestions += 1
            updated[index] = replace(
                item,
                suggested_category=parsed.suggested_category,
                confidence=parsed.confidence,
                categorization_method="local_llm_gemma",
                review_required=True,
                reason=_suggestion_reason(parsed, item),
            )
        elif parsed.status == "no_suggestion":
            no_suggestion_count += 1
            updated[index] = replace(
                item,
                confidence=parsed.confidence,
                categorization_method="local_llm_gemma_no_suggestion",
                review_required=True,
                reason=_no_suggestion_reason(parsed, item),
            )
        elif parsed.status == "new_leaf_candidate":
            new_leaf_candidate_count += 1
            updated[index] = replace(
                item,
                confidence=parsed.confidence,
                categorization_method="local_llm_gemma_new_leaf_candidate",
                review_required=True,
                reason=_new_leaf_candidate_reason(parsed, item),
            )

    diagnostics = replace(
        diagnostics,
        attempted_count=attempted_count,
        existing_leaf_suggestions=existing_leaf_suggestions,
        no_suggestion_count=no_suggestion_count,
        new_leaf_candidate_count=new_leaf_candidate_count,
        low_confidence_response_count=low_confidence_response_count,
        invalid_response_count=invalid_response_count,
        provider_failure_count=provider_failure_count,
        warnings=tuple(warnings),
    )
    return updated, diagnostics


def _generate_with_fallback(
    generate: Callable[[str], str],
    settings: LocalLLMSettings,
    active_model: str,
    transaction_id: str,
    warnings: list[str],
) -> str:
    try:
        return generate(active_model)
    except (OSError, TimeoutError, URLError) as exc:
        if active_model == settings.fallback_model or not settings.fallback_model:
            raise
        warnings.append(
            f"Local LLM primary model {active_model!r} failed for {transaction_id}: "
            f"{exc}; using fallback {settings.fallback_model!r}."
        )
        return generate(settings.fallback_model)


def _eligible_indexes(categorized: list[CategorizedTransaction]) -> list[int]:
    return [
        index
        for index, item in enumerate(categorized)
        if item.review_required and item.categorization_method in {"unmatched", "rule", "recurring"}
    ]


def _allowed_categories(config: AppConfig) -> tuple[str, ...]:
    if config.category_registry.leaf_categories:
        return config.category_registry.leaf_categories
    return config.categories


def _is_low_confidence_suggestion(parsed: _ParsedSuggestion, threshold: float) -> bool:
    return parsed.status in {"category", "new_leaf_candidate"} and parsed.confidence < threshold


def _parse_response(
    raw_response: str,
    transaction_id: str,
    allowed_categories: set[str],
) -> _ParsedSuggestion:
    payload = json.loads(raw_response)
    if not isinstance(payload, dict):
        raise ValueError("structured response must be a JSON object")
    response_transaction_id = str(payload.get("transaction_id", ""))
    if response_transaction_id and response_transaction_id != transaction_id:
        raise ValueError(
            f"response transaction_id {response_transaction_id!r} does not match {transaction_id!r}"
        )
    status = str(payload.get("status", "")).strip()
    confidence = _confidence(payload.get("confidence"))
    rationale = str(payload.get("rationale", payload.get("reason", ""))).strip()
    if not rationale:
        raise ValueError("response rationale is required")
    if status == "no_suggestion":
        return _ParsedSuggestion(
            status=status,
            suggested_category=None,
            new_leaf_candidate=None,
            confidence=confidence,
            rationale=rationale,
        )
    if status == "new_leaf_candidate":
        candidate = str(payload.get("new_leaf_candidate", "")).strip()
        if not candidate:
            raise ValueError("new_leaf_candidate response requires a new_leaf_candidate hint")
        return _ParsedSuggestion(
            status=status,
            suggested_category=None,
            new_leaf_candidate=candidate,
            confidence=confidence,
            rationale=rationale,
        )
    if status != "category":
        raise ValueError(f"unsupported local LLM status {status!r}")
    suggested_category = str(
        payload.get("suggested_category", payload.get("category", ""))
    ).strip()
    if suggested_category not in allowed_categories:
        raise ValueError(
            f"suggested category {suggested_category!r} is outside the allowed YAML leaf categories"
        )
    return _ParsedSuggestion(
        status=status,
        suggested_category=suggested_category,
        new_leaf_candidate=None,
        confidence=confidence,
        rationale=rationale,
    )


def _confidence(value) -> float:
    if value is None:
        raise ValueError("response confidence is required")
    confidence = float(value)
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("response confidence must be between 0.0 and 1.0")
    return confidence


def _suggestion_reason(parsed: _ParsedSuggestion, item: CategorizedTransaction) -> str:
    original = (
        f"Original {item.categorization_method}: "
        f"{item.suggested_category or 'Unmatched'}, "
        f"confidence {item.confidence:.2f}, {item.reason}"
    )
    return f"Local Gemma suggested {parsed.suggested_category}: {parsed.rationale} {original}"


def _no_suggestion_reason(parsed: _ParsedSuggestion, item: CategorizedTransaction) -> str:
    original = (
        f"Original {item.categorization_method}: "
        f"{item.suggested_category or 'Unmatched'}, "
        f"confidence {item.confidence:.2f}, {item.reason}"
    )
    return f"Local Gemma returned no_suggestion: {parsed.rationale} {original}"


def _new_leaf_candidate_reason(parsed: _ParsedSuggestion, item: CategorizedTransaction) -> str:
    original = (
        f"Original {item.categorization_method}: "
        f"{item.suggested_category or 'Unmatched'}, "
        f"confidence {item.confidence:.2f}, {item.reason}"
    )
    return (
        f"Local Gemma suggested new leaf candidate {parsed.new_leaf_candidate}: "
        f"{parsed.rationale} {original}"
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
