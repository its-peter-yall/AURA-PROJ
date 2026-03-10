# test_thinking.py
# Thinking config translation tests for OpenRouter request shaping.

# Covers Claude budget-to-effort mapping, DeepSeek always-on reasoning,
# and graceful degradation for models that do not expose provider-specific
# thinking controls through the shared router abstraction.

# @see: model_router/providers/openrouter.py - Thinking param translation
# @note: These tests target the pure helper function with no SDK access.

"""Tests for thinking config translation across OpenRouter models."""

from model_router.providers.openrouter import _build_thinking_params


class TestClaudeThinkingConfig:
    """Claude models use reasoning.effort mapping."""

    def test_claude_thinking_low_budget(self) -> None:
        params = _build_thinking_params(
            'anthropic/claude-sonnet-4',
            {'thinking_budget': 512},
        )

        assert params == {'reasoning': {'effort': 'low'}}

    def test_claude_thinking_medium_budget(self) -> None:
        params = _build_thinking_params(
            'anthropic/claude-sonnet-4',
            {'thinking_budget': 2048},
        )

        assert params == {'reasoning': {'effort': 'medium'}}

    def test_claude_thinking_high_budget(self) -> None:
        params = _build_thinking_params(
            'anthropic/claude-sonnet-4',
            {'thinking_budget': 8192},
        )

        assert params == {'reasoning': {'effort': 'high'}}

    def test_claude_thinking_boundary_low(self) -> None:
        low = _build_thinking_params(
            'anthropic/claude-sonnet-4',
            {'thinking_budget': 1024},
        )
        medium = _build_thinking_params(
            'anthropic/claude-sonnet-4',
            {'thinking_budget': 1025},
        )

        assert low == {'reasoning': {'effort': 'low'}}
        assert medium == {'reasoning': {'effort': 'medium'}}

    def test_claude_thinking_boundary_medium(self) -> None:
        medium = _build_thinking_params(
            'anthropic/claude-sonnet-4',
            {'thinking_budget': 4096},
        )
        high = _build_thinking_params(
            'anthropic/claude-sonnet-4',
            {'thinking_budget': 4097},
        )

        assert medium == {'reasoning': {'effort': 'medium'}}
        assert high == {'reasoning': {'effort': 'high'}}

    def test_claude_thinking_zero_budget(self) -> None:
        params = _build_thinking_params(
            'anthropic/claude-sonnet-4',
            {'thinking_budget': 0},
        )

        assert params == {}

    def test_claude_thinking_negative_budget(self) -> None:
        params = _build_thinking_params(
            'anthropic/claude-sonnet-4',
            {'thinking_budget': -1},
        )

        assert params == {}

    def test_claude_no_thinking_config(self) -> None:
        assert _build_thinking_params('anthropic/claude-sonnet-4', None) == {}


class TestDeepSeekThinking:
    """DeepSeek R1 reasoning is always on, so config is ignored."""

    def test_deepseek_r1_ignores_thinking_config(self) -> None:
        params = _build_thinking_params(
            'deepseek/deepseek-r1',
            {'thinking_budget': 4096},
        )

        assert params == {}

    def test_deepseek_r1_variant_names(self) -> None:
        free_params = _build_thinking_params(
            'deepseek/deepseek-r1:free',
            {'thinking_budget': 4096},
        )
        versioned_params = _build_thinking_params(
            'deepseek/deepseek-r1-0528',
            {'thinking_budget': 4096},
        )

        assert free_params == {}
        assert versioned_params == {}


class TestGracefulDegradation:
    """Unsupported models silently ignore thinking configuration."""

    def test_unsupported_model_no_thinking(self) -> None:
        params = _build_thinking_params(
            'openai/gpt-4o',
            {'thinking_budget': 4096},
        )

        assert params == {}

    def test_meta_llama_no_thinking(self) -> None:
        params = _build_thinking_params(
            'meta-llama/llama-3-70b',
            {'thinking_budget': 2048},
        )

        assert params == {}

    def test_anthropic_prefix_also_matches_claude(self) -> None:
        params = _build_thinking_params(
            'anthropic/claude-opus-4',
            {'thinking_budget': 2048},
        )

        assert params == {'reasoning': {'effort': 'medium'}}
