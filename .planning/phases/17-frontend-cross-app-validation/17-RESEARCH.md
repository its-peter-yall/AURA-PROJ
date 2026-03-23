# Phase 17: Frontend + Cross-App Validation — Research

**Researched:** 2026-03-23
**Domain:** React frontend (Settings UI), Playwright E2E, AST audit
**Confidence:** HIGH

## Summary

Phase 17 completes the v1.2 milestone by (1) adding two missing use cases to the AURA-NOTES-MANAGER settings page, (2) building an AURA-CHAT settings page from scratch, (3) writing Playwright E2E tests proving settings→behavior propagation and Redis fallback/recovery, and (4) running the existing AST audit to confirm no direct LLM SDK imports outside `shared/model_router/`.

The work splits into four distinct effort tiers:

- **Low effort (NOTES-MANAGER):** Two-line type change + two entries in `USE_CASES` array + two entries in `USE_CASE_MODEL_TYPES`. All backend code already supports `gatekeeper` and `relationship_extraction`.
- **Medium effort (CHAT):** New `features/settings/` directory mirroring NOTES-MANAGER. Seven files to create: types, API client, hooks (2), components (3), route registration. Components copy cleanly because both apps share identical Tailwind tokens, TanStack Query, and Zustand patterns.
- **Medium effort (E2E):** Playwright tests for settings→behavior (live backend) and Redis fallback (integration test). The existing mock pattern in `e2e/fixtures.ts` provides the foundation.
- **Low effort (audit):** Rerun `python -m pytest tests/test_no_direct_imports.py` — already comprehensive and passing from Phase 10.

**Primary recommendation:** Mirror AURA-NOTES-MANAGER settings infrastructure into AURA-CHAT, then extend E2E to validate the full settings→behavior chain across both apps.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

No CONTEXT.md file found for this phase. All decisions are derived from the ROADMAP.md phase description, REQUIREMENTS.md traceability, and the approved 17-UI-SPEC.md design contract.

### Decisions (from prior phases, locked)
- Both settings routers already include `gatekeeper` and `relationship_extraction` in `ALLOWED_USE_CASES` (Phase 14)
- `resolve_use_case_config()` utility is the single config resolution function (Phase 14)
- SettingsStore (Redis) is authoritative over env vars when reachable (Phase 14, FB-01)
- All 8 consumers across both apps are wired to SettingsStore (Phases 15-16)
- UI-SPEC.md design contract is approved and must be followed exactly

### Claude's Discretion
- AURA-CHAT route protection strategy: `RoleProtectedRoute` currently blocks admins → need to either create a new route guard variant or add an exception for `/settings`
- E2E test infrastructure: Redis stop/start tests may need a different harness than standard Playwright (process control vs browser interaction)
- Component reuse strategy: Copy hooks/API from NOTES-MANAGER vs creating a shared package

### Deferred Ideas (OUT OF SCOPE)
- Dynamic thinking mode model list (FUT-01)
- Multi-provider chat config fallback (FUT-02)
- SettingsStore health indicator in UI (FUT-03)
- Unified config migration
- Provider-specific logic in SettingsStore
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| API-01 | Admin can configure gatekeeper model/provider via settings | NOTES-MANAGER backend router already supports; frontend needs 2-line type + array update |
| API-02 | Admin can configure relationship_extraction model/provider | Same as API-01 — backend ready, frontend needs same update |
| PP-01 | Entity extractor passes explicit provider from SettingsStore | Completed in Phase 15 — validated by E2E test SC-03 |
| PP-02 | Gatekeeper routes through ModelRouter with explicit provider | Completed in Phase 15 — validated by E2E |
| PP-03 | Embeddings passes provider from SettingsStore | Completed in Phase 15 — validated by E2E |
| PP-04 | Relationship extraction reads from SettingsStore | Completed in Phase 15 — validated by E2E |
| PP-05 | KG processor reads from SettingsStore at runtime | Completed in Phase 16 — validated by E2E test SC-03 |
| PP-06 | Entity extractor passes explicit provider (NOTES) | Completed in Phase 16 |
| PP-07 | Embeddings passes provider (NOTES) | Completed in Phase 16 |
| PP-08 | Summarizer routes through ModelRouter | Completed in Phase 16 |
| FB-01 | SettingsStore authoritative over env vars | Completed in Phase 14 — validated by E2E test SC-04 |
| FB-02 | Graceful degradation on Redis down | Completed in Phase 14 — validated by E2E test SC-04 |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 18/19 | Frontend framework | NOTES: 18.3.1, CHAT: 19.2.0 |
| TypeScript | 5.6/5.9 | Type safety | Strict mode in both apps |
| TanStack React Query | 5.x | Server state management | Already used in both apps for all API calls |
| Zustand | latest | Client state (auth) | Auth-only state management in both apps |
| Vite | 6/7 | Build tooling | NOTES: 6.0.5, CHAT: 7.2.4 |
| Tailwind CSS | 4.x | Styling | Identical `@theme` tokens in both apps |
| Playwright | 1.49+ | E2E testing | Configured in both apps |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lucide-react | latest | Icons | All icon needs (Shield, Cpu, Key, Zap, etc.) |
| framer-motion | latest | Animations | HierModelPicker dropdown animations |
| sonner | latest | Toast notifications | useSettingsApi.ts mutation feedback |
| clsx + tailwind-merge | latest | Class merging | `cn()` utility in both apps |
| axios | latest | HTTP client (CHAT) | CHAT uses axios; NOTES uses fetchApi wrapper |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Copy hooks from NOTES to CHAT | Shared frontend package | Overkill for 2 files; monorepo not set up for shared frontend |
| shadcn/ui components | Existing hand-rolled `components/ui/` | Both apps already use custom components; no shadcn registry |

