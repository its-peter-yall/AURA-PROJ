# Phase 1: Multi-model Chat Configuration - Research

**Researched:** 2026-04-18  
**Domain:** Multi-model chat configuration with 1-5 model selection  
**Confidence:** HIGH

## Summary

This phase extends the v1.2 Settings Wiring E2E milestone to support **multiple chat models** (1-5) with a **default selection mechanism**. The current system (v1.2) only supports a single default chat model configured via SettingsStore in Redis. This phase will allow administrators to configure multiple models (up to 5) that users can choose from in the chat interface, with one designated as the default.

**Primary recommendation:** Extend the existing SettingsStore schema to support an array of chat models with a `default_index` field, update the `/chat/config` endpoint to return the available models list, and modify the chat page's `InlineModelPicker` to use the admin-configured subset instead of all available models.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- [v1.1 scoping]: Shared package at project root (`shared/model_router/`), not LiteLLM or LangChain
- [v1.1 scoping]: Vertex AI (full) + OpenRouter (full) + Ollama (stub only)
- [v1.2 scoping]: `resolve_use_case_config()` utility centralizes 3-step resolution chain
- [v1.2 scoping]: Zombie-None cache fix with 30s error TTL
- [v1.2 scoping]: `gatekeeper` and `relationship_extraction` added to ALLOWED_USE_CASES
- [Phase 17-02]: AURA-CHAT settings page uses existing axios instance, placed OUTSIDE RoleProtectedRoute

### the agent's Discretion
- Implementation details for multi-model array storage format
- UI/UX for model ordering and default selection in settings
- Validation strategy for model count limits (1-5)

### Deferred Ideas (OUT OF SCOPE)
- Phase 10 follow-up: migrate or remove `AURA-CHAT/test_real_models.py` and extend compliance audit
- Phase 08 Plan 03: close outstanding cross-app regression validation
- Thinking-capable OpenRouter models undocumented — plan dynamic for v1.3

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 19.2.0 | Frontend UI | Already in use, modern features |
| Zustand | 4.x | State management | Used for session-scoped model storage |
| TanStack Query | 5.90.15 | Server state | Already used for settings API |
| FastAPI | 0.109+ | Backend API | Existing framework |
| Redis | 7+ | SettingsStore | Already used for runtime config |
| Pydantic | v2 | Schema validation | Existing validation layer |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| framer-motion | 11.x | UI animations | Already used in InlineModelPicker |
| lucide-react | 0.x | Icons | Existing icon library |

### Installation
```bash
# No new dependencies required - using existing stack
```

## Architecture Patterns

