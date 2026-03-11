# test_cost_calculator.py
# Tests for UsageRecord model, GenerateRequest metadata, and CostCalculator.

# Covers UsageRecord JSON round-trip serialization, GenerateRequest metadata
# field, and CostCalculator pricing for Vertex AI (static), OpenRouter
# (cached), and Ollama ($0) with edge cases for unknown models.

# @see: model_router/types.py - UsageRecord and GenerateRequest models
# @see: model_router/cost_calculator.py - CostCalculator class
# @note: All pricing tests use deterministic values for reproducibility.

"""Tests for UsageRecord, GenerateRequest metadata, and CostCalculator."""

import pytest

from model_router.types import (
    GenerateRequest,
    ProviderType,
    UsageInfo,
    UsageRecord,
)
from model_router.cost_calculator import CostCalculator


class TestUsageRecord:
    """UsageRecord model serialization and field defaults."""

    def test_usage_record_serializes_to_json(self) -> None:
        """UsageRecord model serializes to JSON with all fields."""
        from datetime import datetime, timezone

        record = UsageRecord(
            timestamp=datetime(2026, 3, 11, 12, 0, 0, tzinfo=timezone.utc),
            provider=ProviderType.VERTEX_AI,
            model="gemini-2.0-flash",
            input_tokens=100,
            output_tokens=50,
            thinking_tokens=10,
            estimated_cost_usd=0.000030,
            is_estimated=True,
            session_id="session-1",
            user_id="user-1",
            operation="chat",
        )

        json_str = record.model_dump_json()
        restored = UsageRecord.model_validate_json(json_str)

        assert restored.provider == ProviderType.VERTEX_AI
        assert restored.model == "gemini-2.0-flash"
        assert restored.input_tokens == 100
        assert restored.output_tokens == 50
        assert restored.thinking_tokens == 10
        assert restored.estimated_cost_usd == 0.000030
        assert restored.is_estimated is True
        assert restored.session_id == "session-1"
        assert restored.user_id == "user-1"
        assert restored.operation == "chat"

    def test_usage_record_defaults(self) -> None:
        """UsageRecord has sensible defaults for optional fields."""
        from datetime import datetime, timezone

        record = UsageRecord(
            timestamp=datetime(2026, 3, 11, tzinfo=timezone.utc),
            provider=ProviderType.OLLAMA,
            model="llama3",
        )

        assert record.input_tokens == 0
        assert record.output_tokens == 0
        assert record.thinking_tokens == 0
        assert record.estimated_cost_usd == 0.0
        assert record.is_estimated is True
        assert record.session_id is None
        assert record.user_id is None
        assert record.operation == "chat"


class TestGenerateRequestMetadata:
    """GenerateRequest metadata field tests."""

    def test_generate_request_accepts_metadata(self) -> None:
        """GenerateRequest accepts optional metadata dict."""
        request = GenerateRequest(
            model="gemini-2.0-flash",
            contents="hello",
            metadata={"session_id": "s1", "user_id": "u1"},
        )

        assert request.metadata == {"session_id": "s1", "user_id": "u1"}

    def test_generate_request_metadata_defaults_empty(self) -> None:
        """GenerateRequest metadata defaults to empty dict."""
        request = GenerateRequest(
            model="gemini-2.0-flash",
            contents="hello",
        )

        assert request.metadata == {}


class TestCostCalculatorOllama:
    """CostCalculator returns $0 for Ollama."""

    def test_ollama_returns_zero(self) -> None:
        """Ollama cost is always 0.0 regardless of tokens."""
        calc = CostCalculator()
        usage = UsageInfo(
            input_tokens=10000,
            output_tokens=5000,
            thinking_tokens=1000,
        )

        cost = calc.estimate(usage, "llama3", ProviderType.OLLAMA)

        assert cost == 0.0


