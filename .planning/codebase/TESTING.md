# Testing Patterns

**Analysis Date:** 2026-03-10

## Test Framework

**Runner:**
- `Vitest` for frontend unit/component/hook tests in `AURA-CHAT/client/vitest.config.ts` and the `test` block inside `AURA-NOTES-MANAGER/frontend/vite.config.ts`.
- `Pytest` for Python backend and integration tests in `AURA-CHAT/pyproject.toml`, `AURA-CHAT/pytest.ini`, `AURA-CHAT/tests/`, and `AURA-NOTES-MANAGER/tests/`.
- `Playwright` for frontend E2E in `AURA-CHAT/client/playwright.config.ts` and `AURA-NOTES-MANAGER/frontend/playwright.config.ts`.
- `Jest` for Firestore security rules in `AURA-NOTES-MANAGER/frontend/jest.config.cjs` and legacy JS rules tests in `AURA-NOTES-MANAGER/jest.config.js`.

**Assertion Library:**
- Frontend unit tests use Testing Library + jest-dom in `AURA-CHAT/client/src/test/setup.ts` and `AURA-NOTES-MANAGER/frontend/src/test/setup.ts`.
- Python tests use plain `assert`, `pytest.raises`, and `fastapi.testclient.TestClient` in files such as `AURA-CHAT/tests/security/test_security_middleware.py` and `AURA-NOTES-MANAGER/tests/test_auth_sync.py`.

**Run Commands:**
```bash
cd AURA-CHAT/client && npm run test              # AURA-CHAT Vitest
cd AURA-CHAT/client && npm run test:coverage     # AURA-CHAT coverage report
cd AURA-CHAT/client && npm run test:e2e          # AURA-CHAT Playwright
cd AURA-CHAT && ..\.venv\Scripts\python -m pytest tests -v   # AURA-CHAT backend tests
cd AURA-NOTES-MANAGER/frontend && npm test       # Notes frontend Vitest
cd AURA-NOTES-MANAGER/frontend && npm run test:rules  # Notes Firestore rules via emulator
cd AURA-NOTES-MANAGER/frontend && npm run test:e2e    # Notes frontend Playwright
cd AURA-NOTES-MANAGER && npx jest tests/firestore/    # Legacy Firestore JS rules tests
cd AURA-NOTES-MANAGER && ..\.venv\Scripts\python -m pytest tests -v  # Notes backend tests
```

## Test File Organization

**Location:**
- `AURA-CHAT/client/src/**/*.test.ts(x)` holds co-located frontend tests such as `AURA-CHAT/client/src/components/MessageBubble.test.tsx` and `AURA-CHAT/client/src/features/study-sessions/hooks/useStudySession.test.tsx`.
- `AURA-CHAT/client/e2e/*.spec.ts` holds browser flows such as `AURA-CHAT/client/e2e/chat.spec.ts` and `AURA-CHAT/client/e2e/mobile.spec.ts`.
- `AURA-CHAT/tests/` is split by scope: `api/`, `backend/`, `integration/`, `performance/`, `security/`, and `unit/`.
- `AURA-NOTES-MANAGER/frontend/src/**/*.test.ts(x)` mixes unit, component, store, and integration-style frontend tests, for example `AURA-NOTES-MANAGER/frontend/src/pages/ExplorerPage.test.tsx` and `AURA-NOTES-MANAGER/frontend/src/integration/WarningDialogFlow.test.tsx`.
- `AURA-NOTES-MANAGER/frontend/e2e/*.spec.ts` contains modern Playwright flows such as `AURA-NOTES-MANAGER/frontend/e2e/auth.spec.ts` and `AURA-NOTES-MANAGER/frontend/e2e/kg-processing.spec.ts`.
- `AURA-NOTES-MANAGER/tests/` contains backend pytest suites such as `AURA-NOTES-MANAGER/tests/test_auth_integration.py`, `AURA-NOTES-MANAGER/tests/test_kg_router_delete.py`, and `AURA-NOTES-MANAGER/tests/test_graph_preview.py`.

**Naming:**
- Frontend tests use `*.test.ts` or `*.test.tsx`.
- E2E specs use `*.spec.ts`.
- Python tests use `test_*.py`.

**Structure:**
```
AURA-CHAT/client/src/<feature>/<file>.test.tsx
AURA-CHAT/client/e2e/<flow>.spec.ts
AURA-CHAT/tests/{api,backend,integration,performance,security,unit}/test_*.py
AURA-NOTES-MANAGER/frontend/src/<area>/<file>.test.tsx
AURA-NOTES-MANAGER/frontend/e2e/<flow>.spec.ts
AURA-NOTES-MANAGER/tests/test_*.py
```

