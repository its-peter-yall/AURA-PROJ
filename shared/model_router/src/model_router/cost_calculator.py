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

import logging
import math
from typing import TYPE_CHECKING

from model_router.types import ProviderType, UsageInfo

if TYPE_CHECKING:
    from model_router.config import OpenRouterConfig


logger = logging.getLogger(__name__)


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

    # Static General Compute pricing (USD per 1M tokens, as of 2026-05)
    _GC_PRICING: dict[str, dict[str, float]] = {
        "minimax-m2.7": {"input": 0.40, "output": 2.34},
        "deepseek-v3.2": {"input": 3.00, "output": 4.50},
        "deepseek-v3.1": {"input": 3.00, "output": 4.50},
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
        if provider == ProviderType.GENERAL_COMPUTE:
            return self._estimate_general_compute(usage, model)
        return 0.0

    def _estimate_vertex(self, usage: UsageInfo, model: str) -> float:
        """Compute Vertex AI cost from static pricing table.

        Args:
            usage: Token counts from the generation response.
            model: Model identifier, optionally with 'models/' prefix
                   or version suffix (e.g. 'gemini-2.0-flash-001').

        Returns:
            Estimated cost in USD rounded to 6 decimals.
        """
        normalized = model.replace("models/", "")
        pricing = self._VERTEX_PRICING.get(normalized)
        if pricing is None:
            for key, val in self._VERTEX_PRICING.items():
                if normalized.startswith(key):
                    pricing = val
                    break
        if pricing is None:
            return 0.0
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

    def _estimate_general_compute(self, usage: UsageInfo, model: str) -> float:
        """Compute General Compute cost from static pricing table.

        Args:
            usage: Token counts from the generation response.
            model: Model identifier.

        Returns:
            Estimated cost in USD rounded to 6 decimals.
        """
        pricing = self._GC_PRICING.get(model)
        if pricing is None:
            for key, val in self._GC_PRICING.items():
                if model.startswith(key):
                    pricing = val
                    break
        if pricing is None:
            return 0.0
        input_cost = (usage.input_tokens / 1_000_000) * pricing.get("input", 0.0)
        total_output_tokens = usage.output_tokens + usage.thinking_tokens
        output_cost = (total_output_tokens / 1_000_000) * pricing.get("output", 0.0)
        return round(input_cost + output_cost, 6)

    async def populate_openrouter_pricing(
        self,
        config: OpenRouterConfig,
    ) -> None:
        """Fetch and cache OpenRouter model pricing from the models endpoint.

        Args:
            config: OpenRouter provider configuration.
        """
        import httpx

        try:
            async with httpx.AsyncClient(timeout=15.0) as http_client:
                response = await http_client.get(
                    f"{config.base_url.rstrip('/')}/models",
                    headers={"Authorization": f"Bearer {config.api_key}"},
                )
                response.raise_for_status()

            payload = response.json().get("data", [])
            priced_models = 0
            for item in payload:
                if not isinstance(item, dict):
                    continue

                model_id = item.get("id")
                pricing = item.get("pricing")
                if not isinstance(model_id, str) or not isinstance(pricing, dict):
                    continue

                prompt_price = pricing.get("prompt")
                completion_price = pricing.get("completion")
                try:
                    input_per_million = float(prompt_price) * 1_000_000
                    output_per_million = float(completion_price) * 1_000_000
                except (TypeError, ValueError):
                    continue

                if (
                    not math.isfinite(input_per_million)
                    or not math.isfinite(output_per_million)
                    or input_per_million < 0
                    or output_per_million < 0
                ):
                    continue

                self._openrouter_pricing[model_id] = {
                    "input": input_per_million,
                    "output": output_per_million,
                }
                priced_models += 1

            logger.info("Cached OpenRouter pricing for %d models", priced_models)
        except Exception as error:  # noqa: BLE001
            logger.warning(
                "Failed to populate OpenRouter pricing cache: %s",
                error,
            )

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
