# Phase 10: User Setup Required

**Generated:** 2026-03-10
**Phase:** 10-cross-app-migration-backend-integration
**Status:** Incomplete

Complete these items for shared provider API key encryption to function across
both applications.

## Environment Variables

| Status | Variable | Source | Add to |
|--------|----------|--------|--------|
| [ ] | `AURA_MASTER_KEY` | Generate with: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` | Backend `.env` / deployment secret store used by both apps |

## Dashboard Configuration

- [ ] **Persist the shared encryption key for both backends**
  - Location: deployment secret manager or each backend's `.env`
  - Set to: the generated `AURA_MASTER_KEY` value
  - Notes: both AURA-CHAT and AURA-NOTES-MANAGER must use the same key or
    previously stored provider API keys will become unreadable after restart.

## Local Development

- [ ] Add `AURA_MASTER_KEY` to the local backend environment before testing the
  settings API key endpoints.

## Verification

After completing setup, verify with:

```bash
# From each backend directory after env vars are loaded
../.venv/Scripts/python -c "from server.routers.settings import get_key_manager; print('AURA-CHAT ready')"
../.venv/Scripts/python -c "from api.routers.settings import get_key_manager; print('AURA-NOTES ready')"
```

Expected results:
- Both commands import without `AURA_MASTER_KEY` errors.
- Stored provider API keys remain readable across app restarts.

---

**Once all items complete:** Mark status as "Complete" at top of file.