## Test Structure

**Suite Organization:**
```ts
describe('useStudySession hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('useSessions', () => {
    it('returns sessions after load', async () => {
      // arrange
      // act
      // assert
    });
  });
});
```

```py
class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_get_current_user_success(self) -> None:
        ...
```

**Patterns:**
- Frontend tests group by feature or behavior using nested `describe` blocks, as in `AURA-CHAT/client/src/features/study-sessions/hooks/useStudySession.test.tsx`, `AURA-CHAT/client/src/components/MessageBubble.test.tsx`, and `AURA-NOTES-MANAGER/frontend/src/pages/ExplorerPage.test.tsx`.
- Python tests use `TestX` classes with focused methods in both repos, as seen in `AURA-CHAT/tests/unit/test_messages.py` and `AURA-NOTES-MANAGER/tests/test_auth_integration.py`.
- Large Python endpoint suites often stay in a single file with many fixtures and helper sections, such as `AURA-NOTES-MANAGER/tests/test_kg_router_delete.py`.

## Mocking

**Framework:**
- Frontend unit tests use `vi.mock`, `vi.spyOn`, and Testing Library in both apps.
- AURA-CHAT frontend also uses MSW through `AURA-CHAT/client/src/mocks/server.ts` and `AURA-CHAT/client/src/mocks/handlers.ts`.
- Python tests use `unittest.mock` (`MagicMock`, `AsyncMock`, `patch`) in both repos.
- Playwright tests rely heavily on route interception and local fixtures in `AURA-CHAT/client/e2e/chat.spec.ts` and `AURA-NOTES-MANAGER/frontend/e2e/fixtures.ts`.

**Patterns:**
```ts
vi.mock('@/lib/api', () => ({
  getSessions: vi.fn(),
  createSession: vi.fn(),
}));
```

```py
app.dependency_overrides[get_graph_manager] = lambda: mock_graph_manager
app.dependency_overrides[get_rag_engine] = lambda: mock_rag_engine
with TestClient(app) as test_client:
    yield test_client
```

**What to Mock:**
- Mock network and auth boundaries: `AURA-CHAT/client/src/lib/api.ts`, `AURA-NOTES-MANAGER/frontend/src/api/client.ts`, Firebase, Firestore, Neo4j, Redis, and LLM clients.
- Mock FastAPI dependencies instead of booting real services; use the override pattern from `AURA-CHAT/tests/backend/api/conftest.py` and `AURA-NOTES-MANAGER/tests/test_auth_sync.py`.
- For E2E, mock slow or privileged backend flows through Playwright routes or mock auth utilities, as done in `AURA-CHAT/client/e2e/chat.spec.ts` and `AURA-NOTES-MANAGER/frontend/e2e/fixtures.ts`.

**What NOT to Mock:**
- Do not mock Zustand store behavior when the store itself is the unit under test; `AURA-NOTES-MANAGER/frontend/src/stores/useExplorerStore.test.ts` exercises the real store via `useExplorerStore.getState()`.
- Do not bypass Pydantic model construction in backend validation tests; `AURA-NOTES-MANAGER/tests/test_kg_router_delete.py` creates `BatchDeleteRequest` and `BatchDeleteResponse` directly.

## Fixtures and Factories

**Test Data:**
```py
@pytest.fixture
def sample_session(sample_user) -> Dict[str, Any]:
    return {
        'id': 'session-456-def',
        'user_id': sample_user['id'],
        'status': 'active',
    }
```

```ts
function createAssistantMessage(overrides: Partial<LocalMessage> = {}): LocalMessage {
  return {
    id: 'msg-2',
    role: 'assistant',
    content: 'Machine learning is a subset of AI [1].',
    ...overrides,
  };
}
```

**Location:**
- Shared Python fixtures live in `AURA-CHAT/tests/conftest.py`, `AURA-CHAT/tests/backend/api/conftest.py`, and `AURA-NOTES-MANAGER/conftest.py`.
- AURA-CHAT frontend test infrastructure lives in `AURA-CHAT/client/src/test/setup.ts` plus `AURA-CHAT/client/src/mocks/`.
- Notes frontend test infrastructure lives in `AURA-NOTES-MANAGER/frontend/src/test/setup.ts` and Playwright helpers in `AURA-NOTES-MANAGER/frontend/e2e/fixtures.ts`.

## Coverage

