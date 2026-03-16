# Phase 11: Frontend Provider Settings + Model Selection UI - Research

**Researched:** 2026-03-11
**Domain:** React frontend UI (React 19 + React 18), Zustand state management, TanStack Query data fetching, hierarchical model selection
**Confidence:** HIGH

## Summary

Phase 11 builds the frontend UI layer for the multi-provider LLM architecture established in Phases 8-10. The backend APIs already exist: `/api/v1/settings/defaults`, `/api/v1/settings/models`, `/api/v1/settings/providers/{provider}/models`, and API key management endpoints. The phase requires three major frontend deliverables: (1) a provider settings page for admin configuration, (2) a hierarchical model selector for the settings page (2-level for Vertex AI/Ollama, 3-level for OpenRouter), and (3) an inline compact model picker in the chat interface for mid-session model switching. Components are built in AURA-CHAT (React 19) first, then adapted for AURA-NOTES-MANAGER (React 18).

The existing codebase already has patterns for all major concerns: Zustand stores (`useAuthStore`), TanStack Query hooks with query key factories (`sessionKeys`), a searchable `Dropdown` component with Framer Motion animations, feature-based folder structure, and Vitest testing with RTL. The main technical challenge is the state synchronization between Zustand (client-side model selection) and TanStack Query (server-side model lists), plus the hierarchical grouping of OpenRouter models by vendor prefix (e.g., `anthropic/claude-3.5-sonnet` → provider: OpenRouter, vendor: Anthropic, model: Claude 3.5 Sonnet).

**Primary recommendation:** Build a new `src/features/settings/` feature module with provider settings components and hooks, extend the existing chat interface with an inline model picker, and use a Zustand store for model selection state that persists to sessionStorage (keyed by session ID) for CONFIG-02 session persistence.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| UI-01 | Provider selection uses a hierarchical UI: 2-level for Vertex AI, 3-level for OpenRouter (provider > vendor > model) with search/filter | Existing `Dropdown` component has search capability; extend with grouped/nested variant. OpenRouter model names use `vendor/model` format (e.g., `anthropic/claude-3.5-sonnet`) enabling client-side vendor extraction. Backend `/api/v1/settings/models` returns flat `ModelInfo[]` with `name`, `provider`, `display_name` — frontend groups by provider and vendor. |
| UI-02 | Chat interface includes an inline compact model picker for quick mid-session model switching | ChatPage already has model selection via `Dropdown` in the input area controls bar. Replace with new hierarchical picker that groups models and supports search. Compact footprint needed — current model dropdown is `max-w-[160px]`. |
| CONFIG-02 | Student can select a different chat model for their study session that persists for the session duration | Current model state lives in `configState` useState (ChatPage line 80). Move to a Zustand store with sessionStorage persistence keyed by session ID. Zustand 5.0's `persist` middleware supports `sessionStorage` natively. On session resume, read persisted model selection. |
</phase_requirements>

## Standard Stack

### Core (Already Installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 19.2.0 (CHAT) / 18.3.1 (NOTES) | UI framework | Already in both apps |
| Zustand | 5.0.11 (CHAT) / 5.0.2 (NOTES) | Client state management | Already used for auth store; ideal for model selection persistence |
| TanStack Query | 5.90.15 (CHAT) / 5.62.0 (NOTES) | Server state (model lists, settings) | Already used for health checks, chat config, sessions |
| Framer Motion | 12.34.3 (CHAT) / 12.24.12 (NOTES) | Animations | Already used in Dropdown component |
| Lucide React | 0.562.0 (CHAT) / 0.468.0 (NOTES) | Icons | Already used throughout both apps |
| Vitest | 3.2.4 (both) | Unit testing | Already configured in both apps |
| Testing Library | 16.3.1 (both) | Component testing | Already used for SettingsPage tests, ChatPage tests |
| Axios | 1.13.2 (CHAT only) | HTTP client | AURA-CHAT uses axios; AURA-NOTES-MANAGER uses native fetch |

