"""Unified error hierarchy for all model router operations."""


class ModelRouterError(Exception):
    """Base error for model router failures."""

    def __init__(
        self,
        message: str,
        *,
        provider: str = '',
        model: str = '',
        original: BaseException | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.original = original
        if original is not None:
            self.__cause__ = original


class AuthenticationError(ModelRouterError):
    """Provider authentication failed."""


class RateLimitError(ModelRouterError):
    """Provider rate limit exceeded."""

    def __init__(
        self,
        message: str,
        *,
        provider: str = '',
        model: str = '',
        original: BaseException | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(
            message,
            provider=provider,
            model=model,
            original=original,
        )
        self.retry_after = retry_after


class ContentPolicyError(ModelRouterError):
    """Provider blocked content due to safety or policy."""


class ModelUnavailableError(ModelRouterError):
    """Requested model is unavailable."""


class ProviderTimeoutError(ModelRouterError):
    """Provider timed out while processing a request."""


class EmbeddingDimensionError(ModelRouterError):
    """Embedding dimension mismatch between expected and actual sizes."""

    def __init__(
        self,
        *,
        expected: int,
        actual: int,
        provider: str = '',
        model: str = '',
        original: BaseException | None = None,
    ) -> None:
        super().__init__(
            (
                'Embedding dimension mismatch: '
                f'expected {expected}, got {actual}'
            ),
            provider=provider,
            model=model,
            original=original,
        )
        self.expected = expected
        self.actual = actual
