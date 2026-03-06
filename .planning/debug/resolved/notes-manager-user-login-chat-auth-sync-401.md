---
status: resolved
trigger: "Investigate issue: notes-manager-user-login-chat-auth-sync-401"
created: 2026-02-23T18:04:38.449Z
updated: 2026-02-23T18:30:00.000Z
---

## Current Focus

hypothesis: Verification complete; fix appears stable for auth token app binding.
test: Confirm targeted auth tests pass including regression assertion for explicit auth app binding.
expecting: `/auth/sync` verification path is now deterministic and no longer coupled to default Firebase app order.
next_action: archive debug session file and report root cause/fix/evidence

## Symptoms

expected: A newly created user in AURA-NOTES-MANAGER should be recognized by AURA-CHAT login flow, and `/auth/sync` should succeed (200/204) so the user can complete login.
actual: After creating a new user in AURA-NOTES-MANAGER and trying to login in AURA-CHAT with that user ID, `/auth/sync` responds 401 and login fails.
errors: INFO:     127.0.0.1:51134 - "POST /auth/sync HTTP/1.1" 401 Unauthorized
reproduction: (1) In AURA-NOTES-MANAGER, create/add a new user using admin ID flow. (2) In AURA-CHAT, attempt login with that new user ID. (3) Observe `/auth/sync` returns 401.
started: Not explicitly provided; treated as current reproducible behavior.

## Eliminated

- hypothesis: New user missing in Firestore causes `/auth/sync` 401.
  evidence: In `AURA-CHAT/server/routers/auth.py`, missing user path raises 403 at the `not user_doc.exists` branch, not 401.
  timestamp: 2026-02-23T18:12:00.000Z
- hypothesis: AURA-NOTES-MANAGER and AURA-CHAT are using different Firebase project IDs in service-account files.
  evidence: Both `AURA-CHAT/serviceAccountKey-auth.json` and `AURA-NOTES-MANAGER/serviceAccountKey-auth.json` declare the same `project_id` (`aura-auth-proj`).
  timestamp: 2026-02-23T18:13:00.000Z

## Evidence

- timestamp: 2026-02-23T18:08:00.000Z
  checked: `AURA-CHAT/server/routers/auth.py`
  found: `/auth/sync` performs `verify_firebase_token()` first, then checks Firestore user existence.
  implication: Any 401 on `/auth/sync` originates from token verification/missing uid, not from "user not provisioned" logic.
- timestamp: 2026-02-23T18:09:00.000Z
  checked: `AURA-NOTES-MANAGER/api/users.py`
  found: Admin create-user flow creates Firebase Auth user and writes Firestore `users/{uid}` using that Firebase UID.
  implication: Cross-app identity key is expected to be Firebase UID, not a separate synthetic ID field.
- timestamp: 2026-02-23T18:11:00.000Z
  checked: `AURA-CHAT/server/auth/firebase_auth.py`
  found: `initialize_firebase()` reuses `firebase_admin._apps[0]` whenever any Firebase app already exists.
  implication: Auth verification can accidentally use a previously initialized app, regardless of `FIREBASE_CREDENTIALS`.
- timestamp: 2026-02-23T18:11:30.000Z
  checked: `AURA-CHAT/server/auth/firestore_client.py`
  found: Startup initializes Firebase app in lifespan before auth calls, using env-based credential resolution.
  implication: Initialization order can determine which Firebase app auth ends up reusing.
- timestamp: 2026-02-23T18:14:30.000Z
  checked: runtime probe of AURA-CHAT env resolution
  found: `FIREBASE_CREDENTIALS` resolves to auth service-account path and `GOOGLE_APPLICATION_CREDENTIALS` can be unset/externally set.
  implication: Existing code is sensitive to ambient process env and app-initialization side effects.
- timestamp: 2026-02-23T18:23:30.000Z
  checked: `AURA-CHAT/server/auth/firebase_auth.py` and `AURA-CHAT/server/auth/dependencies.py`
  found: Added named Firebase app isolation (`aura-auth`), Firestore client binding to that app, and explicit `auth.verify_id_token(..., app=auth_app)`.
  implication: Token verification no longer depends on whichever Firebase app initialized first in process.
- timestamp: 2026-02-23T18:28:30.000Z
  checked: `AURA-CHAT/tests/backend/api/test_auth.py`
  found: Targeted suite passed (5 tests), including new regression test asserting token verification passes explicit `app` argument from `get_auth_app()`.
  implication: Fix behavior is covered by test and currently passes in local backend test run.

## Resolution

root_cause: AURA-CHAT auth reused `firebase_admin._apps[0]` and verified tokens without binding to a dedicated auth app. If another Firebase app initialized first (or process env altered credential selection), `/auth/sync` could verify against the wrong app context and return 401 before user sync checks.
fix: Isolated auth Firebase initialization to a named app (`aura-auth`) and changed token verification to explicitly use that app (`auth.verify_id_token(..., app=auth_app)`), removing global default-app coupling.
verification:
  - `.venv/Scripts/python -m pytest AURA-CHAT/tests/backend/api/test_auth.py -q` passed (5/5).
  - Added regression test to enforce dedicated auth-app token verification binding.
files_changed:
  - AURA-CHAT/server/auth/firebase_auth.py
  - AURA-CHAT/server/auth/dependencies.py
  - AURA-CHAT/tests/backend/api/test_auth.py
