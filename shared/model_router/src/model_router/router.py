# router.py
# Core router for provider registration, routing, and request delegation.

# Centralizes provider bootstrap and request routing for shared generation and
# embedding calls. This update adds lazy OpenRouter auto-registration while
# preserving the existing Vertex AI bootstrap and routing heuristics.

# @see: model_router/config.py - RouterConfig and provider config models
# @note: Slash-delimited model IDs route to OpenRouter unless overridden.

"""Core router for provider registration, routing, and delegation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, AsyncGenerator

from model_router.config import OpenRouterConfig, RouterConfig
from model_router.errors import ModelRouterError, ModelUnavailableError
from model_router.providers.base import BaseEmbeddingProvider, BaseProvider
from model_router.providers.vertex_ai import (
    VertexAIEmbeddingProvider,
    VertexAIProvider,
)
from model_router.types import (
    GenerateRequest,
    GenerateResponse,
    ModelInfo,
    ProviderType,
    StreamChunk,
    UsageInfo,
)

if TYPE_CHECKING:
    from model_router.cost_calculator import CostCalculator
    from model_router.key_manager import KeyManager
    from model_router.usage_tracker import UsageTracker

logger = logging.getLogger(__name__)

_default_router: "ModelRouter | None" = None


def _coerce_provider_type(value: ProviderType | str) -> ProviderType:
    """Normalize a provider identifier to the ProviderType enum."""
    if isinstance(value, ProviderType):
        return value
    return ProviderType(value)


def _coerce_metadata_provider_type(value: ProviderType | str) -> ProviderType:
    """Normalize metadata provider input to shared router errors."""
    try:
        return _coerce_provider_type(value)
    except ValueError as error:
        raise ModelUnavailableError(
            f"No provider registered for {value}",
            provider=str(value),
            original=error,
        ) from error


class ModelRouter:
    """Route generation and embedding requests to registered providers."""

    def __init__(
        self,
        config: RouterConfig | None = None,
        key_manager: "KeyManager | None" = None,
    ) -> None:
        self._config = config or RouterConfig()
        self._providers: dict[ProviderType, BaseProvider] = {}
        self._embedding_providers: dict[ProviderType, BaseEmbeddingProvider] = {}
        self._usage_tracker: "UsageTracker | None" = None
        self._cost_calculator: "CostCalculator | None" = None
        self._key_manager: "KeyManager | None" = key_manager

        if self._should_auto_register_vertex():
            vertex_provider = VertexAIProvider(self._config.vertex_ai)
            embedding_provider = VertexAIEmbeddingProvider(self._config.vertex_ai)
            self.register_provider(ProviderType.VERTEX_AI, vertex_provider)
            self.register_embedding_provider(ProviderType.VERTEX_AI, embedding_provider)

        if self._should_auto_register_openrouter():
            from model_router.providers.openrouter import (
                OpenRouterEmbeddingProvider,
                OpenRouterProvider,
            )

            openrouter_provider = OpenRouterProvider(self._config.openrouter)
            self.register_provider(ProviderType.OPENROUTER, openrouter_provider)
            self.register_embedding_provider(
                ProviderType.OPENROUTER,
                OpenRouterEmbeddingProvider(self._config.openrouter),
            )

    def _should_auto_register_vertex(self) -> bool:
        """Return True when config should bootstrap the Vertex AI providers."""
        return self._config.test_mode or bool(self._config.vertex_ai.project_id)

    def _should_auto_register_openrouter(self) -> bool:
        """Return True when config should bootstrap the OpenRouter provider."""
        return self._config.test_mode or bool(self._config.openrouter.api_key)

    async def _maybe_lazy_register_openrouter(self) -> None:
        """Lazily register OpenRouter provider if key exists in KeyManager.

        This enables UI-stored API keys to work without OPENROUTER_API_KEY
        env var at router initialization. Called when a slash-form model ID
        routes to OpenRouter but the provider is not yet registered.
        """
        # Already registered - nothing to do
        if ProviderType.OPENROUTER in self._providers:
            return

        # No KeyManager available - cannot lazy register
        if self._key_manager is None:
            return

        try:
            api_key = await self._key_manager.get_key("openrouter")
            if api_key:
                from model_router.providers.openrouter import (
                    OpenRouterEmbeddingProvider,
                    OpenRouterProvider,
                )

                openrouter_config = self._config.openrouter
                # Create provider with fetched key (override any empty config key)
                or_config = OpenRouterConfig(
                    api_key=api_key,
                    base_url=openrouter_config.base_url,
                    site_url=openrouter_config.site_url,
                    site_name=openrouter_config.site_name,
                )
                provider = OpenRouterProvider(or_config)
                self.register_provider(ProviderType.OPENROUTER, provider)
                self.register_embedding_provider(
                    ProviderType.OPENROUTER,
                    OpenRouterEmbeddingProvider(or_config),
                )
                logger.info("Lazy registered OpenRouter provider from KeyManager")
        except Exception:
            logger.warning(
                "Failed to lazy register OpenRouter provider",
                exc_info=True,
            )

    def set_usage_tracking(
        self,
        tracker: "UsageTracker",
        calculator: "CostCalculator",
    ) -> None:
        """Bind usage tracking for late initialization.

        Use this when the Redis client is not available at router
        construction time.

        Args:
            tracker: UsageTracker instance for recording.
            calculator: CostCalculator instance for cost estimation.
        """
        self._usage_tracker = tracker
        self._cost_calculator = calculator

    def register_provider(
        self,
        provider_type: ProviderType,
        provider: BaseProvider,
    ) -> None:
        """Register a generation provider implementation."""
        self._providers[provider_type] = provider

    def register_embedding_provider(
        self,
        provider_type: ProviderType,
        provider: BaseEmbeddingProvider,
    ) -> None:
        """Register an embedding provider implementation."""
        self._embedding_providers[provider_type] = provider

    def get_provider(
        self,
        provider_type: ProviderType | str,
    ) -> BaseProvider:
        """Return a registered provider for provider-specific operations."""
        resolved_type = _coerce_metadata_provider_type(provider_type)
        provider = self._providers.get(resolved_type)
        if provider is None:
            raise ModelUnavailableError(
                f"No provider registered for {resolved_type.value}",
                provider=resolved_type.value,
            )
        return provider

    def _determine_provider_type(self, request: GenerateRequest) -> ProviderType:
        """Determine which provider should handle a generation request."""
        if request.provider:
            try:
                return _coerce_provider_type(request.provider)
            except ValueError as error:
                raise ModelUnavailableError(
                    f"No provider registered for {request.provider}",
                    provider=str(request.provider),
                    model=request.model,
                    original=error,
                ) from error

        model_name = request.model.strip()
        if model_name.startswith("models/"):
            return ProviderType.VERTEX_AI

        if "/" in model_name:
            return ProviderType.OPENROUTER
        return self._config.default_provider

    async def _resolve_provider(self, request: GenerateRequest) -> BaseProvider:
        """Resolve the provider instance for a generation request."""
        resolved_type = self._determine_provider_type(request)
        provider = self._providers.get(resolved_type)

        # Attempt lazy OpenRouter registration if needed
        if provider is None and resolved_type is ProviderType.OPENROUTER:
            await self._maybe_lazy_register_openrouter()
            # Re-check after lazy registration attempt
            provider = self._providers.get(resolved_type)

        if provider is None:
            raise ModelUnavailableError(
                f"No provider registered for {resolved_type.value}",
                provider=resolved_type.value,
                model=request.model,
            )
        return provider

    def _build_request(
        self,
        request: GenerateRequest | None,
        kwargs: dict[str, Any],
    ) -> GenerateRequest:
        """Return the request object for generate/stream convenience methods."""
        if request is not None:
            return request
        if not kwargs:
            raise ValueError("request or generation kwargs are required")
        return GenerateRequest(**kwargs)

    async def generate(
        self,
        request: GenerateRequest | None = None,
        **kwargs: Any,
    ) -> GenerateResponse:
        """Generate content through the resolved provider."""
        resolved_request = self._build_request(request, kwargs)
        provider = await self._resolve_provider(resolved_request)
        response = await provider.generate(resolved_request)

        if self._usage_tracker and self._cost_calculator:
            try:
                cost = self._cost_calculator.estimate(
                    response.usage,
                    response.model_used,
                    response.provider,
                )
                await self._usage_tracker.record(
                    usage=response.usage,
                    model=response.model_used,
                    provider=response.provider,
                    estimated_cost=cost,
                    session_id=resolved_request.metadata.get("session_id"),
                    user_id=resolved_request.metadata.get("user_id"),
                )
            except Exception:
                logger.warning(
                    "Usage tracking failed for generate()",
                    exc_info=True,
                )

        return response

    async def list_models(
        self,
        provider: ProviderType | str | None = None,
    ) -> list[ModelInfo]:
        """List available models from one or all registered providers."""
        if provider is not None:
            resolved_provider = self.get_provider(provider)
            return await resolved_provider.list_models()

        all_models: list[ModelInfo] = []
        for registered_provider in self._providers.values():
            all_models.extend(await registered_provider.list_models())
        for embedding_provider in self._embedding_providers.values():
            all_models.extend(await embedding_provider.list_models())
        return all_models

    async def health_check(
        self,
        provider: ProviderType | str | None = None,
    ) -> dict[ProviderType, bool]:
        """Check one or all registered providers for availability."""
        if provider is not None:
            resolved_type = _coerce_metadata_provider_type(provider)
            registered_provider = self._providers.get(resolved_type)
            if registered_provider is None:
                return {resolved_type: False}
            return {resolved_type: await registered_provider.health_check()}

        results: dict[ProviderType, bool] = {}
        for provider_type, registered_provider in self._providers.items():
            results[provider_type] = await registered_provider.health_check()
        return results

    async def embed(
        self,
        texts: list[str] | None = None,
        *,
        text: str | None = None,
        provider: ProviderType | str | None = None,
    ) -> list[list[float]]:
        """Generate validated embeddings through the configured provider."""
        if text is not None and texts is None:
            texts = [text]

        if not self._embedding_providers:
            raise ModelRouterError("No embedding provider registered")

        if provider is not None:
            try:
                provider_type = _coerce_provider_type(provider)
            except ValueError as error:
                raise ModelRouterError(
                    "Unknown embedding provider",
                    provider=str(provider),
                    original=error,
                ) from error

            embedding_provider = self._embedding_providers.get(provider_type)
            if embedding_provider is None:
                available = ", ".join(p.value for p in self._embedding_providers)
                raise ModelRouterError(
                    f"No embedding provider registered for {provider_type.value}. "
                    f"Available: {available}",
                    provider=provider_type.value,
                )
            return await embedding_provider.embed(texts or [])

        # Default: use the first registered embedding provider
        first_provider = next(iter(self._embedding_providers.values()))
        return await first_provider.embed(texts or [])

    async def stream(
        self,
        request: GenerateRequest | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream normalized chunks from the resolved provider."""
        resolved_request = self._build_request(request, kwargs)
        provider = await self._resolve_provider(resolved_request)

        total_text = ""
        async for chunk in provider.stream(resolved_request):  # type: ignore[reportGeneralTypeIssues]
            total_text += chunk.text
            yield chunk

        if self._usage_tracker and self._cost_calculator:
            try:
                provider_type = self._determine_provider_type(resolved_request)
                # Estimate tokens from character count (~4 chars/token)
                est_output = max(len(total_text) // 4, 1)
                est_input = max(len(str(resolved_request.contents)) // 4, 1)
                usage = UsageInfo(
                    input_tokens=est_input,
                    output_tokens=est_output,
                )
                cost = self._cost_calculator.estimate(
                    usage,
                    resolved_request.model,
                    provider_type,
                )
                await self._usage_tracker.record(
                    usage=usage,
                    model=resolved_request.model,
                    provider=provider_type,
                    estimated_cost=cost,
                    session_id=resolved_request.metadata.get("session_id"),
                    user_id=resolved_request.metadata.get("user_id"),
                    operation="stream",
                )
            except Exception:
                logger.warning(
                    "Usage tracking failed for stream()",
                    exc_info=True,
                )

    async def stream_with_usage(
        self,
        request: GenerateRequest | None = None,
        *,
        usage_out: list[UsageInfo] | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream normalized chunks with optional usage data output.

        Yields StreamChunk objects like stream(). If usage_out is provided,
        the usage data will be appended to that list when the stream
        completes, allowing callers to access it without re-estimation.

        Args:
            request: Generation request or None (uses kwargs).
            usage_out: Optional mutable list to receive UsageInfo after
                      stream completion. List will have one item appended.
            **kwargs: Request fields if request object not provided.

        Example:
            usage_data: list[UsageInfo] = []
            async for chunk in router.stream_with_usage(req, usage_out=usage_data):
                print(chunk.text)
            # usage_data[0] now contains the UsageInfo
        """
        resolved_request = self._build_request(request, kwargs)
        provider = await self._resolve_provider(resolved_request)

        total_output_text = ""
        total_thinking_text = ""
        async for chunk in provider.stream(resolved_request):  # type: ignore[reportGeneralTypeIssues]
            if chunk.type == "thinking":
                total_thinking_text += chunk.text
            else:
                total_output_text += chunk.text
            yield chunk

        est_input = max(len(str(resolved_request.contents)) // 4, 1)
        est_output = max(len(total_output_text) // 4, 1)
        est_thinking = max(len(total_thinking_text) // 4, 0)
        usage = UsageInfo(
            input_tokens=est_input,
            output_tokens=est_output,
            thinking_tokens=est_thinking,
        )

        if usage_out is not None:
            usage_out.append(usage)

        if self._usage_tracker and self._cost_calculator:
            try:
                provider_type = self._determine_provider_type(resolved_request)
                cost = self._cost_calculator.estimate(
                    usage,
                    resolved_request.model,
                    provider_type,
                )
                await self._usage_tracker.record(
                    usage=usage,
                    model=resolved_request.model,
                    provider=provider_type,
                    estimated_cost=cost,
                    session_id=resolved_request.metadata.get("session_id"),
                    user_id=resolved_request.metadata.get("user_id"),
                    operation="stream",
                )
            except Exception:
                logger.warning(
                    "Usage tracking failed for stream_with_usage()",
                    exc_info=True,
                )


def get_default_router() -> ModelRouter:
    """Return a process-wide router singleton built from environment config."""
    global _default_router
    if _default_router is None:
        _default_router = ModelRouter(RouterConfig.from_env())
    return _default_router


def reset_default_router() -> None:
    """Reset the cached default router singleton."""
    global _default_router
    _default_router = None


__all__ = ["ModelRouter", "get_default_router", "reset_default_router"]
