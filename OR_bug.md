# OpenRouter Cost Tracking & Dashboard Accuracy Bug Report

## Overview
The usage dashboard (e.g., `/usage` in AURA-NOTES-MANAGER) currently displays **$0.0000 cost** for all OpenRouter models despite showing token usage. Investigation confirms the dashboard **does not fetch actual cost metrics from OpenRouter**, and the local cost estimation logic for OpenRouter is completely uninitialized in production.

## 🔴 Root Cause 1: Missing OpenRouter Pricing Data
The core reason OpenRouter models show $0.0000 is that the pricing cache is never populated.

- **File:** `shared/model_router/src/model_router/cost_calculator.py`
- **Mechanism:** The `CostCalculator` uses an internal dictionary `_openrouter_pricing` to calculate costs for OpenRouter models.
- **The Bug:** The method `update_openrouter_pricing()` is **never called in production code**. A search across the codebase reveals it is only ever used in `test_cost_calculator.py`. 
- **Consequence:** When `_estimate_openrouter()` executes, `pricing = self._openrouter_pricing.get(model, {})` returns an empty dict, resulting in `$0.00 * tokens = $0.00`.

## 🔴 Root Cause 2: Completely Local Estimation
The dashboard does not pull real-time billing or usage metrics from OpenRouter's API. 

- **File:** `AURA-NOTES-MANAGER/api/routers/usage.py` and `shared/model_router/src/model_router/usage_tracker.py`
- **Mechanism:** The dashboard relies 100% on `UsageTracker.get_summary()`, which reads `UsageRecord` entries stored locally in Redis.
- **The Bug / Limitation:** While `OpenRouterProvider.get_credit_balance()` exists and calls OpenRouter's `/auth/key` endpoint, this data is *only* used for health checks and validation. Actual spend is never synced back to the dashboard.

## 🟠 Additional Accuracy Issue 1: Streaming Token Estimation
Even if pricing were populated, the token counts used for cost calculation during streaming are highly inaccurate.

- **File:** `shared/model_router/src/model_router/router.py` (methods `stream` and `stream_with_usage`)
- **Mechanism:** Streaming responses do not currently capture exact token usage from the OpenRouter stream chunks.
- **The Bug:** The router falls back to a rudimentary character-count estimation: `est_output = max(len(total_text) // 4, 1)`. This guarantees a divergence between the dashboard's "Tokens" metric and what OpenRouter actually bills.

## 🟡 Additional Accuracy Issue 2: Date Range Truncation
Same-day usage data may randomly disappear from the dashboard due to timezone/date parsing.

- **File:** `AURA-NOTES-MANAGER/api/routers/usage.py`
- **Mechanism:** The `_parse_date_range` function converts YYYY-MM-DD strings from the frontend into `datetime` objects.
- **The Bug:** When `end_date` is parsed from a string, it defaults to `00:00:00 UTC` of that day. Any usage that occurs *later* on that same day is excluded from the Redis `ZRANGEBYSCORE` query.

---

## 🛠️ Recommended Remediation Plan

1. **Populate Pricing Cache on Startup / Model Fetch:**
   Update `OpenRouterProvider.list_models()` (in `shared/model_router/src/model_router/providers/openrouter.py`) to parse the `pricing` fields returned by the `https://openrouter.ai/api/v1/models` endpoint.
   Wire this into the `CostCalculator` during app startup or via a periodic background Celery/ARQ task.

2. **Capture Actual Streaming Tokens:**
   Modify the OpenRouter streaming parser to capture the `usage` block that OpenRouter sends at the end of its SSE streams (when `include_usage` is requested), rather than relying on `len() // 4`.

3. **Fix Date Range Filters:**
   Update `_parse_date_range` to set the `end_date` to `23:59:59.999999` of the target day.

4. **(Optional) Sync Actual Spend:**
   To perfectly match the OpenRouter dashboard, build an admin-level sync task that periodically queries OpenRouter's actual usage endpoints and overrides the local estimations.