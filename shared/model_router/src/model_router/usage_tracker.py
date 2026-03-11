# usage_tracker.py
# Redis-backed usage tracking for LLM request instrumentation.

# Persists UsageRecord entries to Redis sorted sets keyed by timestamp,
# enabling time-range queries for dashboards and session-scoped cost
# aggregation. Follows the same constructor-injected Redis pattern
# as SettingsStore and KeyManager.

# @see: model_router/types.py - UsageRecord and UsageInfo models
# @see: model_router/cost_calculator.py - Cost estimation before recording
# @note: All tracking failures are caught and logged, never propagated.

"""Redis-backed usage tracking for LLM request instrumentation."""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from model_router.types import ProviderType, UsageInfo, UsageRecord

logger = logging.getLogger(__name__)

USAGE_KEY = "aura:usage:records"
USAGE_SESSION_PREFIX = "aura:usage:session:"


class UsageTracker:
    """Record and query LLM usage data in Redis sorted sets.

    Each record is stored as a JSON-serialized member with the Unix
    timestamp as its score, enabling efficient time-range queries
    via ZRANGEBYSCORE.

    Args:
        redis_client: Async Redis-compatible client with sorted set
                      methods (zadd, zrangebyscore, zcard).
    """

    def __init__(self, redis_client: Any) -> None:
        """Store the injected async Redis client.

        Args:
            redis_client: Async Redis-compatible client.
        """
        self._redis = redis_client

    async def record(
        self,
        usage: UsageInfo,
        model: str,
        provider: ProviderType,
        estimated_cost: float = 0.0,
        session_id: str | None = None,
        user_id: str | None = None,
        operation: str = "chat",
    ) -> None:
        """Persist a usage record to Redis sorted sets.

        Stores in the global sorted set and, if session_id is
        provided, also in a session-specific sorted set.

        Args:
            usage: Token counts from the generation response.
            model: Model identifier used for the request.
            provider: Which provider handled the request.
            estimated_cost: Estimated cost in USD.
            session_id: Optional study session identifier.
            user_id: Optional user identifier.
            operation: Type of operation (chat, embed, extract).
        """
        now = datetime.now(timezone.utc)
        record = UsageRecord(
            timestamp=now,
            provider=provider,
            model=model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            thinking_tokens=usage.thinking_tokens,
            estimated_cost_usd=estimated_cost,
            session_id=session_id,
            user_id=user_id,
            operation=operation,
        )

        score = record.timestamp.timestamp()
        payload = record.model_dump_json()

        await self._redis.zadd(USAGE_KEY, {payload: score})

        if session_id:
            session_key = f"{USAGE_SESSION_PREFIX}{session_id}"
            await self._redis.zadd(session_key, {payload: score})

    async def get_records(
        self,
        start_date: datetime,
        end_date: datetime,
        provider: str | None = None,
    ) -> list[UsageRecord]:
        """Return usage records within a time range.

        Args:
            start_date: Start of the query range (inclusive).
            end_date: End of the query range (inclusive).
            provider: Optional provider filter (e.g. "vertex_ai").

        Returns:
            List of UsageRecord within the time range.
        """
        start_score = start_date.timestamp()
        end_score = end_date.timestamp()

        raw_entries = await self._redis.zrangebyscore(
            USAGE_KEY, start_score, end_score
        )

        records = []
        for entry in raw_entries:
            text = entry.decode() if isinstance(entry, bytes) else entry
            record = UsageRecord.model_validate_json(text)
            if provider and record.provider.value != provider:
                continue
            records.append(record)

        return records

    async def get_session_summary(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        """Return aggregated usage totals for a session.

        Args:
            session_id: Study session identifier.

        Returns:
            Dict with total_cost, total_input_tokens,
            total_output_tokens, total_thinking_tokens,
            and request_count.
        """
        session_key = f"{USAGE_SESSION_PREFIX}{session_id}"

        raw_entries = await self._redis.zrangebyscore(
            session_key, float("-inf"), float("+inf")
        )

        total_cost = 0.0
        total_input = 0
        total_output = 0
        total_thinking = 0

        for entry in raw_entries:
            text = entry.decode() if isinstance(entry, bytes) else entry
            record = UsageRecord.model_validate_json(text)
            total_cost += record.estimated_cost_usd
            total_input += record.input_tokens
            total_output += record.output_tokens
            total_thinking += record.thinking_tokens

        return {
            "total_cost": total_cost,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_thinking_tokens": total_thinking,
            "request_count": len(raw_entries),
        }

    async def get_summary(
        self,
        start_date: datetime,
        end_date: datetime,
        provider: str | None = None,
    ) -> dict[str, Any]:
        """Return aggregated usage summary for a time range.

        Args:
            start_date: Start of the query range (inclusive).
            end_date: End of the query range (inclusive).
            provider: Optional provider filter.

        Returns:
            Dict with total_cost, total_requests, by_provider,
            by_model, and daily breakdowns.
        """
        records = await self.get_records(start_date, end_date, provider)

        total_cost = 0.0
        total_requests = len(records)

        provider_agg: dict[str, dict[str, float | int]] = defaultdict(
            lambda: {"cost": 0.0, "requests": 0}
        )
        model_agg: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"cost": 0.0, "requests": 0, "provider": ""}
        )
        daily_agg: dict[str, dict[str, float | int]] = defaultdict(
            lambda: {"cost": 0.0, "requests": 0}
        )

        for record in records:
            total_cost += record.estimated_cost_usd

            prov_key = record.provider.value
            provider_agg[prov_key]["cost"] += record.estimated_cost_usd
            provider_agg[prov_key]["requests"] += 1

            model_agg[record.model]["cost"] += record.estimated_cost_usd
            model_agg[record.model]["requests"] += 1
            model_agg[record.model]["provider"] = prov_key

            date_key = record.timestamp.strftime("%Y-%m-%d")
            daily_agg[date_key]["cost"] += record.estimated_cost_usd
            daily_agg[date_key]["requests"] += 1

        by_provider = [
            {
                "provider": prov,
                "cost": data["cost"],
                "requests": data["requests"],
            }
            for prov, data in sorted(provider_agg.items())
        ]

        by_model = [
            {
                "model": model,
                "provider": data["provider"],
                "cost": data["cost"],
                "requests": data["requests"],
            }
            for model, data in sorted(model_agg.items())
        ]

        daily = [
            {
                "date": date,
                "cost": data["cost"],
                "requests": data["requests"],
            }
            for date, data in sorted(daily_agg.items())
        ]

        return {
            "total_cost": total_cost,
            "total_requests": total_requests,
            "by_provider": by_provider,
            "by_model": by_model,
            "daily": daily,
        }