**Installation (AURA-CHAT client — new deps if needed):**
```bash
cd AURA-CHAT/client
npm install sonner  # For toast notifications (if not already installed)
```

---

## Architecture Patterns

### Recommended Project Structure (AURA-CHAT new settings feature)

```
AURA-CHAT/client/src/
├── types/
│   └── settings.ts              # NEW: UseCase, ProviderType, ModelInfo types
├── features/
│   └── settings/
│       ├── api/
│       │   └── settingsApi.ts   # NEW: fetch wrappers for /api/v1/settings/*
│       ├── hooks/
│       │   ├── useSettingsApi.ts # NEW: TanStack Query hooks
│       │   └── useModelList.ts   # NEW: groupModelsByProvider utility
│       ├── components/
│       │   ├── DefaultModelSection.tsx    # NEW: Use case config rows
│       │   ├── ProviderSettingsSection.tsx # NEW: Provider status cards
│       │   ├── ApiKeyManager.tsx          # NEW: API key CRUD
│       │   └── HierarchicalModelPicker.tsx # NEW: Model selection dropdown
│       └── SettingsPage.tsx               # NEW: Main settings page
├── App.tsx                       # MODIFY: Add /settings route
└── components/
    └── AdminSettingsRoute.tsx    # NEW: Admin-only route guard (if needed)
```

### Pattern 1: Settings Page Layout (from UI-SPEC.md)
**What:** 2/3 + 1/3 grid layout — main config (left) + system status sidebar (right)
**When to use:** Both apps use this identical layout
**Example:** See `AURA-NOTES-MANAGER/frontend/src/pages/SettingsPage.tsx` lines 62-246

### Pattern 2: UseCase Config Resolution
**What:** `USE_CASES` array maps use case IDs to labels/descriptions. `USE_CASE_MODEL_TYPES` maps each to `'generation'` or `'embedding'` for model filtering.
**When to use:** Adding new configurable use cases
**Example:**
```typescript
// Source: AURA-NOTES-MANAGER/frontend/src/features/settings/components/DefaultModelSection.tsx
const USE_CASES: { id: UseCase; label: string; description: string }[] = [
    { id: 'chat', label: 'Chat Model', description: '...' },
    { id: 'embeddings', label: 'Embeddings Model', description: '...' },
    { id: 'entity_extraction', label: 'Entity Extraction Model', description: '...' },
    // ADD:
    { id: 'gatekeeper', label: 'Gatekeeper Model', description: 'Used for query validation and access control' },
    { id: 'relationship_extraction', label: 'Relationship Extraction Model', description: 'Used for extracting relationships between entities in documents' },
];
```

### Pattern 3: Settings API Client (axios vs fetch)
**What:** AURA-CHAT uses axios with auth interceptor; NOTES-MANAGER uses `fetchApi` wrapper
**When to use:** AURA-CHAT settings API client should use the existing axios instance from `lib/api.ts`
**Example:**
```typescript
// AURA-CHAT pattern — use existing api instance from lib/api.ts
import api from '@/lib/api';
export const fetchDefaults = () => api.get('/api/v1/settings/defaults');
```