### Supporting (Already Available)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| clsx + tailwind-merge | via `cn()` utility | Conditional CSS classes | All component styling |
| react-router-dom | 7.11.0 (CHAT) / 7.1.0 (NOTES) | Routing | Settings page navigation |
| sonner | 2.0.7 (NOTES only) | Toast notifications | Success/error feedback in NOTES settings |

### Nothing New Needed
No new npm dependencies are required. All UI patterns can be built with existing libraries. The hierarchical selector is a composition of existing patterns (search input, grouped list, Framer Motion animations).

## Architecture Patterns

### Recommended Project Structure

**AURA-CHAT:**
```
client/src/
├── features/
│   └── settings/
│       ├── SettingsPage.tsx              # Existing — extend with provider section
│       ├── SettingsPage.test.tsx          # Existing — extend tests
│       ├── components/
│       │   ├── ProviderSettingsSection.tsx  # Provider config cards
│       │   ├── DefaultModelSection.tsx      # Use-case default model pickers
│       │   ├── ApiKeyManager.tsx            # API key store/validate/delete UI
│       │   └── HierarchicalModelPicker.tsx  # Shared hierarchical model selector
│       └── hooks/
│           ├── useSettingsApi.ts            # TanStack Query hooks for settings endpoints
│           └── useModelList.ts             # Model listing + grouping logic
├── features/
│   └── chat/
│       └── components/
│           └── InlineModelPicker.tsx        # Compact chat model picker
├── stores/
│   ├── useAuthStore.ts                     # Existing
│   └── useModelStore.ts                    # NEW: model selection + session persistence
└── types/
    └── settings.ts                         # NEW: settings API types
```

**AURA-NOTES-MANAGER (copy + adapt):**
```
frontend/src/
├── pages/
│   └── SettingsPage.tsx                    # NEW: settings page (separate from AdminDashboard)
├── features/
│   └── settings/
│       ├── components/
│       │   ├── ProviderSettingsSection.tsx  # Adapted from CHAT
│       │   ├── DefaultModelSection.tsx      # Adapted from CHAT
│       │   ├── ApiKeyManager.tsx            # Adapted from CHAT
│       │   └── HierarchicalModelPicker.tsx  # Adapted from CHAT
│       └── hooks/
│           ├── useSettingsApi.ts            # Uses fetchApi instead of axios
│           └── useModelList.ts             # Identical to CHAT version
├── stores/
│   ├── useAuthStore.ts                     # Existing
│   └── index.ts                            # Existing
└── types/
    └── settings.ts                         # Identical to CHAT version
```

### Pattern 1: Query Key Factory for Settings

**What:** Centralized query keys for consistent cache invalidation, following the established `sessionKeys` pattern.
**When to use:** All TanStack Query hooks for settings data.

```typescript
// features/settings/hooks/useSettingsApi.ts
export const settingsKeys = {
    all: ['settings'] as const,
    defaults: () => [...settingsKeys.all, 'defaults'] as const,
    models: () => [...settingsKeys.all, 'models'] as const,
    providerModels: (provider: string) => [...settingsKeys.models(), provider] as const,
    apiKey: (provider: string) => [...settingsKeys.all, 'apiKey', provider] as const,
};
```

### Pattern 2: Model Grouping by Provider and Vendor

**What:** Transform flat `ModelInfo[]` from the API into a hierarchical tree structure for the UI.
**When to use:** Both the settings page model picker and the inline chat model picker.