### Recommended Data Flow
```
┌─────────────────────────────────────────────────────────────────┐
│  Admin Settings UI                                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ DefaultModelSection (modified)                            │  │
│  │ - Multi-select for chat use case (1-5 models)             │  │
│  │ - "Set as Default" button per model                       │  │
│  │ - Drag/drop or arrow buttons for ordering                 │  │
│  └───────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │ PUT /settings/defaults/chat
                            │ {provider, models[], default_index}
┌───────────────────────────▼─────────────────────────────────────┐
│  Backend (FastAPI)                                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ SettingsStore (extended)                                  │  │
│  │ - Redis hash: aura:model_router:settings                  │  │
│  │ - chat key stores: {provider, models[], default_index}    │  │
│  └───────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │ GET /chat/config
┌───────────────────────────▼─────────────────────────────────────┐
│  Chat UI                                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ InlineModelPicker (modified)                              │  │
│  │ - Uses allowedModels from /chat/config                    │  │
│  │ - Shows only admin-selected models (1-5)                  │  │
│  │ - Pre-selects default model on session create             │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Current vs Proposed Schema

**Current SettingsStore Schema (v1.2):**
```python
# Redis: aura:model_router:settings
{
  "chat": {"provider": "vertex_ai", "model": "gemini-2.5-flash-lite"},
  "embeddings": {"provider": "vertex_ai", "model": "text-embedding-004"},
  # ... other use cases
}
```

**Proposed Multi-Model Schema (Phase 1):**
```python
# Redis: aura:model_router:settings
{
  "chat": {
    "provider": "vertex_ai",  # Primary provider (for compatibility)
    "model": "gemini-2.5-flash-lite",  # Default model (for compatibility)
    "models": [  # NEW: Array of 1-5 models
      {"provider": "vertex_ai", "model": "gemini-2.5-flash-lite"},
      {"provider": "openrouter", "model": "openai/gpt-4o-mini"},
      {"provider": "vertex_ai", "model": "gemini-2.5-flash"}
    ],
    "default_index": 0  # NEW: Index of default model in models array
  },
  # ... other use cases (unchanged)
}
```

### Pattern 1: Backward-Compatible Schema Extension
**What:** Extend the existing chat configuration while maintaining backward compatibility with existing code that reads single `provider`/`model` fields.

**When to use:** When the new multi-model feature needs to coexist with existing single-model consumers.

**Example:**
```python
# model_router/settings_store.py
async def get_default(self, use_case: str) -> dict[str, Any] | None:
    """Return the configured default for a specific use case.
    
    For chat use case with multi-model config, returns the default
    model from the models array (at default_index).
    """
    raw_value = await self._redis.hget(SETTINGS_KEY, use_case)
    if raw_value is None:
        return None
    
    parsed = json.loads(_decode_redis_text(raw_value))
    
    # Handle multi-model chat configuration
    if use_case == "chat" and "models" in parsed and parsed["models"]:
        default_idx = parsed.get("default_index", 0)
        default_model = parsed["models"][default_idx]
        return {
            "provider": default_model["provider"],
            "model": default_model["model"],
            # Include full config for consumers that need it
            "_multi_model_config": parsed
        }
    
    # Legacy single-model format
    return parsed
```

### Pattern 2: UI-Driven Model Selection
**What:** The settings UI allows admins to select multiple models from the full available list, set one as default, and optionally order them.

**When to use:** For the chat use case where users need model choice constrained by admin policy.

**Implementation approach:**
1. Extend `DefaultModelSection` to show multi-select UI for chat use case only
2. Use existing `HierarchicalModelPicker` for individual model selection
3. Add list UI showing selected models with reordering and "Set as Default" actions

### Anti-Patterns to Avoid
- **Breaking existing single-model consumers:** Don't remove `provider`/`model` fields from chat config - maintain them as aliases to the default model
- **Storing provider-specific model lists:** Don't duplicate model discovery logic - use existing `ModelCache`
- **Frontend-side filtering only:** Enforce the 1-5 model limit at the API level, not just in UI

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Model list caching | Custom cache | `ModelCache` in model_router | Already handles provider failures, TTL, refresh |
| Settings persistence | File-based config | `SettingsStore` (Redis) | Runtime updates without restart, cross-app sharing |
| Model validation | Manual regex | Provider's model list endpoint | Validates against actual available models |
| Multi-select UI | Custom checkbox list | Existing patterns + HierarchicalModelPicker | Consistent UX, accessibility, tested |

**Key insight:** The existing `ModelCache`, `SettingsStore`, and `HierarchicalModelPicker` provide all the primitives needed. The work is in orchestrating them for the multi-model use case.

## Common Pitfalls

### Pitfall 1: Cache Inconsistency Between Single and Multi-Model Views
**What goes wrong:** The `_defaults_cache` in `settings_store.py` caches at the use_case level. If different consumers read different formats (single-model vs multi-model), they may get stale data.

**Why it happens:** The cache key is just the use_case string, not the requested format.

**How to avoid:** Ensure all consumers go through the same `get_default()` method which normalizes to the standard `{provider, model}` format. The `_multi_model_config` extra field can be used by consumers that need the full list.

**Warning signs:** Model list doesn't update immediately after settings change; different pages show different defaults.

### Pitfall 2: Chat Page Not Reflecting Default Model Change
**What goes wrong:** When admin changes the default model in settings, existing chat sessions continue using the old default.

**Why it happens:** `useModelStore` persists session-specific model selections in sessionStorage, overriding the default.

**How to avoid:** On session creation, always initialize from `/chat/config` default. Only persist user overrides. Clear model selection when default changes (compare stored default with config response).

**Warning signs:** New sessions start with wrong model; model reverts after page refresh.

### Pitfall 3: Provider Mismatch in Multi-Model Config
**What goes wrong:** Admin selects models from multiple providers but the chat backend uses the wrong provider credentials.

**Why it happens:** Each model has its own provider, but some code paths may use a single provider override.

**How to avoid:** Ensure every model entry in the array includes its provider. The chat router already handles provider-specific routing via `set_model(model, provider)` - verify this works for all models in the list.

**Warning signs:** API errors about invalid credentials; requests going to wrong provider endpoint.

### Pitfall 4: Exceeding Model Count Limits
**What goes wrong:** Admin somehow configures 6+ models, or UI allows invalid selection.

**Why it happens:** Validation only in UI, not API; race conditions in concurrent updates.

**How to avoid:** Validate 1-5 model limit in `set_default()` API endpoint. Return 400 error with clear message if exceeded.

## Code Examples

### Settings Store Extension for Multi-Model
```python
# shared/model_router/src/model_router/settings_store.py