### Anti-Patterns to Avoid
- **Direct SDK imports:** Never import `vertexai`, `google.generativeai`, or `openai` outside `shared/model_router/`
- **Import-time config reads:** Always call `resolve_use_case_config()` at request time, not module import
- **Default exports:** Project convention requires named exports only
- **`any` type:** Use `unknown` or specific types

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Model picker dropdown | Custom searchable select | `HierarchicalModelPicker` from NOTES | Already handles 3-level hierarchy, search, animations |
| Settings API hooks | Raw useEffect + fetch | TanStack Query `useQuery`/`useMutation` | Cache invalidation, loading states, error handling built-in |
| Toast notifications | Custom toast component | `sonner` library | Already used in NOTES, lightweight |
| AST import scanning | Custom Python AST script | `tests/test_no_direct_imports.py` | Already comprehensive, covers both apps |
| Route protection | Manual auth checks in components | `RoleProtectedRoute` pattern | Existing auth guard pattern |

**Key insight:** The settings feature in AURA-CHAT is a near-exact copy of NOTES-MANAGER's settings — the only difference is the API base URL (axios vs fetch) and the system status sidebar content (Chat Server health vs Notes Manager health).

---

## Common Pitfalls

### Pitfall 1: AURA-CHAT Admin Route Access
**What goes wrong:** `RoleProtectedRoute` in AURA-CHAT actively blocks admin users, redirecting them to NOTES-MANAGER. Adding `/settings` route behind this guard means admins can never reach it.
**Why it happens:** `RoleProtectedRoute` checks `isAdmin()` and returns null/redirect for admin users (line 63 of `RoleProtectedRoute.tsx`).
**How to avoid:** Create a separate `AdminSettingsRoute` component OR add the settings route outside `RoleProtectedRoute` with its own admin check. The NOTES-MANAGER pattern uses `AdminHeader` with role-based access in the backend.
**Warning signs:** Admin user lands on NOTES-MANAGER instead of settings page.

### Pitfall 2: API Base URL Mismatch
**What goes wrong:** AURA-CHAT settings hooks hit the wrong backend (NOTES-MANAGER on port 8001 vs CHAT on port 8000).
**Why it happens:** The axios instance in `lib/api.ts` uses `API_BASE_URL = 'http://127.0.0.1:8000'`. New settings API calls must use this same instance.
**How to avoid:** Import `api` from `@/lib/api` for all settings API calls. Do NOT create a new axios instance.
**Warning signs:** 404 errors on `/api/v1/settings/*` endpoints.

### Pitfall 3: E2E Tests Need Live Backends
**What goes wrong:** Settings→behavior E2E tests can't work with mocks because they need actual LLM provider metadata in responses.
**Why it happens:** The test (SC-03) requires triggering KG processing and checking response metadata for `provider: "openrouter"` — mocks can't simulate this.
**How to avoid:** Use `AURA_TEST_MODE=true` with real backend processes. Mock only the LLM calls themselves (not the settings API). Or make SC-03 a skipped test that documents live-credentials requirement.
**Warning signs:** Test passes with mocks but fails with real backend.

### Pitfall 4: Redis Recovery Test Timing
**What goes wrong:** SC-04 (Redis stop/start) test races against cache TTL (30s error cache, 300s normal cache).
**Why it happens:** After Redis restart, `get_default_sync()` returns cached error sentinel until `_ERROR_CACHE_TTL` (30s) expires. The test expects values to resume within 30 seconds.
**How to avoid:** Call `clear_defaults_cache()` from `settings_store.py` in the test's Redis-restart handler, or wait the full 30s after restart. The cache fix from Phase 14 guarantees 30s error TTL (not 5min).
**Warning signs:** Test intermittent failure on CI.

### Pitfall 5: `sonner` Toast Dependency in AURA-CHAT
**What goes wrong:** `sonner` is used in NOTES-MANAGER's `useSettingsApi.ts` but may not be installed in AURA-CHAT.
**Why it happens:** AURA-CHAT uses `react-hot-toast` or no toast library currently.
**How to avoid:** Check `AURA-CHAT/client/package.json` for `sonner`. Install if missing. Or use a different toast approach (e.g., the existing notification pattern in CHAT).
**Warning signs:** Import error on `sonner` in AURA-CHAT client build.

---

## Code Examples

### UseCase Type Extension (NOTES-MANAGER)
```typescript
// Source: AURA-NOTES-MANAGER/frontend/src/types/settings.ts
// BEFORE:
export type UseCase = 'chat' | 'embeddings' | 'entity_extraction';
// AFTER:
export type UseCase = 'chat' | 'embeddings' | 'entity_extraction' | 'gatekeeper' | 'relationship_extraction';
```

### Settings API Hooks Pattern
```typescript
// Source: AURA-NOTES-MANAGER/frontend/src/features/settings/hooks/useSettingsApi.ts
export const useDefaults = () => {
    return useQuery({
        queryKey: settingsKeys.defaults(),
        queryFn: async () => {
            return await fetchApi<Record<string, DefaultModelSetting>>('/v1/settings/defaults');
        },
        staleTime: 2 * 60 * 1000,
    });
};
```