```typescript
// types/settings.ts
export interface ModelInfo {
    name: string;           // e.g., 'anthropic/claude-3.5-sonnet' or 'gemini-2.5-flash'
    provider: string;       // 'vertex_ai' | 'openrouter' | 'ollama'
    display_name: string | null;
}

export interface ModelGroup {
    provider: string;
    providerLabel: string;  // 'Vertex AI' | 'OpenRouter' | 'Ollama'
    vendors: VendorGroup[]; // Only for OpenRouter; others have a single implicit vendor
}

export interface VendorGroup {
    vendor: string;         // 'anthropic' | 'google' | 'openai' | etc.
    vendorLabel: string;    // 'Anthropic' | 'Google' | 'OpenAI'
    models: ModelInfo[];
}

// Pure function for grouping — no hooks needed, easily testable
export function groupModelsByProvider(models: ModelInfo[]): ModelGroup[] {
    // Group by provider
    // For OpenRouter: extract vendor from model name (split on '/')
    // For Vertex AI/Ollama: single vendor group
}
```

### Pattern 3: Zustand Model Selection Store with Session Persistence

**What:** A Zustand store that tracks the currently selected chat model per session, persisted to sessionStorage.
**When to use:** AURA-CHAT only (CONFIG-02 requirement).

```typescript
// stores/useModelStore.ts
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface ModelSelectionState {
    // Map of sessionId → selected model name
    sessionModels: Record<string, string>;
    
    // Actions
    setSessionModel: (sessionId: string, model: string) => void;
    getSessionModel: (sessionId: string) => string | undefined;
    clearSessionModel: (sessionId: string) => void;
}

export const useModelStore = create<ModelSelectionState>()(
    persist(
        (set, get) => ({
            sessionModels: {},
            setSessionModel: (sessionId, model) =>
                set((state) => ({
                    sessionModels: { ...state.sessionModels, [sessionId]: model },
                })),
            getSessionModel: (sessionId) => get().sessionModels[sessionId],
            clearSessionModel: (sessionId) =>
                set((state) => {
                    const { [sessionId]: _, ...rest } = state.sessionModels;
                    return { sessionModels: rest };
                }),
        }),
        {
            name: 'aura-model-selection',
            storage: createJSONStorage(() => sessionStorage),
        }
    )
);
```

### Pattern 4: Cache Invalidation on Provider Change

**What:** When admin changes provider config or API key, invalidate the cached model list.
**When to use:** Settings mutation success handlers.

```typescript
// In settings mutation hooks
const queryClient = useQueryClient();

const storeApiKeyMutation = useMutation({
    mutationFn: (args: { provider: string; apiKey: string }) =>
        storeApiKey(args.provider, args.apiKey),
    onSuccess: (_data, variables) => {
        // Invalidate model lists for this provider (may have unlocked new models)
        queryClient.invalidateQueries({ queryKey: settingsKeys.providerModels(variables.provider) });
        queryClient.invalidateQueries({ queryKey: settingsKeys.models() });
    },
});
```

### Pattern 5: React Version Adaptation (CHAT → NOTES)

**What:** Components built for React 19 in AURA-CHAT adapted for React 18 in AURA-NOTES-MANAGER.
**When to use:** All components that get copied to NOTES.

Key differences to handle:
- **API client:** CHAT uses axios (`api.get()`), NOTES uses native fetch (`fetchApi<T>()`). Abstract API calls into hook layer so components are identical.
- **Toast notifications:** CHAT has no toast system, NOTES uses `sonner`. Add `toast.success()` / `toast.error()` in NOTES versions.
- **No QueryClientProvider in App.tsx for NOTES:** Already present in `main.tsx` — this is fine.
- **Route structure:** CHAT uses `<MainLayout>` wrapper, NOTES uses direct route rendering. NOTES needs a new `/settings` route in App.tsx.

### Anti-Patterns to Avoid

