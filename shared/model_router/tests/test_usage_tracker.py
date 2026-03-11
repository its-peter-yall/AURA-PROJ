# test_usage_tracker.py
# Tests for UsageTracker Redis persistence and ModelRouter usage hooks.

# Covers UsageTracker.record() persistence to Redis sorted sets,
# session-specific sorted sets, time-range queries, aggregation
# summaries, and ModelRouter integration for generate() and stream().

# @see: model_router/usage_tracker.py - UsageTracker class under test
# @see: model_router/router.py - Router hooks for usage tracking
# @note: Uses FakeAsyncRedis from conftest.py with sorted set extensions.

"""Tests for UsageTracker Redis persistence and router integration."""

import json
from datetime import datetime, timezone

import pytest

from model_router.cost_calculator import CostCalculator
from model_router.types import (
    GenerateRequest,
    GenerateResponse,
    ProviderType,
    StreamChunk,
    UsageInfo,
    UsageRecord,
)
from model_router.usage_tracker import (
    USAGE_KEY,
    USAGE_SESSION_PREFIX,
    UsageTracker,
)


class FakeSortedSetRedis:
    """In-memory async Redis double with sorted set support."""

    def __init__(self) -> None:
        self._sorted_sets: dict[str, list[tuple[float, str]]] = {}

    async def zadd(
        self,
        name: str,
        mapping: dict[str, float],
    ) -> int:
        """Add members to a sorted set with scores."""
        ss = self._sorted_sets.setdefault(name, [])
        added = 0
        for member, score in mapping.items():
            ss.append((score, member))
            added += 1
        ss.sort(key=lambda x: x[0])
        return added

    async def zrangebyscore(
        self,
        name: str,
        min_score: float,
        max_score: float,
    ) -> list[str]:
        """Return members within the score range."""
        ss = self._sorted_sets.get(name, [])
        return [
            member
            for score, member in ss
            if min_score <= score <= max_score
        ]

    async def zcard(self, name: str) -> int:
        """Return the number of members in a sorted set."""
        return len(self._sorted_sets.get(name, []))

    def dump_sorted_set(self, name: str) -> list[tuple[float, str]]:
        """Expose sorted set contents for test assertions."""
        return list(self._sorted_sets.get(name, []))


@pytest.fixture
def fake_sorted_redis() -> FakeSortedSetRedis:
    """Return a fake Redis with sorted set support."""
    return FakeSortedSetRedis()


@pytest.fixture
def tracker(fake_sorted_redis: FakeSortedSetRedis) -> UsageTracker:
    """Return a UsageTracker with fake Redis."""
    return UsageTracker(fake_sorted_redis)


class TestUsageTrackerRecord:
    """UsageTracker.record() persistence tests."""

    @pytest.mark.asyncio
    async def test_record_stores_in_global_sorted_set(
        self,
        tracker: UsageTracker,
        fake_sorted_redis: FakeSortedSetRedis,
    ) -> None:
        """record() stores a UsageRecord in the global sorted set."""
        usage = UsageInfo(input_tokens=100, output_tokens=50)

        await tracker.record(
            usage=usage,
            model="gemini-2.0-flash",
            provider=ProviderType.VERTEX_AI,
            estimated_cost=0.0003,
        )

        count = await fake_sorted_redis.zcard(USAGE_KEY)
        assert count == 1

        entries = fake_sorted_redis.dump_sorted_set(USAGE_KEY)
        record = UsageRecord.model_validate_json(entries[0][1])
        assert record.model == "gemini-2.0-flash"
        assert record.provider == ProviderType.VERTEX_AI
        assert record.input_tokens == 100
        assert record.output_tokens == 50
        assert record.estimated_cost_usd == 0.0003

    @pytest.mark.asyncio
    async def test_record_with_session_stores_in_session_set(
        self,
        tracker: UsageTracker,
        fake_sorted_redis: FakeSortedSetRedis,
    ) -> None:
        """record() with session_id also stores in session-specific set."""
        usage = UsageInfo(input_tokens=100, output_tokens=50)

        await tracker.record(
            usage=usage,
            model="gemini-2.0-flash",
            provider=ProviderType.VERTEX_AI,
            estimated_cost=0.0003,
            session_id="sess-123",
        )

        session_key = f"{USAGE_SESSION_PREFIX}sess-123"
        count = await fake_sorted_redis.zcard(session_key)
        assert count == 1

        entries = fake_sorted_redis.dump_sorted_set(session_key)
        record = UsageRecord.model_validate_json(entries[0][1])
        assert record.session_id == "sess-123"

    @pytest.mark.asyncio
    async def test_record_without_session_skips_session_set(
        self,
        tracker: UsageTracker,
        fake_sorted_redis: FakeSortedSetRedis,
    ) -> None:
        """record() without session_id does not create session set."""
        usage = UsageInfo(input_tokens=100, output_tokens=50)

        await tracker.record(
            usage=usage,
            model="gemini-2.0-flash",
            provider=ProviderType.VERTEX_AI,
        )

        # Only the global key should have entries
        global_count = await fake_sorted_redis.zcard(USAGE_KEY)
        assert global_count == 1

        # No session key created
        assert len(fake_sorted_redis._sorted_sets) == 1


