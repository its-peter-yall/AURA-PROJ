# Deferred Items

## 2026-03-10

- Full `shared/model_router` pytest suite is currently blocked by pre-existing failures in `shared/model_router/tests/test_compat.py` against `AURA-CHAT/backend/utils/vertex_ai_client.py` (`_GenerativeModelWrapper` attribute missing in the dirty worktree). This was discovered while verifying 10-01 and is out of scope for the shared config module plan.
