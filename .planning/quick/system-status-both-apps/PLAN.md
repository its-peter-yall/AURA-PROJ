# PLAN: Display system status for both applications in AURA-NOTES-MANAGER settings

## Goal
Update the `SettingsPage` in `AURA-NOTES-MANAGER` to display the health status of both the Notes Manager and the Chat application.

## Proposed Changes

### 1. Frontend Proxy (`AURA-NOTES-MANAGER/frontend/vite.config.ts`)
- Add proxy for `/chat-api` -> `http://127.0.0.1:8000`.
- Rewrite path `/chat-api` to `/` (since AURA-CHAT uses `/health` etc at root).
- Actually, AURA-CHAT has `/health` prefix in its router, but it also has root `/health`.
- Wait, AURA-CHAT `routers/health.py` has `prefix="/health"`. So `/health` becomes `/health/health`? No.
- Let's check `AURA-CHAT/server/main.py` include router.
- `app.include_router(health_router)` where `health_router` has `prefix="/health"`.
- `app.include_router(health_root_router)` where `health_root_router` has no prefix.
- So `GET /health` works.
- If I proxy `/chat-api` to `http://127.0.0.1:8000`, then `/chat-api/health` will go to `http://127.0.0.1:8000/chat-api/health` unless I rewrite.
- I'll rewrite `/chat-api` to ``.

### 2. API Client (`AURA-NOTES-MANAGER/frontend/src/api/client.ts`)
- Define `ChatHealthStatus` interface.
- Update `HealthStatus` interface to include `chat` property.
- Update `checkHealth` to fetch from `/chat-api/health`.

### 3. Settings Page (`AURA-NOTES-MANAGER/frontend/src/pages/SettingsPage.tsx`)
- Update the "System Status" section.
- Split into "Notes Manager" and "Chat" sub-sections or similar.
- Add specific indicators for Chat: Neo4j, Semantic Router.

## Verification Plan
1. Start AURA-CHAT backend on 8000.
2. Start AURA-NOTES-MANAGER backend on 8001.
3. Start AURA-NOTES-MANAGER frontend on 5174.
4. Navigate to Settings and verify both statuses are shown and correct.
