# Coding Conventions

**Analysis Date:** 2026-03-10

## Naming Patterns

**Files:**
- React page and component files use `PascalCase` names such as `AURA-CHAT/client/src/features/chat/ChatPage.tsx`, `AURA-CHAT/client/src/components/MessageBubble.tsx`, and `AURA-NOTES-MANAGER/frontend/src/pages/ExplorerPage.tsx`.
- Hooks use `useX` camelCase names such as `AURA-CHAT/client/src/features/study-sessions/hooks/useStudySession.ts`, `AURA-CHAT/client/src/hooks/useGraphQuery.ts`, and `AURA-NOTES-MANAGER/frontend/src/features/kg/hooks/useKGProcessing.ts`.
- Zustand stores use `useXStore` names such as `AURA-CHAT/client/src/stores/useAuthStore.ts` and `AURA-NOTES-MANAGER/frontend/src/stores/useExplorerStore.ts`.
- Python modules use `snake_case` names such as `AURA-CHAT/server/routers/chat.py`, `AURA-CHAT/backend/routers/sessions.py`, and `AURA-NOTES-MANAGER/api/auth.py`.

**Functions:**
- TypeScript functions and local helpers use `camelCase`; examples include `getSessions` in `AURA-CHAT/client/src/lib/api.ts`, `extractFilename` in `AURA-NOTES-MANAGER/frontend/src/api/client.ts`, and `build_classification_context` in `AURA-CHAT/server/routers/chat.py`.
- React hooks are exported as named functions in both apps; examples include `useSessions` in `AURA-CHAT/client/src/features/study-sessions/hooks/useStudySession.ts` and `useKGProcessing` in `AURA-NOTES-MANAGER/frontend/src/features/kg/hooks/useKGProcessing.ts`.
- Python route dependencies and helpers use `snake_case`; examples include `verify_firebase_token` in `AURA-NOTES-MANAGER/api/auth.py` and `initialize_session_manager` in `AURA-CHAT/backend/routers/sessions.py`.

**Variables:**
- Local TypeScript state and variables use `camelCase`; examples include `isRefreshing` and `failedQueue` in `AURA-CHAT/client/src/lib/api.ts` and `processDialog` in `AURA-NOTES-MANAGER/frontend/src/stores/useExplorerStore.ts`.
- Constants use `UPPER_SNAKE_CASE` when global or config-like, such as `API_BASE_URL` in `AURA-CHAT/client/src/lib/api.ts`, `API_BASE` in `AURA-NOTES-MANAGER/frontend/src/api/client.ts`, and `IS_PRODUCTION` in `AURA-NOTES-MANAGER/api/main.py`.

**Types:**
- TypeScript interfaces and aliases use `PascalCase`; examples include `AuthState` in `AURA-CHAT/client/src/stores/useAuthStore.ts`, `BlobResponse` in `AURA-NOTES-MANAGER/frontend/src/api/client.ts`, and `ProcessingRequest` in `AURA-NOTES-MANAGER/frontend/src/features/kg/types/kg.types.ts`.
- Pydantic request and response models use `PascalCase` plus `Request` or `Response` suffixes; examples include `ChatRequest` in `AURA-CHAT/server/schemas/chat.py`, `CreateSessionRequest` in `AURA-CHAT/backend/routers/sessions.py`, and `BatchDeleteRequest` in `AURA-NOTES-MANAGER/api/modules/models.py`.

## Code Style

**Formatting:**
- TypeScript is compiled in strict mode in `AURA-CHAT/client/tsconfig.app.json` and split-reference mode in `AURA-NOTES-MANAGER/frontend/tsconfig.json`; preserve strict typing and unused symbol errors.
- ESLint flat config is the active formatter/linter signal for both frontends via `AURA-CHAT/client/eslint.config.js` and `AURA-NOTES-MANAGER/frontend/eslint.config.js`.
- Semicolons and single quotes are the dominant TypeScript style in both frontends; examples appear throughout `AURA-CHAT/client/src/test/setup.ts` and `AURA-NOTES-MANAGER/frontend/src/api/client.ts`.
- Python follows 4-space indentation, typed signatures, and docstrings in primary entry points such as `AURA-CHAT/server/main.py` and `AURA-NOTES-MANAGER/api/main.py`.