class TestUsageTrackerGetRecords:
    """UsageTracker.get_records() time-range query tests."""

    @pytest.mark.asyncio
    async def test_get_records_returns_within_time_range(
        self,
        tracker: UsageTracker,
        fake_sorted_redis: FakeSortedSetRedis,
    ) -> None:
        """get_records() returns records within the time range."""
        usage = UsageInfo(input_tokens=100, output_tokens=50)

        # Record multiple entries
        await tracker.record(
            usage=usage,
            model="gemini-2.0-flash",
            provider=ProviderType.VERTEX_AI,
        )
        await tracker.record(
            usage=usage,
            model="gemini-2.5-pro",
            provider=ProviderType.VERTEX_AI,
        )

        start = datetime(2020, 1, 1, tzinfo=timezone.utc)
        end = datetime(2030, 1, 1, tzinfo=timezone.utc)

        records = await tracker.get_records(start, end)
        assert len(records) == 2

    @pytest.mark.asyncio
    async def test_get_records_filters_by_provider(
        self,
        tracker: UsageTracker,
        fake_sorted_redis: FakeSortedSetRedis,
    ) -> None:
        """get_records() with provider filter returns matching records."""
        usage = UsageInfo(input_tokens=100, output_tokens=50)

        await tracker.record(
            usage=usage,
            model="gemini-2.0-flash",
            provider=ProviderType.VERTEX_AI,
        )
        await tracker.record(
            usage=usage,
            model="anthropic/claude-sonnet-4",
            provider=ProviderType.OPENROUTER,
        )

        start = datetime(2020, 1, 1, tzinfo=timezone.utc)
        end = datetime(2030, 1, 1, tzinfo=timezone.utc)

        records = await tracker.get_records(
            start, end, provider="vertex_ai"
        )
        assert len(records) == 1
        assert records[0].provider == ProviderType.VERTEX_AI


class TestUsageTrackerSessionSummary:
    """UsageTracker.get_session_summary() aggregation tests."""

    @pytest.mark.asyncio
    async def test_get_session_summary_aggregates_totals(
        self,
        tracker: UsageTracker,
    ) -> None:
        """get_session_summary() returns aggregated totals."""
        await tracker.record(
            usage=UsageInfo(input_tokens=100, output_tokens=50),
            model="gemini-2.0-flash",
            provider=ProviderType.VERTEX_AI,
            estimated_cost=0.0003,
            session_id="sess-abc",
        )
        await tracker.record(
            usage=UsageInfo(input_tokens=200, output_tokens=100),
            model="gemini-2.0-flash",
            provider=ProviderType.VERTEX_AI,
            estimated_cost=0.0006,
            session_id="sess-abc",
        )

        summary = await tracker.get_session_summary("sess-abc")

        assert summary["total_input_tokens"] == 300
        assert summary["total_output_tokens"] == 150
        assert summary["total_cost"] == pytest.approx(0.0009)
        assert summary["request_count"] == 2

    @pytest.mark.asyncio
    async def test_get_session_summary_empty_session(
        self,
        tracker: UsageTracker,
    ) -> None:
        """get_session_summary() for unknown session returns zeros."""
        summary = await tracker.get_session_summary("nonexistent")

        assert summary["total_cost"] == 0.0
        assert summary["request_count"] == 0