- **Don't mix server and client state:** Model lists from the API go in TanStack Query. User's model selection goes in Zustand. Never store API response data in Zustand.
- **Don't use `any` type:** The ModelInfo response from the API must be properly typed. Use the TypeScript interface matching the backend `ModelInfo` Pydantic model.
- **Don't put grouping logic in components:** The `groupModelsByProvider()` function should be a pure utility, easily testable without rendering components.
- **Don't hand-roll search/filter in JSX:** Extract search/filter logic into a `useMemo` or custom hook, keeping render functions clean.
- **Don't use default exports:** Project enforces named exports only (Google TypeScript Style Guide).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dropdown with search | Custom select element | Extend existing `Dropdown` component or compose new variant | Existing component already handles search, keyboard nav, click-outside, animations |
| CSS class composition | Manual className strings | `cn()` utility (clsx + tailwind-merge) | Already used everywhere; prevents class conflicts |
| HTTP requests | Raw fetch with manual auth | Existing `api` axios instance (CHAT) or `fetchApi` (NOTES) | Auth token injection, error handling already configured |
| Server state caching | Manual useState + useEffect | TanStack Query hooks | Stale-while-revalidate, cache invalidation, loading/error states |
| Client state persistence | Manual localStorage/sessionStorage | Zustand `persist` middleware | Handles serialization, hydration, storage selection automatically |
| Animation patterns | CSS transitions | Framer Motion (AnimatePresence, motion) | Already used in Dropdown; consistent animation language |

## Common Pitfalls

### Pitfall 1: Stale Model Lists After Provider Config Change

**What goes wrong:** Admin stores a new API key, but the model list still shows the old cached data.
**Why it happens:** TanStack Query's staleTime prevents automatic refetch. The settings mutations don't invalidate the model queries.
**How to avoid:** In every settings mutation's `onSuccess`, call `queryClient.invalidateQueries({ queryKey: settingsKeys.models() })`. This is the standard TanStack Query pattern.
**Warning signs:** Model list shows empty or stale data after API key update.

### Pitfall 2: React 18 vs React 19 Incompatibilities

**What goes wrong:** Components copied from AURA-CHAT (React 19) to AURA-NOTES-MANAGER (React 18) break.
**Why it happens:** React 19 has different typing for children props, new `use()` hook, ref forwarding changes.
**How to avoid:** Stick to React 18-compatible patterns in shared components. Avoid `use()`, `useFormStatus()`, and other React 19-only APIs. Test in NOTES after copying.
**Warning signs:** Type errors on `children?: ReactNode`, runtime errors from new hooks.

### Pitfall 3: OpenRouter Vendor Extraction Edge Cases

**What goes wrong:** Model grouping fails for models with unexpected name formats.
**Why it happens:** OpenRouter model names are `vendor/model-name` format (e.g., `anthropic/claude-3.5-sonnet`), but edge cases exist.
**How to avoid:** Defensive parsing: split on first `/` only. If no `/` found, use the model name as-is with provider as the "vendor". The curated prefixes from the backend are: `anthropic/`, `google/`, `openai/`, `deepseek/`, `meta-llama/`.
**Warning signs:** Models appearing ungrouped or in wrong vendor category.

### Pitfall 4: Session Model Persistence Memory Leak

**What goes wrong:** `sessionModels` map in Zustand grows unbounded as users create new sessions.
**Why it happens:** Old session model selections are never cleaned up.
**How to avoid:** The `sessionStorage` strategy already handles this — sessionStorage is cleared when the browser tab closes. For within-session cleanup, clear entries when sessions are deleted.
**Warning signs:** sessionStorage growing large over extended use.

### Pitfall 5: Zustand/TanStack Query State Sync Race

**What goes wrong:** User selects a model, but the model no longer exists in the provider's model list (e.g., provider removed).
**Why it happens:** Client-side selection (Zustand) and server model list (TanStack Query) can diverge.
**How to avoid:** When rendering the model picker, validate that the selected model exists in the current model list. If not, fall back to the server's default model. Always show the effective model, never a stale selection.
**Warning signs:** Selected model shows as "Unknown" or requests fail with model-unavailable errors.

### Pitfall 6: Missing Keyboard Navigation in Custom Pickers