**Linting:**
- `AURA-CHAT/client/eslint.config.js` and `AURA-NOTES-MANAGER/frontend/eslint.config.js` both extend `@eslint/js`, `typescript-eslint`, and React hooks rules.
- `react-refresh/only-export-components` is explicitly enforced in `AURA-NOTES-MANAGER/frontend/eslint.config.js`.
- Ignore patterns are minimal and target generated output only (`dist`, `coverage`) in both frontend ESLint configs.

## File Header Pattern

**AURA-CHAT TypeScript/TSX:**
- Use the compact single-line header style already present in `AURA-CHAT/client/src/test/setup.ts`, `AURA-CHAT/client/src/components/MessageBubble.test.tsx`, and `AURA-CHAT/client/src/hooks/useGraphQuery.test.tsx`.

```ts
// setup.ts
// Test setup file for Vitest with React Testing Library
// ...
// @see: vitest.config.ts - Vitest configuration referencing this file
// @note: All mocks are cleared after each test to prevent state leakage
```

**AURA-NOTES-MANAGER TypeScript/TSX and Python:**
- Use the block-style banner header already present in `AURA-NOTES-MANAGER/frontend/src/api/client.ts`, `AURA-NOTES-MANAGER/frontend/src/features/kg/hooks/useKGProcessing.ts`, and `AURA-NOTES-MANAGER/api/main.py`.

```ts
/**
 * ============================================================================
 * FILE: client.ts
 * LOCATION: frontend/src/api/client.ts
 * ============================================================================
 */
```

## Import Organization

**Order:**
1. Runtime/framework imports (`react`, `@tanstack/react-query`, `fastapi`, stdlib modules)
2. Third-party helpers (`axios`, `firebase`, `slowapi`, `msw`)
3. App-local imports (`@/types`, `../stores/useAuthStore`, `backend.*`, `server.*`, `api.*`)

**Path Aliases:**
- `@/*` points at `AURA-CHAT/client/src/*` via `AURA-CHAT/client/tsconfig.app.json`.
- `@/*` points at `AURA-NOTES-MANAGER/frontend/src/*` via `AURA-NOTES-MANAGER/frontend/vite.config.ts` and app tsconfig references.

**Observed usage:**
- Type-only imports are used in client code, for example `import type { Citation }` in `AURA-CHAT/client/src/components/MessageBubble.test.tsx` and `import type { ProcessingRequest }` in `AURA-NOTES-MANAGER/frontend/src/features/kg/hooks/useKGProcessing.test.tsx`.
- Python imports usually group stdlib before framework/app imports, as seen in `AURA-CHAT/server/main.py`, `AURA-CHAT/server/routers/chat.py`, and `AURA-NOTES-MANAGER/api/main.py`.

## State Management

**Client state:**
- Use Zustand for persistent UI/auth state only. `AURA-CHAT/client/src/stores/useAuthStore.ts` owns auth, token, and active department. `AURA-NOTES-MANAGER/frontend/src/stores/useExplorerStore.ts` owns selection, dialogs, navigation, and KG polling UI state.
- Keep store actions colocated inside the store definition rather than split across helper modules. Both store files export a single `create(...)` call with actions inline.