async def get_chat_models_config(self) -> dict[str, Any] | None:
    """Get full multi-model chat configuration.
    
    Returns:
        Dict with models array and default_index, or None if not configured.
    """
    raw_value = await self._redis.hget(SETTINGS_KEY, "chat")
    if raw_value is None:
        return None
    
    parsed = json.loads(_decode_redis_text(raw_value))
    
    # Handle both old and new format
    if "models" in parsed:
        return parsed
    
    # Convert legacy format to new format
    return {
        "provider": parsed.get("provider"),
        "model": parsed.get("model"),
        "models": [
            {
                "provider": parsed.get("provider", "vertex_ai"),
                "model": parsed.get("model", "gemini-2.5-flash-lite")
            }
        ],
        "default_index": 0
    }

async def set_chat_models(
    self,
    models: list[dict[str, str]],
    default_index: int = 0
) -> None:
    """Set the multi-model chat configuration.
    
    Args:
        models: List of {provider, model} dicts (1-5 items)
        default_index: Index of the default model in the array
        
    Raises:
        ValueError: If models list is empty or has >5 items
    """
    if not models:
        raise ValueError("At least one model must be configured")
    if len(models) > 5:
        raise ValueError("Maximum 5 models allowed")
    if not (0 <= default_index < len(models)):
        raise ValueError("default_index out of range")
    
    payload = {
        "models": models,
        "default_index": default_index,
        # Maintain backward compatibility
        "provider": models[default_index]["provider"],
        "model": models[default_index]["model"]
    }
    
    await self._redis.hset(SETTINGS_KEY, "chat", json.dumps(payload))
```

### API Endpoint for Multi-Model Settings
```python
# AURA-CHAT/server/routers/settings.py

class ChatModelsUpdate(BaseModel):
    """Payload for updating chat multi-model configuration."""
    models: list[DefaultModelUpdate]  # 1-5 items
    default_index: int = Field(ge=0, le=4)

@router.put("/defaults/chat/models")
async def set_chat_models(
    payload: ChatModelsUpdate,
    store: SettingsStore = Depends(get_settings_store),
) -> dict[str, Any]:
    """Update the multi-model configuration for chat use case."""
    if len(payload.models) < 1 or len(payload.models) > 5:
        raise HTTPException(
            status_code=400,
            detail="Chat models must be between 1 and 5"
        )
    if payload.default_index >= len(payload.models):
        raise HTTPException(
            status_code=400,
            detail="default_index exceeds models list length"
        )
    
    models_data = [
        {"provider": m.provider, "model": m.model}
        for m in payload.models
    ]
    
    await store.set_chat_models(models_data, payload.default_index)
    
    return {
        "use_case": "chat",
        "models": models_data,
        "default_index": payload.default_index,
    }