**What goes wrong:** Hierarchical model picker is not keyboard-accessible.
**Why it happens:** Custom dropdown patterns often miss arrow key navigation, focus management.
**How to avoid:** Follow the existing `Dropdown` component's keyboard handling (Escape to close). Add arrow key navigation for nested groups. Ensure focus ring visibility (Cyber Yellow per product guidelines, WCAG 2.1 AA).
**Warning signs:** Users can't navigate models without a mouse; accessibility audit fails.

## Code Examples

### Example 1: Settings API Types (TypeScript)

```typescript
// types/settings.ts — Frontend types matching backend API responses

export type ProviderType = 'vertex_ai' | 'openrouter' | 'ollama';
export type UseCase = 'chat' | 'embeddings' | 'entity_extraction';

export interface ModelInfo {
    name: string;
    provider: ProviderType;
    display_name: string | null;
}

export interface DefaultModelSetting {
    provider: string;
    model: string;
}

export interface ApiKeyStatus {
    provider: string;
    masked_key: string;
    valid: boolean | null; // null = validation not applicable (Ollama)
}
```

### Example 2: TanStack Query Hooks for Settings (AURA-CHAT)

```typescript
// features/settings/hooks/useSettingsApi.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api'; // axios instance

export const settingsKeys = {
    all: ['settings'] as const,
    defaults: () => [...settingsKeys.all, 'defaults'] as const,
    models: () => [...settingsKeys.all, 'models'] as const,
    providerModels: (provider: string) => [...settingsKeys.models(), provider] as const,
    apiKey: (provider: string) => [...settingsKeys.all, 'apiKey', provider] as const,
};

export function useAllModels() {
    return useQuery({
        queryKey: settingsKeys.models(),
        queryFn: async (): Promise<ModelInfo[]> => {
            const response = await api.get('/api/v1/settings/models');
            return response.data;
        },
        staleTime: 5 * 60 * 1000, // 5 minutes (backend caches with TTL too)
    });
}

export function useDefaults() {
    return useQuery({
        queryKey: settingsKeys.defaults(),
        queryFn: async () => {
            const response = await api.get('/api/v1/settings/defaults');
            return response.data;
        },
        staleTime: 2 * 60 * 1000,
    });
}
```

### Example 3: Model Grouping Pure Function

```typescript
// features/settings/hooks/useModelList.ts
import { useMemo } from 'react';
import type { ModelInfo, ModelGroup, VendorGroup } from '@/types/settings';

const PROVIDER_LABELS: Record<string, string> = {
    vertex_ai: 'Vertex AI',
    openrouter: 'OpenRouter',
    ollama: 'Ollama',
};

function capitalizeVendor(vendor: string): string {
    const known: Record<string, string> = {
        anthropic: 'Anthropic',
        google: 'Google',
        openai: 'OpenAI',
        deepseek: 'DeepSeek',
        'meta-llama': 'Meta Llama',
    };
    return known[vendor] ?? vendor.charAt(0).toUpperCase() + vendor.slice(1);
}

export function groupModelsByProvider(models: ModelInfo[]): ModelGroup[] {
    const providerMap = new Map<string, ModelInfo[]>();
    
    for (const model of models) {
        const list = providerMap.get(model.provider) ?? [];
        list.push(model);
        providerMap.set(model.provider, list);
    }
    
    return Array.from(providerMap.entries()).map(([provider, providerModels]) => {
        const vendorMap = new Map<string, ModelInfo[]>();
        
        for (const model of providerModels) {
            let vendor: string;
            if (provider === 'openrouter' && model.name.includes('/')) {
                vendor = model.name.split('/')[0];
            } else {
                vendor = provider; // Vertex AI / Ollama: vendor = provider
            }
            const list = vendorMap.get(vendor) ?? [];
            list.push(model);
            vendorMap.set(vendor, list);
        }
        
        const vendors: VendorGroup[] = Array.from(vendorMap.entries()).map(
            ([vendor, vendorModels]) => ({
                vendor,
                vendorLabel: capitalizeVendor(vendor),
                models: vendorModels.sort((a, b) =>
                    (a.display_name ?? a.name).localeCompare(b.display_name ?? b.name)
                ),
            })
        );
        
        return {
            provider,
            providerLabel: PROVIDER_LABELS[provider] ?? provider,
            vendors: vendors.sort((a, b) => a.vendorLabel.localeCompare(b.vendorLabel)),
        };
    });
}
```