**Server state:**
- Use TanStack Query for remote data and cache invalidation. Query-key factories are explicit in `AURA-CHAT/client/src/features/study-sessions/hooks/useStudySession.ts`, while Notes uses stable tuple keys such as `['kg', 'queue']` and `['explorer', 'tree']` in `AURA-NOTES-MANAGER/frontend/src/features/kg/hooks/useKGProcessing.ts`.
- Cache invalidation happens inside mutation `onSuccess` callbacks, not in components; examples include `useCreateSession` in `AURA-CHAT/client/src/features/study-sessions/hooks/useStudySession.ts` and `processFiles` in `AURA-NOTES-MANAGER/frontend/src/features/kg/hooks/useKGProcessing.ts`.

## API Conventions

**Frontend API layer:**
- `AURA-CHAT/client/src/lib/api.ts` centralizes Axios configuration, auth headers, 401 retry behavior, and all typed API calls. Add new chat/client endpoints there rather than scattering `fetch` or `axios` across pages.
- `AURA-NOTES-MANAGER/frontend/src/api/client.ts` centralizes native `fetch` wrappers and throws domain-specific `DuplicateError` for 409 conflicts. Add new Notes frontend calls through `fetchApi`, `fetchBlob`, or `fetchFormData`.
- Keep response typing at the API boundary. Both apps return `Promise<T>` from API helpers and let hooks/components consume typed payloads.

**Backend routers:**
- FastAPI routers are defined as `router = APIRouter(prefix=..., tags=[...])`; examples include `AURA-CHAT/server/routers/chat.py`, `AURA-CHAT/backend/routers/sessions.py`, `AURA-NOTES-MANAGER/api/explorer.py`, and `AURA-NOTES-MANAGER/api/routers/graph_preview.py`.
- Request and response schemas stay near the route layer with Pydantic `BaseModel` types, such as `CreateSessionRequest` in `AURA-CHAT/backend/routers/sessions.py` and route schemas in `AURA-NOTES-MANAGER/api/schemas/graph_preview.py`.
- Dependency injection is the standard authentication/service pattern. Examples: `Depends(get_rag_engine)` and `Depends(require_student_or_staff)` in `AURA-CHAT/server/routers/chat.py`, and `Depends(get_current_user)` in `AURA-NOTES-MANAGER/api/auth.py`.

## Error Handling

**Patterns:**
- Frontend API layers normalize errors before they reach components. `AURA-CHAT/client/src/lib/api.ts` logs by response/request/message branch; `AURA-NOTES-MANAGER/frontend/src/api/client.ts` parses JSON error bodies and raises typed exceptions.
- Frontend auth flows convert low-level provider failures into user-facing messages inside stores, as shown in `AURA-CHAT/client/src/stores/useAuthStore.ts`.
- FastAPI routes raise `HTTPException` for auth and validation failures, and wrap broader failures in structured responses. See `AURA-NOTES-MANAGER/api/auth.py` and `AURA-CHAT/server/main.py`.
- A global exception handler is active in `AURA-CHAT/server/main.py`; Notes applies middleware-driven security headers and route-local exceptions in `AURA-NOTES-MANAGER/api/main.py`.

## Logging

**Framework:**
- `AURA-CHAT` favors structured logger instances from `backend.utils.logging_config.setup_logging`, used in `AURA-CHAT/server/main.py`, `AURA-CHAT/server/routers/chat.py`, and `AURA-CHAT/backend/routers/sessions.py`.
- `AURA-NOTES-MANAGER` backend mixes `logging.getLogger(__name__)` in `AURA-NOTES-MANAGER/api/main.py` with direct `print(...)` debug statements still present in `AURA-NOTES-MANAGER/api/auth.py`.
- Frontend code still uses `console.error`, `console.warn`, and dev-only `console.log` in files such as `AURA-CHAT/client/src/stores/useAuthStore.ts` and `AURA-NOTES-MANAGER/frontend/src/api/client.ts`.

**Patterns:**
- Log and rethrow on backend failures instead of swallowing exceptions.
- Keep dev-only diagnostics gated by environment checks, as in `AURA-CHAT/client/src/stores/useAuthStore.ts`.

## Comments