class TestUsageTrackerGetSummary:
    """UsageTracker.get_summary() aggregation tests."""

    @pytest.mark.asyncio
    async def test_get_summary_returns_aggregated_totals(
        self,
        tracker: UsageTracker,
    ) -> None:
        """get_summary() returns total cost, requests, by_provider, etc."""
        await tracker.record(
            usage=UsageInfo(input_tokens=100, output_tokens=50),
            model="gemini-2.0-flash",
            provider=ProviderType.VERTEX_AI,
            estimated_cost=0.0003,
        )
        await tracker.record(
            usage=UsageInfo(input_tokens=200, output_tokens=100),
            model="anthropic/claude-sonnet-4",
            provider=ProviderType.OPENROUTER,
            estimated_cost=0.002,
        )

        start = datetime(2020, 1, 1, tzinfo=timezone.utc)
        end = datetime(2030, 1, 1, tzinfo=timezone.utc)

        summary = await tracker.get_summary(start, end)

        assert summary["total_cost"] == pytest.approx(0.0023)
        assert summary["total_requests"] == 2
        assert len(summary["by_provider"]) == 2
        assert len(summary["by_model"]) == 2

    @pytest.mark.asyncio
    async def test_get_summary_with_provider_filter(
        self,
        tracker: UsageTracker,
    ) -> None:
        """get_summary() with provider filter returns only that provider."""
        await tracker.record(
            usage=UsageInfo(input_tokens=100, output_tokens=50),
            model="gemini-2.0-flash",
            provider=ProviderType.VERTEX_AI,
            estimated_cost=0.0003,
        )
        await tracker.record(
            usage=UsageInfo(input_tokens=200, output_tokens=100),
            model="anthropic/claude-sonnet-4",
            provider=ProviderType.OPENROUTER,
            estimated_cost=0.002,
        )

        start = datetime(2020, 1, 1, tzinfo=timezone.utc)
        end = datetime(2030, 1, 1, tzinfo=timezone.utc)

        summary = await tracker.get_summary(
            start, end, provider="vertex_ai"
        )

        assert summary["total_requests"] == 1
        assert summary["total_cost"] == pytest.approx(0.0003)


class TestRouterUsageIntegration:
    """ModelRouter usage tracking integration tests."""

    @pytest.mark.asyncio
    async def test_generate_records_usage(self) -> None:
        """Router with tracker calls record() after generate()."""
        from model_router import ModelRouter
        from model_router.config import (
            OpenRouterConfig,
            RouterConfig,
            VertexAIConfig,
        )

        redis = FakeSortedSetRedis()
        tracker = UsageTracker(redis)
        calculator = CostCalculator()

        config = RouterConfig(
            test_mode=True,
            vertex_ai=VertexAIConfig(
                project_id="test-project", region="global"
            ),
            openrouter=OpenRouterConfig(api_key="test-key"),
        )
        router = ModelRouter(config)
        router.set_usage_tracking(tracker, calculator)

        await router.generate(
            model="gemini-2.0-flash",
            contents="hello",
            metadata={"session_id": "s1", "user_id": "u1"},
        )

        count = await redis.zcard(USAGE_KEY)
        assert count == 1

        entries = redis.dump_sorted_set(USAGE_KEY)
        record = UsageRecord.model_validate_json(entries[0][1])
        assert record.model == "gemini-2.0-flash"
        assert record.provider == ProviderType.VERTEX_AI
        assert record.session_id == "s1"
        assert record.user_id == "u1"

    @pytest.mark.asyncio
    async def test_stream_records_usage(self) -> None:
        """Router with tracker records usage after stream() completes."""
        from model_router import ModelRouter
        from model_router.config import (
            OpenRouterConfig,
            RouterConfig,
            VertexAIConfig,
        )

        redis = FakeSortedSetRedis()
        tracker = UsageTracker(redis)
        calculator = CostCalculator()

        config = RouterConfig(
            test_mode=True,
            vertex_ai=VertexAIConfig(
                project_id="test-project", region="global"
            ),
            openrouter=OpenRouterConfig(api_key="test-key"),
        )
        router = ModelRouter(config)
        router.set_usage_tracking(tracker, calculator)

        chunks = []
        async for chunk in router.stream(
            model="gemini-2.0-flash",
            contents="hello",
            metadata={"session_id": "s2"},
        ):
            chunks.append(chunk)

        assert len(chunks) >= 1

        count = await redis.zcard(USAGE_KEY)
        assert count == 1

        entries = redis.dump_sorted_set(USAGE_KEY)
        record = UsageRecord.model_validate_json(entries[0][1])
        assert record.session_id == "s2"

    @pytest.mark.asyncio
    async def test_router_without_tracker_works_normally(self) -> None:
        """Router without usage tracker works identically to before."""
        from model_router import ModelRouter
        from model_router.config import (
            OpenRouterConfig,
            RouterConfig,
            VertexAIConfig,
        )

        config = RouterConfig(
            test_mode=True,
            vertex_ai=VertexAIConfig(
                project_id="test-project", region="global"
            ),
            openrouter=OpenRouterConfig(api_key="test-key"),
        )
        router = ModelRouter(config)

        # No tracker set -- should work fine
        response = await router.generate(
            model="gemini-2.0-flash", contents="hello"
        )
        assert response.text == "Test-mode output."

        chunks = [
            c
            async for c in router.stream(
                model="gemini-2.0-flash", contents="hello"
            )
        ]
        assert len(chunks) == 1