@router.get("/defaults/chat/models")
async def get_chat_models(
    store: SettingsStore = Depends(get_settings_store),
) -> dict[str, Any]:
    """Get the multi-model configuration for chat use case."""
    config = await store.get_chat_models_config()
    if config is None:
        # Return fallback default
        default = _USE_CASE_DEFAULTS["chat"]
        return {
            "models": [default],
            "default_index": 0,
            "provider": default["provider"],
            "model": default["model"]
        }
    return config
```

### Chat Config Response with Multi-Model
```python
# AURA-CHAT/server/routers/chat.py

@router.get("/config")
async def get_config():
    """Get chat configuration including available models."""
    # ... existing model discovery logic ...
    
    # Fetch multi-model config from SettingsStore
    chat_models_config = None
    default_model = config.RAG_MODEL_DEFAULT
    try:
        _store = SettingsStore(get_redis())
        chat_models_config = await _store.get_chat_models_config()
        if chat_models_config:
            models_config = chat_models_config.get("models", [])
            default_idx = chat_models_config.get("default_index", 0)
            if models_config and 0 <= default_idx < len(models_config):
                default_model = models_config[default_idx]["model"]
                # Build allowed_models from admin selection
                allowed_models = [m["model"] for m in models_config]
    except Exception as e:
        logger.warning("Failed to fetch chat models config: %s", e)
    
    return {
        "allowed_models": allowed_models,  # Now 1-5 admin-selected models
        "default_model": default_model,
        "thinking": {
            "enabled": config.ENABLE_THINKING,
            "supported_models": supported_models,
            "model_capabilities": model_capabilities,
            "enabled_modes": config.THINKING_ENABLED_MODES,
        },
    }
```

### Frontend: Multi-Model Settings UI
```typescript
// AURA-CHAT/client/src/features/settings/components/ChatModelsSection.tsx

interface ChatModelConfig {
  models: Array<{ provider: string; model: string }>;
  default_index: number;
}

export function ChatModelsSection() {
  const { data: config, isLoading } = useChatModelsConfig();
  const updateMutation = useUpdateChatModels();
  const { data: allModels } = useAllModels();
  
  const [selectedModels, setSelectedModels] = useState<Array<{ provider: string; model: string }>>([]);
  const [defaultIndex, setDefaultIndex] = useState(0);
  
  useEffect(() => {
    if (config) {
      setSelectedModels(config.models);
      setDefaultIndex(config.default_index);
    }
  }, [config]);
  
  const handleAddModel = (provider: string, model: string) => {
    if (selectedModels.length >= 5) {
      toast.error("Maximum 5 models allowed");
      return;
    }
    setSelectedModels([...selectedModels, { provider, model }]);
  };
  
  const handleRemoveModel = (index: number) => {
    const newModels = selectedModels.filter((_, i) => i !== index);
    setSelectedModels(newModels);
    if (defaultIndex >= newModels.length) {
      setDefaultIndex(Math.max(0, newModels.length - 1));
    }
  };
  
  const handleSetDefault = (index: number) => {
    setDefaultIndex(index);
  };
  
  const handleSave = () => {
    updateMutation.mutate({
      models: selectedModels,
      default_index: defaultIndex
    });
  };
  
  // Render: List of selected models with remove/set-default buttons
  // Plus HierarchicalModelPicker to add new models
}
```

### Frontend: Chat Page Using Multi-Model Config
```typescript
// AURA-CHAT/client/src/features/chat/ChatPage.tsx (relevant section)