**When to Comment:**
- Prefer comments that explain intent, test isolation, retry behavior, or environment constraints. Good examples: `AURA-CHAT/client/src/test/setup.ts`, `AURA-CHAT/tests/conftest.py`, and `AURA-NOTES-MANAGER/frontend/e2e/fixtures.ts`.
- Inline comments are common around auth retry, polling, and mocked behavior; preserve that density in non-obvious code paths.

**JSDoc/TSDoc:**
- Public hooks and utility modules often carry top-of-file and function-level docs in both frontends, for example `AURA-CHAT/client/src/features/study-sessions/hooks/useStudySession.ts` and `AURA-NOTES-MANAGER/frontend/src/api/client.ts`.
- Python entry points and dependencies usually include module or function docstrings, especially in `AURA-CHAT/server/main.py`, `AURA-CHAT/server/routers/chat.py`, and `AURA-NOTES-MANAGER/api/auth.py`.

## Function Design

**Size:**
- Small hooks and helpers are preferred for data access (`AURA-CHAT/client/src/hooks/useGraphQuery.ts`, `AURA-NOTES-MANAGER/frontend/src/features/kg/hooks/useKGProcessing.ts`), but route files can be large when they own several related endpoints (`AURA-CHAT/server/routers/chat.py`, `AURA-CHAT/backend/routers/sessions.py`).

**Parameters:**
- TypeScript API and hook functions use explicit primitive parameters rather than opaque options objects unless the payload is domain-specific; examples include `getSemesters(departmentId)` in `AURA-CHAT/client/src/lib/api.ts` and `fetchApi<T>(endpoint, options?)` in `AURA-NOTES-MANAGER/frontend/src/api/client.ts`.
- Python endpoints and helpers are strongly named with typed parameters and optional defaults, for example `getSessions(userId, status?, limit, offset)` equivalents in `AURA-CHAT/client/src/lib/api.ts` mirror router signatures in `AURA-CHAT/backend/routers/sessions.py`.

**Return Values:**
- Frontend API helpers return raw typed payloads and let hooks manage cache and view state.
- Backend route functions return Pydantic models, dictionaries, or `StreamingResponse` depending on endpoint semantics, as seen in `AURA-CHAT/server/routers/chat.py` and `AURA-CHAT/backend/routers/sessions.py`.

## Module Design

**Exports:**
- Named exports are the dominant pattern for hooks, stores, and helpers across both frontends, such as `sessionKeys` and `useSessions` in `AURA-CHAT/client/src/features/study-sessions/hooks/useStudySession.ts` and `fetchApi` in `AURA-NOTES-MANAGER/frontend/src/api/client.ts`.
- Default exports still exist for app shells and page-level components, so preserve local file behavior when editing those modules. Current examples include `AURA-CHAT/client/src/App.tsx`, `AURA-CHAT/client/src/components/ui/Dropdown.tsx`, `AURA-NOTES-MANAGER/frontend/src/App.tsx`, and `AURA-NOTES-MANAGER/frontend/src/pages/ExplorerPage.tsx`.

**Barrel Files:**
- Notes frontend uses barrel-style re-exports from store/type folders, for example `AURA-NOTES-MANAGER/frontend/src/stores/index.ts` and `AURA-NOTES-MANAGER/frontend/src/types/index.ts`.
- AURA-CHAT relies more on direct imports plus the `@/types` re-export surface referenced in `AURA-CHAT/client/src/lib/api.ts`.

## Shared Guidance

- Match the local header/comment style of the app you are editing; AURA-CHAT and AURA-NOTES-MANAGER do not use the same file banner format.
- Put remote data logic in API helpers and hooks, not directly in pages.
- Put persistent UI/auth state in Zustand, and invalidate TanStack Query caches from mutation callbacks.
- For FastAPI work, define request/response models near the router and wire services through `Depends(...)`.

---

*Convention analysis: 2026-03-10*
