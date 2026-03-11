# cost_calculator.py
# Provider-specific cost estimation for LLM token usage.

# Computes estimated USD costs from token counts and model pricing.
# Vertex AI uses a static pricing table, OpenRouter uses cached pricing
# from its models API, and Ollama is always free.

# @see: model_router/types.py - UsageInfo and ProviderType models
# @note: All Vertex AI prices are per 1M tokens and should be verified
#        against Google Cloud pricing periodically. Last verified 2026-03.

"""Provider-specific cost estimation for LLM token usage."""

from __future__ import annotations

from model_router.types import ProviderType, UsageInfo


class CostCalculator:
    """Estimate USD cost from token usage and model pricing.

    Supports three pricing strategies:
    - Vertex AI: Static pricing table (per 1M tokens).
    - OpenRouter: Cached pricing from the models API.
    - Ollama: Always $0.00 (local inference).
    """

    # Static Vertex AI pricing (USD per 1M tokens, as of 2026-03)
    _VERTEX_PRICING: dict[str, dict[str, float]] = {
        "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
        "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
        "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
    }

    def __init__(self) -> None:
        """Initialize with empty OpenRouter pricing cache."""
        self._openrouter_pricing: dict[str, dict[str, float]] = {}

    def estimate(
        self,
        usage: UsageInfo,
        model: str,
        provider: ProviderType,
    ) -> float:
        """Estimate USD cost for the given usage and provider.

        Args:
            usage: Token counts from the generation response.
            model: Model identifier used for the request.
            provider: Which provider handled the request.

        Returns:
            Estimated cost in USD, rounded to 6 decimal places.
            Returns 0.0 for unknown models or Ollama.
        """
        if provider == ProviderType.OLLAMA:
            return 0.0
        if provider == ProviderType.VERTEX_AI:
            return self._estimate_vertex(usage, model)
        if provider == ProviderType.OPENROUTER:
            return self._estimate_openrouter(usage, model)
        return 0.0

    def _estimate_vertex(self, usage: UsageInfo, model: str) -> float:
        """Compute Vertex AI cost from static pricing table.

        Args:
            usage: Token counts from the generation response.
            model: Model identifier, optionally with 'models/' prefix.

        Returns:
            Estimated cost in USD rounded to 6 decimals.
        """
        normalized = model.replace("models/", "")
        pricing = self._VERTEX_PRICING.get(normalized, {})
        input_cost = (usage.input_tokens / 1_000_000) * pricing.get("input", 0.0)
        # Thinking tokens priced at output rate (industry standard)
        total_output_tokens = usage.output_tokens + usage.thinking_tokens
        output_cost = (total_output_tokens / 1_000_000) * pricing.get("output", 0.0)
        return round(input_cost + output_cost, 6)

    def _estimate_openrouter(
        self,
        usage: UsageInfo,
        model: str,
    ) -> float:
        """Compute OpenRouter cost from cached pricing data.

        Args:
            usage: Token counts from the generation response.
            model: OpenRouter model identifier (e.g. vendor/model).

        Returns:
            Estimated cost in USD rounded to 6 decimals.
        """
        pricing = self._openrouter_pricing.get(model, {})
        input_cost = (usage.input_tokens / 1_000_000) * pricing.get("input", 0.0)
        # Thinking tokens priced at output rate (industry standard)
        total_output_tokens = usage.output_tokens + usage.thinking_tokens
        output_cost = (total_output_tokens / 1_000_000) * pricing.get("output", 0.0)
        return round(input_cost + output_cost, 6)

    def update_openrouter_pricing(
        self,
        pricing: dict[str, dict[str, float]],
    ) -> None:
        """Update cached pricing data for OpenRouter models.

        Args:
            pricing: Mapping of model ID to input/output pricing
                     (USD per 1M tokens).
        """
        self._openrouter_pricing.update(pricing)