export function ChatPage() {
  // ... existing state ...
  
  // Fetch chat config (now returns 1-5 admin-selected models)
  const { data: config } = useQuery({
    queryKey: ['chatConfig'],
    queryFn: getChatConfig,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
  
  // Extract allowed models from config
  const allowedModels = config?.allowed_models; // Array of 1-5 model IDs
  const defaultModel = config?.default_model;
  
  // Initialize session model from default if not set
  useEffect(() => {
    if (currentSessionId && defaultModel && !sessionModel) {
      setSessionModel(currentSessionId, defaultModel);
    }
  }, [currentSessionId, defaultModel, sessionModel]);
  
  // InlineModelPicker now only shows allowedModels
  // ...
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single hardcoded model | SettingsStore-backed default | v1.2 (Settings Wiring) | Admin-configurable without restart |
| All models visible to users | Admin-selected subset (1-5) | Phase 1 (this) | Controlled model availability, simpler UX |
| Env var fallback only | 3-step resolution chain | v1.2 | Redis → Env → Hardcoded fallback |

**Deprecated/outdated:**
- Direct env var access for chat model: Use `resolve_use_case_config()` instead
- Frontend model list hardcoding: Use `/chat/config` endpoint

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Backward compatibility required for single-model consumers | Architecture Patterns | Breaking changes would require updating all consumers simultaneously |
| A2 | 1-5 model limit is sufficient for admin use cases | User Constraints | May need to increase limit later if requirements change |
| A3 | Default model should be session-scoped, not user-scoped | Chat Page Integration | Different sessions may want different models; user-scoped would be too rigid |
| A4 | Provider information must be stored per-model | Backend Architecture | OpenRouter models have format "vendor/model", but provider is still needed for routing |

## Open Questions

1. **Model Ordering:** Should the order in the settings UI determine the order in the chat dropdown, or should it always be alphabetical?
   - What we know: Users prefer predictable ordering; alphabetical is consistent
   - What's unclear: Whether admins want to curate the display order
   - Recommendation: Support ordering in settings UI (drag/drop or arrows), persist in config

2. **Migration Strategy:** How to handle existing Redis settings when deploying this change?
   - What we know: Current format is `{"provider": "x", "model": "y"}`
   - What's unclear: Whether we auto-migrate on first read or require manual migration
   - Recommendation: Auto-migrate in `get_chat_models_config()` - convert single to array format

3. **Validation Timing:** Should invalid model selections (provider down, model removed) be caught at save time or use-time?
   - What we know: Providers can go down temporarily; models can be deprecated
   - What's unclear: Whether strict validation at save is too brittle
   - Recommendation: Validate format at save; validate availability lazily at use-time with fallback

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Redis | SettingsStore | ✓ | 7+ | In-memory cache (existing) |
| React 19 | Frontend | ✓ | 19.2.0 | — |
| FastAPI | Backend | ✓ | 0.109+ | — |
| Existing model_router | Backend/Frontend | ✓ | Local package | — |

**Missing dependencies with no fallback:** None

**Missing dependencies with fallback:** None

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (backend), Vitest (frontend) |
| Config file | `shared/model_router/pyproject.toml`, `AURA-CHAT/client/vitest.config.ts` |
| Quick run command | `python -m pytest shared/model_router/tests/test_settings_store.py -x` |
| Full suite command | `python -m pytest shared/model_router/tests/` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| MULTI-01 | SettingsStore supports multi-model format | unit | `pytest test_settings_store.py` | ✅ existing |
| MULTI-02 | API validates 1-5 model limit | unit | `pytest test_settings_router.py` | ❌ Wave 0 |
| MULTI-03 | /chat/config returns allowed_models array | integration | `pytest tests/api/test_chat.py` | ❌ Wave 0 |
| MULTI-04 | Chat page uses default from config | e2e | `npm run test:e2e` | ❌ Wave 0 |
| MULTI-05 | Model picker shows only allowed models | e2e | `npm run test:e2e` | ❌ Wave 0 |

### Wave 0 Gaps
- [ ] `shared/model_router/tests/test_multi_model_config.py` — unit tests for new methods
- [ ] `AURA-CHAT/server/tests/test_settings_router.py` — test PUT /defaults/chat/models
- [ ] `AURA-CHAT/client/src/features/settings/components/ChatModelsSection.test.tsx` — UI tests

### Sampling Rate
- **Per task commit:** `pytest test_settings_store.py -x` (backend), `npm test -- ChatModelsSection` (frontend)
- **Per wave merge:** Full backend + frontend test suites
- **Phase gate:** All tests green before `/gsd-verify-work`

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | N/A (uses existing auth) |
| V3 Session Management | No | N/A (stateless JWT) |
| V4 Access Control | Yes | Admin-only settings endpoints (existing) |
| V5 Input Validation | Yes | Pydantic validation of 1-5 model limit, array bounds checking |
| V6 Cryptography | No | N/A (no new crypto) |

### Known Threat Patterns for Multi-Model Config

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Model injection (unauthorized model in list) | Tampering | Validate each model against provider's available models |
| Excessive model enumeration | Information Disclosure | Limit to 5 models max; don't expose all available models |
| Default index out of bounds | Denial of Service | Validate default_index < len(models) in API |

## Sources

### Primary (HIGH confidence)
- `shared/model_router/src/model_router/settings_store.py` - Current SettingsStore implementation
- `AURA-CHAT/server/routers/settings.py` - Existing settings API
- `AURA-CHAT/server/routers/chat.py` - Chat config endpoint and model resolution
- `AURA-CHAT/client/src/features/settings/components/DefaultModelSection.tsx` - Current settings UI
- `AURA-CHAT/client/src/features/chat/components/InlineModelPicker.tsx` - Current model picker

### Secondary (MEDIUM confidence)
- `AURA-CHAT/client/src/stores/useModelStore.ts` - Session-scoped model persistence
- `shared/model_router/src/model_router/types.py` - Type definitions
- `.planning/STATE.md` - Recent quick tasks showing model configuration evolution

### Tertiary (LOW confidence)
- None - all critical claims verified against codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - using existing components
- Architecture: HIGH - clear extension pattern from existing code
- Pitfalls: MEDIUM-HIGH - identified from code review and similar implementations
- UI/UX patterns: MEDIUM - based on existing component capabilities

**Research date:** 2026-04-18  
**Valid until:** 30 days (stable architecture)

---

## RESEARCH COMPLETE

**Phase:** 1 - Multi-model chat configuration  
**Confidence:** HIGH

### Key Findings
1. **Backward-compatible schema extension** is the right approach - maintain `provider`/`model` fields as aliases to the default model in the array
2. **SettingsStore** needs two new methods: `get_chat_models_config()` and `set_chat_models()` with 1-5 validation
3. **API endpoint** `/settings/defaults/chat/models` should handle the multi-model CRUD (separate from existing single-model endpoint for compatibility)
4. **Chat config endpoint** already returns `allowed_models` - just need to populate it from admin selection instead of all available models
5. **Frontend changes** are localized to: (a) new ChatModelsSection in settings, (b) InlineModelPicker already accepts `allowedModels` prop

### File Created
`.planning/phases/01-multi-model-chat-configuration-allow-1-5-models-with-default/01-RESEARCH.md`

### Confidence Assessment
| Area | Level | Reason |
|------|-------|--------|
| Standard stack | HIGH | All existing components |
| Architecture | HIGH | Clear extension pattern |
| Pitfalls | HIGH | Identified from code analysis |
| UI/UX patterns | MEDIUM-HIGH | Based on existing components |

### Open Questions
1. Model ordering: admin-curated vs alphabetical (recommend: admin-curated with drag/drop)
2. Migration: auto-convert legacy format on read (recommend: yes)
3. Validation timing: save-time vs use-time (recommend: format at save, availability at use)

### Ready for Planning
Research complete. The planner can now create PLAN.md files with confidence that:
- The architecture leverages existing components (SettingsStore, ModelCache, InlineModelPicker)
- The schema change is backward compatible
- The scope is well-defined (1-5 models, chat use case only)
- Test gaps are identified for Wave 0