### AURA-CHAT Axios Pattern for API Calls
```typescript
// Source: AURA-CHAT/client/src/lib/api.ts
// Use existing axios instance with auth interceptor
import api from '@/lib/api';
export const fetchSettingsDefaults = async () => {
    const response = await api.get('/api/v1/settings/defaults');
    return response.data;
};
```

### AST Audit (existing)
```python
# Source: tests/test_no_direct_imports.py
# Already covers forbidden imports: vertexai, google.generativeai, google.genai, openai, google.cloud.aiplatform, google.auth
# SCAN_DIRS covers AURA-CHAT/backend, AURA-CHAT/server, AURA-NOTES-MANAGER/api, AURA-NOTES-MANAGER/services
# Run: python -m pytest tests/test_no_direct_imports.py -v
```

### Playwright Mock Pattern
```typescript
// Source: AURA-CHAT/client/e2e/chat.spec.ts
await page.route('**/api/v1/settings/defaults', async (route) => {
    await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
            chat: { provider: 'vertex_ai', model: 'gemini-2.5-flash-lite' },
            embeddings: { provider: 'vertex_ai', model: 'text-embedding-004' },
            entity_extraction: { provider: 'vertex_ai', model: 'gemini-2.5-flash-lite' },
            gatekeeper: { provider: 'vertex_ai', model: 'gemini-2.5-flash-lite' },
            relationship_extraction: { provider: 'vertex_ai', model: 'gemini-2.5-flash-lite' },
        }),
    });
});
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded env vars per consumer | `resolve_use_case_config()` with 3-step fallback | Phase 14 | Runtime config changes without restart |
| Module-level config reads | Per-call SettingsStore resolution | Phases 15-16 | Config changes take effect immediately |
| Direct Vertex SDK calls | ModelRouter abstraction | Phase 16 (summarizer) | Multi-provider support |
| 5-min zombie-None cache | 30s error TTL + shorter normal TTL | Phase 14 | Redis recovery within 30s |
| No AST enforcement | `test_no_direct_imports.py` CI gate | Phase 10 | Prevents SDK bypass |

**Deprecated/outdated:**
- `LLM_ENTITY_EXTRACTION_MODEL` env var as primary config: superseded by SettingsStore; env var is now fallback only
- Blanket OpenRouter skip in gatekeeper: removed in Phase 15
- Import-time `get_default_sync()` in consumer `__init__`: removed in Phase 16

---

## Open Questions

1. **AURA-CHAT admin route access strategy**
   - What we know: `RoleProtectedRoute` blocks all admin users from AURA-CHAT
   - What's unclear: Whether admins should access settings via CHAT's own UI or always use NOTES-MANAGER's settings (which controls both apps)
   - Recommendation: Add a conditional admin check in `RoleProtectedRoute` that allows `/settings` route for admins. Both apps' settings routers hit the same Redis backend, so settings in either app control both apps.

2. **E2E test environment for Redis control**
   - What we know: SC-04 needs to stop/start Redis and verify consumer behavior
   - What's unclear: Whether Playwright can control Redis process (it's a browser test framework)
   - Recommendation: SC-04 should be a pytest integration test (Python subprocess control) rather than a Playwright browser test. Or use Docker-based Redis with Playwright API testing.

3. **`sonner` availability in AURA-CHAT**
   - What we know: NOTES-MANAGER uses `sonner` for toast notifications in settings hooks
   - What's unclear: Whether AURA-CHAT already has `sonner` installed
   - Recommendation: Check `package.json` first; if missing, install it. It's a lightweight toast library that's already proven in NOTES-MANAGER.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Playwright 1.49+ (E2E), Vitest (frontend unit), pytest (backend) |
| Config file | `AURA-CHAT/client/playwright.config.ts`, `AURA-NOTES-MANAGER/frontend/playwright.config.ts` |
| Quick run command | `npx playwright test --grep "settings"` |
| Full suite command | `npm run test:e2e` (both apps) + `python -m pytest tests/` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-01 | Gatekeeper row visible in NOTES settings | Playwright E2E | `npx playwright test --grep "gatekeeper"` | ❌ Wave 0 |
| API-02 | Relationship extraction row visible | Playwright E2E | `npx playwright test --grep "relationship"` | ❌ Wave 0 |
| SC-01 | All 5 use case rows visible in CHAT settings | Playwright E2E | `npx playwright test --grep "use case rows"` | ❌ Wave 0 |
| SC-02 | Gatekeeper picker functional | Playwright E2E | `npx playwright test --grep "gatekeeper picker"` | ❌ Wave 0 |
| SC-03 | Settings → behavior propagation | Playwright E2E (live) | `npx playwright test --grep "settings.*behavior"` | ❌ Wave 0 |
| SC-04 | Redis fallback and recovery | pytest integration | `python -m pytest tests/test_redis_fallback.py` | ❌ Wave 0 |
| SC-05 | Full test suites pass | Existing | `npm run test` + `python -m pytest tests/` | ✅ |
| AST | No direct SDK imports | pytest | `python -m pytest tests/test_no_direct_imports.py` | ✅ |

### Sampling Rate
- **Per task commit:** `npm run build` (type check) + `npm run lint`
- **Per wave merge:** `npx playwright test` (relevant specs) + `python -m pytest tests/test_no_direct_imports.py`
- **Phase gate:** Full suites green — `npm run test` + `npm run test:e2e` in both apps + `python -m pytest tests/`

### Wave 0 Gaps
- [ ] `AURA-CHAT/client/src/types/settings.ts` — UseCase, ProviderType, ModelInfo types
- [ ] `AURA-CHAT/client/src/features/settings/` — Full feature directory (api, hooks, components, page)
- [ ] `AURA-CHAT/client/src/App.tsx` — `/settings` route registration
- [ ] `AURA-NOTES-MANAGER/frontend/src/types/settings.ts` — Extended UseCase type
- [ ] `AURA-NOTES-MANAGER/frontend/e2e/settings.spec.ts` — NOTES settings E2E tests
- [ ] `AURA-CHAT/client/e2e/settings.spec.ts` — CHAT settings E2E tests
- [ ] `tests/test_redis_fallback.py` or integration test for SC-04 (if separate from Playwright)

---

## Sources

### Primary (HIGH confidence)
- `AURA-NOTES-MANAGER/frontend/src/pages/SettingsPage.tsx` — Complete settings page to mirror
- `AURA-NOTES-MANAGER/frontend/src/features/settings/components/DefaultModelSection.tsx` — USE_CASES array pattern
- `AURA-NOTES-MANAGER/frontend/src/features/settings/hooks/useSettingsApi.ts` — TanStack Query hooks pattern
- `AURA-NOTES-MANAGER/frontend/src/features/settings/hooks/useModelList.ts` — Model grouping utility
- `AURA-NOTES-MANAGER/frontend/src/features/settings/components/HierarchicalModelPicker.tsx` — Reusable picker component
- `AURA-NOTES-MANAGER/frontend/src/types/settings.ts` — Type definitions to extend
- `AURA-NOTES-MANAGER/api/routers/settings.py` — Backend settings endpoints (already supports all 6 use cases)
- `AURA-CHAT/server/routers/settings.py` — Identical backend endpoints
- `shared/model_router/src/model_router/settings_store.py` — Config resolution with fallback chain
- `tests/test_no_direct_imports.py` — Existing AST audit
- `.planning/phases/17-frontend-cross-app-validation/17-UI-SPEC.md` — Approved design contract

### Secondary (MEDIUM confidence)
- `AURA-CHAT/client/src/lib/api.ts` — Axios client with auth interceptor pattern
- `AURA-CHAT/client/src/components/RoleProtectedRoute.tsx` — Admin routing constraint
- `AURA-CHAT/client/src/App.tsx` — Current route structure
- `AURA-CHAT/client/e2e/chat.spec.ts` — Playwright mock pattern
- `AURA-NOTES-MANAGER/frontend/e2e/fixtures.ts` — E2E fixture infrastructure
- `AURA-NOTES-MANAGER/frontend/playwright.config.ts` — Sequential E2E config
- `AURA-CHAT/client/playwright.config.ts` — Parallel E2E config

### Tertiary (LOW confidence — needs validation)
- `sonner` availability in AURA-CHAT client — needs `package.json` check
- Redis process control in Playwright — architectural feasibility unclear
- AURA-CHAT `/settings` route access for admins — needs `RoleProtectedRoute` modification decision

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Both apps' dependencies well-documented in AGENTS.md
- Architecture: HIGH — UI-SPEC.md provides complete design contract; NOTES-MANAGER code is the template
- Pitfalls: HIGH — Admin route blocking is a clear known issue documented in code
- E2E strategy: MEDIUM — Redis control test architecture needs validation
- CHAT settings build: HIGH — Exact mirror of NOTES-MANAGER with minor API client differences

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (stable stack; React/Vite/Playwright versions locked)