**Requirements:**
- `AURA-CHAT/pyproject.toml` enables coverage for `backend` and sets `fail_under = 30`; this is a low enforced threshold, not a strong quality gate.
- `AURA-CHAT/client/vitest.config.ts` has targeted include lists and comments out global thresholds, so coverage is selective rather than repo-wide.
- `AURA-NOTES-MANAGER/frontend/vite.config.ts` generates V8 coverage for `src/**/*.{ts,tsx}` but does not enforce thresholds.
- `AURA-NOTES-MANAGER` backend has no central pytest config or enforced fail-under setting detected; coverage commands are documented in `AURA-NOTES-MANAGER/README_TESTS.md` for specific suites.

**View Coverage:**
```bash
cd AURA-CHAT/client && npm run test:coverage
cd AURA-CHAT && ..\.venv\Scripts\python -m pytest --cov=backend --cov=server tests
cd AURA-NOTES-MANAGER/frontend && vitest run --coverage
cd AURA-NOTES-MANAGER && pytest tests/test_kg_router_delete.py --cov=api.kg.router --cov-report=term-missing
```

## Test Types

**Unit Tests:**
- React component and hook tests dominate the frontend suites, e.g. `AURA-CHAT/client/src/components/MessageBubble.test.tsx`, `AURA-CHAT/client/src/hooks/useGraphQuery.test.tsx`, `AURA-NOTES-MANAGER/frontend/src/api/client.test.ts`, and `AURA-NOTES-MANAGER/frontend/src/features/kg/components/KGStatusBadge.test.tsx`.
- Python unit-style tests focus on isolated managers, helpers, and schemas, such as `AURA-CHAT/tests/unit/test_messages.py` and request/response validation in `AURA-NOTES-MANAGER/tests/test_kg_router_delete.py`.

**Integration Tests:**
- AURA-CHAT backend includes explicit integration folders like `AURA-CHAT/tests/integration/test_rag_engine_integration.py` and `AURA-CHAT/tests/integration/test_session_manager_integration.py`.
- Notes backend integration patterns appear in endpoint-heavy files like `AURA-NOTES-MANAGER/tests/test_auth_sync.py` and `AURA-NOTES-MANAGER/tests/test_graph_preview.py` using `TestClient(app)` plus patched service boundaries.
- Frontend integration-style tests exist under `AURA-NOTES-MANAGER/frontend/src/integration/`.

**E2E Tests:**
- AURA-CHAT uses Playwright with `fullyParallel: true` in `AURA-CHAT/client/playwright.config.ts` and route-mocked smoke flows in `AURA-CHAT/client/e2e/chat.spec.ts`.
- Notes uses Playwright with `fullyParallel: false` in `AURA-NOTES-MANAGER/frontend/playwright.config.ts`, default mock auth, and shared fixtures in `AURA-NOTES-MANAGER/frontend/e2e/fixtures.ts`.

## Common Patterns

**Async Testing:**
```py
@pytest.mark.asyncio
async def test_verify_mock_token_success(self) -> None:
    result = await verify_firebase_token('mock-token-admin')
    assert result['role'] == 'admin'
```

```ts
await waitFor(() => {
  expect(result.current.isSuccess).toBe(true);
});
```

**Error Testing:**
```ts
await expect(fetchApi('/test')).rejects.toThrow(DuplicateError);
```

```py
with pytest.raises(HTTPException) as exc_info:
    await get_current_user(credentials)
assert exc_info.value.status_code == 401
```

## Current Gaps

- `AURA-CHAT/client/vitest.config.ts` explicitly excludes `AURA-CHAT/client/src/features/modules/hooks/useDocuments.test.tsx` and `AURA-CHAT/client/src/features/modules/hooks/useModule.test.tsx`, so module-selection hooks are not part of current coverage.
- `AURA-CHAT/client/vitest.config.ts` comments out global coverage thresholds, and `AURA-CHAT/pyproject.toml` enforces only `fail_under = 30`; the repo does not currently enforce the higher coverage expectations described elsewhere.
- `AURA-CHAT/tests/api/test_api_smoke.py` is only a placeholder, so the `tests/api/` area is not a meaningful API regression suite yet.
- Many E2E flows in `AURA-CHAT/client/e2e/chat.spec.ts` and `AURA-NOTES-MANAGER/frontend/e2e/auth.spec.ts` rely on mocked routes or mock auth, which is good for determinism but leaves full live-service coverage limited.
- `AURA-NOTES-MANAGER/frontend/src/test/setup.ts` globally mocks React Query hooks, so some component and hook tests validate shape and rendering more than real cache behavior.
- `AURA-NOTES-MANAGER` backend has substantial pytest coverage in targeted files like `AURA-NOTES-MANAGER/tests/test_graph_manager_delete.py` and `AURA-NOTES-MANAGER/tests/test_kg_router_delete.py`, but no centralized pytest config or repo-wide coverage threshold is detected.

---

*Testing analysis: 2026-03-10*