### Example 4: Inline Model Picker Trigger Button (Compact)

```typescript
// Compact trigger for inline chat picker (replaces existing model Dropdown in ChatPage)
// Sits in the chat input controls bar alongside mode selector and thinking toggle

<button
    onClick={() => setPickerOpen(!pickerOpen)}
    className={cn(
        'flex items-center gap-1.5 px-2 min-h-9 text-[11px] font-bold tracking-wider rounded-md border transition-all',
        pickerOpen
            ? 'bg-primary/20 text-primary border-primary/50'
            : 'text-muted-foreground hover:text-primary border-transparent hover:bg-primary/10'
    )}
>
    <Cpu className="w-3.5 h-3.5 shrink-0" />
    <span className="truncate max-w-[120px] uppercase">
        {formatModelLabel(selectedModel)}
    </span>
    <ChevronDown className={cn('w-3 h-3 transition-transform', pickerOpen && 'rotate-180')} />
</button>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hard-coded Gemini model list in `getChatConfig()` | Dynamic model discovery via `/api/v1/settings/models` | Phase 10 (2026-03-10) | Frontend must fetch models instead of using static config |
| Model selection in component useState | Zustand store with persistence middleware | Phase 11 (this phase) | Enables CONFIG-02 session persistence |
| Flat model dropdown | Hierarchical grouped picker | Phase 11 (this phase) | Supports 200+ OpenRouter models organized by vendor |

**Existing model selection to replace:**
- `ChatPage.tsx` line 80: `model: ''` in `configState` useState — replace with Zustand store read
- `ChatPage.tsx` line 98-102: `queryKey: ['chatConfig']` for `getChatConfig` — supplement with `useAllModels()` hook
- `ChatPage.tsx` lines 573-586: flat `Dropdown` for model selection — replace with `InlineModelPicker`
- `lib/utils.ts` lines 79-98: `formatModelLabel()` with hard-coded Gemini map — extend to use `display_name` from API

## Open Questions

1. **Admin vs Student Access Control**
   - What we know: Backend settings endpoints exist without role-based access control differentiation. The UI needs both an admin settings page and a student model picker.
   - What's unclear: Should the admin settings page (provider config, API keys, defaults) be gated behind a role check in the frontend? The existing `SettingsPage` in AURA-CHAT has no role restriction.
   - Recommendation: Gate admin-only sections (API key management, default model config) behind `useAuthStore().isStaff()`. Students see only the model picker. The backend should also add role checks but that's out of scope for Phase 11 (frontend-only phase).

2. **Processing Model Selection for AURA-NOTES-MANAGER**
   - What we know: NOTES uses models for KG processing (entity extraction, embeddings). The settings page should let admins set default models for these use cases.
   - What's unclear: Does NOTES need a per-operation model picker inline (like CHAT's inline picker), or just the settings page defaults?
   - Recommendation: NOTES only needs the settings page with use-case defaults (chat, embeddings, entity_extraction). No inline picker needed for NOTES — the admin sets processing model defaults once.

3. **`formatModelLabel()` Backward Compatibility**
   - What we know: The current function has a hard-coded map for 4 Gemini models.
   - What's unclear: Should the function be removed entirely in favor of `display_name` from the API?
   - Recommendation: Keep `formatModelLabel()` as a fallback. Use `display_name` from the API when available, fall back to `formatModelLabel()` for models without display names.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 3.2.4 + React Testing Library 16.3.1 |
| Config file | `AURA-CHAT/client/vitest.config.ts` |
| Quick run command | `cd AURA-CHAT/client && npm run test:run -- --reporter=verbose` |
| Full suite command | `cd AURA-CHAT/client && npm run test:run` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UI-01 | Hierarchical model picker renders 2-level (Vertex AI) and 3-level (OpenRouter) groups | unit | `cd AURA-CHAT/client && npx vitest run src/features/settings/components/HierarchicalModelPicker.test.tsx` | ❌ Wave 0 |
| UI-01 | Model grouping function correctly groups models by provider and vendor | unit | `cd AURA-CHAT/client && npx vitest run src/features/settings/hooks/useModelList.test.ts` | ❌ Wave 0 |
| UI-01 | Search/filter narrows displayed models | unit | `cd AURA-CHAT/client && npx vitest run src/features/settings/components/HierarchicalModelPicker.test.tsx` | ❌ Wave 0 |
| UI-02 | Inline model picker renders in chat input area | unit | `cd AURA-CHAT/client && npx vitest run src/features/chat/components/InlineModelPicker.test.tsx` | ❌ Wave 0 |
| UI-02 | Model switch mid-session updates selected model | unit | `cd AURA-CHAT/client && npx vitest run src/features/chat/components/InlineModelPicker.test.tsx` | ❌ Wave 0 |
| CONFIG-02 | Model selection persists to sessionStorage and restores on session resume | unit | `cd AURA-CHAT/client && npx vitest run src/stores/useModelStore.test.ts` | ❌ Wave 0 |
| CONFIG-02 | Settings API hooks fetch and cache model data | unit | `cd AURA-CHAT/client && npx vitest run src/features/settings/hooks/useSettingsApi.test.ts` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd AURA-CHAT/client && npx vitest run --reporter=verbose`
- **Per wave merge:** `cd AURA-CHAT/client && npm run test:run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `src/types/settings.ts` — TypeScript types for settings API responses
- [ ] `src/stores/useModelStore.ts` + `src/stores/useModelStore.test.ts` — Zustand model selection store
- [ ] `src/features/settings/hooks/useSettingsApi.ts` + test — TanStack Query hooks
- [ ] `src/features/settings/hooks/useModelList.ts` + test — Model grouping logic
- [ ] `src/features/settings/components/HierarchicalModelPicker.tsx` + test — Hierarchical picker
- [ ] `src/features/chat/components/InlineModelPicker.tsx` + test — Compact chat picker
- [ ] NOTES equivalents (adapted copies)

## Sources

### Primary (HIGH confidence)
- **Codebase inspection:** Direct reading of all referenced source files in AURA-CHAT and AURA-NOTES-MANAGER
- **Phase 10 summaries:** 10-01, 10-02, 10-03, 10-04, 10-06 — confirmed backend API surface
- **Backend settings router:** `AURA-CHAT/server/routers/settings.py` — confirmed all endpoint paths and response shapes
- **Shared model_router types:** `shared/model_router/src/model_router/types.py` — confirmed `ModelInfo` schema (name, provider, display_name)
- **OpenRouter provider:** `shared/model_router/src/model_router/providers/openrouter.py` — confirmed curated vendor prefixes and model name format

### Secondary (MEDIUM confidence)
- **Zustand 5.0 persist middleware:** Based on Zustand 5.x API (already installed, confirmed from package.json)
- **TanStack Query 5 patterns:** Based on existing codebase patterns (sessionKeys factory) and TanStack Query 5 API

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already installed and actively used in both apps
- Architecture: HIGH — following established patterns from existing features (study-sessions, chat, modules)
- Pitfalls: HIGH — identified from direct codebase analysis and known React 18/19 differences
- API surface: HIGH — backend endpoints directly read from source code

**Research date:** 2026-03-11
**Valid until:** 2026-04-10 (stable — no external dependencies changing)
