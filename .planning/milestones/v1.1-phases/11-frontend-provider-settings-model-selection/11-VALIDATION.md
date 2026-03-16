# Phase 11: Frontend Provider Settings + Model Selection UI — Validation

**Generated:** 2026-03-11
**Phase:** 11-frontend-provider-settings-model-selection
**Requirements:** UI-01, UI-02, CONFIG-02

## Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest 3.2.4 + React Testing Library 16.3.1 |
| Config file | `AURA-CHAT/client/vitest.config.ts` |
| Quick run command | `cd AURA-CHAT/client && npm run test:run -- --reporter=verbose` |
| Full suite command | `cd AURA-CHAT/client && npm run test:run` |

## Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UI-01 | Hierarchical model picker renders 2-level (Vertex AI) and 3-level (OpenRouter) groups | unit | `cd AURA-CHAT/client && npx vitest run src/features/settings/components/HierarchicalModelPicker.test.tsx` | ❌ Wave 0 |
| UI-01 | Model grouping function correctly groups models by provider and vendor | unit | `cd AURA-CHAT/client && npx vitest run src/features/settings/hooks/useModelList.test.ts` | ❌ Wave 0 |
| UI-01 | Search/filter narrows displayed models | unit | `cd AURA-CHAT/client && npx vitest run src/features/settings/components/HierarchicalModelPicker.test.tsx` | ❌ Wave 0 |
| UI-02 | Inline model picker renders in chat input area | unit | `cd AURA-CHAT/client && npx vitest run src/features/chat/components/InlineModelPicker.test.tsx` | ❌ Wave 0 |
| UI-02 | Model switch mid-session updates selected model | unit | `cd AURA-CHAT/client && npx vitest run src/features/chat/components/InlineModelPicker.test.tsx` | ❌ Wave 0 |
| CONFIG-02 | Model selection persists to sessionStorage and restores on session resume | unit | `cd AURA-CHAT/client && npx vitest run src/stores/useModelStore.test.ts` | ❌ Wave 0 |
| CONFIG-02 | Settings API hooks fetch and cache model data | unit | `cd AURA-CHAT/client && npx vitest run src/features/settings/hooks/useSettingsApi.test.ts` | ❌ Wave 0 |

## Sampling Rate

- **Per task commit:** `cd AURA-CHAT/client && npx vitest run --reporter=verbose`
- **Per wave merge:** `cd AURA-CHAT/client && npm run test:run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

## Wave 0 Gaps

- [ ] `src/types/settings.ts` — TypeScript types for settings API responses
- [ ] `src/stores/useModelStore.ts` + `src/stores/useModelStore.test.ts` — Zustand model selection store
- [ ] `src/features/settings/hooks/useSettingsApi.ts` + test — TanStack Query hooks
- [ ] `src/features/settings/hooks/useModelList.ts` + test — Model grouping logic
- [ ] `src/features/settings/components/HierarchicalModelPicker.tsx` + test — Hierarchical picker
- [ ] `src/features/chat/components/InlineModelPicker.tsx` + test — Compact chat picker
- [ ] NOTES equivalents (adapted copies)