class TestCostCalculatorVertexAI:
    """CostCalculator Vertex AI static pricing tests."""

    def test_vertex_flash_pricing(self) -> None:
        """Vertex AI gemini-2.0-flash: $0.10/1M input, $0.40/1M output."""
        calc = CostCalculator()
        usage = UsageInfo(input_tokens=1000, output_tokens=500)

        cost = calc.estimate(usage, "gemini-2.0-flash", ProviderType.VERTEX_AI)

        # input: 1000/1M * 0.10 = 0.0001
        # output: 500/1M * 0.40 = 0.0002
        # total: 0.0003
        assert cost == pytest.approx(0.0003, abs=1e-7)

    def test_vertex_pro_pricing(self) -> None:
        """Vertex AI gemini-2.5-pro uses its specific pricing tier."""
        calc = CostCalculator()
        usage = UsageInfo(input_tokens=1000, output_tokens=500)

        cost = calc.estimate(usage, "gemini-2.5-pro", ProviderType.VERTEX_AI)

        # input: 1000/1M * 1.25 = 0.00125
        # output: 500/1M * 5.00 = 0.0025
        # total: 0.00375
        assert cost == pytest.approx(0.00375, abs=1e-7)

    def test_vertex_flash_25_pricing(self) -> None:
        """Vertex AI gemini-2.5-flash pricing tier."""
        calc = CostCalculator()
        usage = UsageInfo(input_tokens=1000, output_tokens=500)

        cost = calc.estimate(usage, "gemini-2.5-flash", ProviderType.VERTEX_AI)

        # input: 1000/1M * 0.15 = 0.00015
        # output: 500/1M * 0.60 = 0.0003
        # total: 0.00045
        assert cost == pytest.approx(0.00045, abs=1e-7)

    def test_vertex_strips_models_prefix(self) -> None:
        """Vertex AI normalizes 'models/' prefix for pricing lookup."""
        calc = CostCalculator()
        usage = UsageInfo(input_tokens=1000, output_tokens=500)

        cost = calc.estimate(usage, "models/gemini-2.0-flash", ProviderType.VERTEX_AI)

        assert cost == pytest.approx(0.0003, abs=1e-7)

    def test_vertex_unknown_model_returns_zero(self) -> None:
        """Unknown Vertex model returns 0.0 (graceful degradation)."""
        calc = CostCalculator()
        usage = UsageInfo(input_tokens=1000, output_tokens=500)

        cost = calc.estimate(usage, "gemini-unknown-model", ProviderType.VERTEX_AI)

        assert cost == 0.0

    def test_vertex_version_suffix_matches_base_model(self) -> None:
        """Vertex AI model with version suffix matches base pricing."""
        calc = CostCalculator()
        usage = UsageInfo(input_tokens=1000, output_tokens=500)

        cost = calc.estimate(
            usage, "gemini-2.0-flash-001", ProviderType.VERTEX_AI,
        )

        # Should match gemini-2.0-flash pricing
        assert cost == pytest.approx(0.0003, abs=1e-7)

    def test_vertex_preview_suffix_matches_base_model(self) -> None:
        """Vertex AI model with preview suffix matches base pricing."""
        calc = CostCalculator()
        usage = UsageInfo(input_tokens=1000, output_tokens=500)

        cost = calc.estimate(
            usage,
            "gemini-2.5-pro-preview-05-06",
            ProviderType.VERTEX_AI,
        )

        # Should match gemini-2.5-pro pricing
        assert cost == pytest.approx(0.00375, abs=1e-7)

    def test_vertex_includes_thinking_tokens_in_output_cost(self) -> None:
        """Thinking tokens are priced at output rate for Vertex AI."""
        calc = CostCalculator()
        usage = UsageInfo(
            input_tokens=1000,
            output_tokens=500,
            thinking_tokens=200,
        )

        cost = calc.estimate(usage, "gemini-2.0-flash", ProviderType.VERTEX_AI)

        # input: 1000/1M * 0.10 = 0.0001
        # output: (500 + 200)/1M * 0.40 = 0.00028
        # total: 0.00038
        assert cost == pytest.approx(0.00038, abs=1e-7)


class TestCostCalculatorOpenRouter:
    """CostCalculator OpenRouter cached pricing tests."""

    def test_openrouter_uses_cached_pricing(self) -> None:
        """OpenRouter uses cached pricing dict for estimation."""
        calc = CostCalculator()
        calc.update_openrouter_pricing(
            {
                "anthropic/claude-sonnet-4": {
                    "input": 3.00,
                    "output": 15.00,
                },
            }
        )
        usage = UsageInfo(input_tokens=1000, output_tokens=500)

        cost = calc.estimate(
            usage,
            "anthropic/claude-sonnet-4",
            ProviderType.OPENROUTER,
        )

        # input: 1000/1M * 3.00 = 0.003
        # output: 500/1M * 15.00 = 0.0075
        # total: 0.0105
        assert cost == pytest.approx(0.0105, abs=1e-7)

    def test_openrouter_unknown_model_returns_zero(self) -> None:
        """OpenRouter unknown model returns 0.0."""
        calc = CostCalculator()
        usage = UsageInfo(input_tokens=1000, output_tokens=500)

        cost = calc.estimate(
            usage,
            "unknown/model",
            ProviderType.OPENROUTER,
        )

        assert cost == 0.0

    def test_update_openrouter_pricing_stores_data(self) -> None:
        """update_openrouter_pricing() stores pricing for later estimates."""
        calc = CostCalculator()

        calc.update_openrouter_pricing(
            {
                "meta-llama/llama-3-70b": {
                    "input": 0.59,
                    "output": 0.79,
                },
            }
        )
        usage = UsageInfo(input_tokens=2000, output_tokens=1000)

        cost = calc.estimate(
            usage,
            "meta-llama/llama-3-70b",
            ProviderType.OPENROUTER,
        )

        # input: 2000/1M * 0.59 = 0.00118
        # output: 1000/1M * 0.79 = 0.00079
        # total: 0.00197
        assert cost == pytest.approx(0.00197, abs=1e-7)

    def test_openrouter_includes_thinking_tokens_in_output_cost(self) -> None:
        """Thinking tokens are priced at output rate for OpenRouter."""
        calc = CostCalculator()
        calc.update_openrouter_pricing(
            {
                "anthropic/claude-sonnet-4": {
                    "input": 3.00,
                    "output": 15.00,
                },
            }
        )
        usage = UsageInfo(
            input_tokens=1000,
            output_tokens=500,
            thinking_tokens=300,
        )

        cost = calc.estimate(
            usage,
            "anthropic/claude-sonnet-4",
            ProviderType.OPENROUTER,
        )

        # input: 1000/1M * 3.00 = 0.003
        # output: (500 + 300)/1M * 15.00 = 0.012
        # total: 0.015
        assert cost == pytest.approx(0.015, abs=1e-7)
