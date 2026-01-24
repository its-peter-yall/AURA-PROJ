# Implementation Plan: Session Management Improvements

I will enhance the session management experience by replacing the browser prompt with a custom UI, enabling session renaming, and adding a "pin" feature.

## 1. Backend Updates (`AURA-CHAT/backend`)
### Data Models (`routers/sessions.py`)
- Update `CreateSessionRequest`: Add `pinned: bool = False`.
- Update `UpdateSessionRequest`: Add `pinned: Optional[bool] = None`.
- Update `SessionResponse`: Add `pinned: bool`.

### Database Logic (`session_manager.py`)
- Update `create_session`: Initialize `pinned` property in Neo4j node creation.
- Update `update_session`: Add logic to update the `pinned` property.
- Update `list_user_sessions`:
  - Return `s.pinned` in the Cypher query.
  - Update sort order to prioritize pinned sessions: `ORDER BY s.pinned DESC, s.updated_at DESC`.

## 2. Frontend Updates (`AURA-CHAT/client`)
### Type Definitions (`src/types/api.ts`)
- Update `StudySession` interface to include `pinned: boolean`.
- Update `UpdateSessionRequest` interface to include `pinned?: boolean`.

### New Component (`src/features/chat/components/SessionNameModal.tsx`)
- Create a new modal component consistent with `ConfirmationDialog` styles.
- Features:
  - Input field for session name.
  - "Create" or "Save" button.
  - "Cancel" button.
  - Backdrop blur and theme-consistent styling (Cyber Yellow).

### Chat Page Integration (`src/features/chat/ChatPage.tsx`)
- Remove usage of `window.prompt()`.
- Integrate `SessionNameModal` for creating new sessions.
- Manage modal state (`isOpen`, `pendingSessionType`).

### Session Sidebar Enhancements (`src/features/study-sessions/components/SessionSidebar.tsx`)
- Add "Pin" toggle button to session items (using a Pin icon).
- Add "Edit" button to session items (using an Edit/Pencil icon).
- Integrate `SessionNameModal` for renaming existing sessions.
- Implement handlers:
  - `handlePin`: Toggles `pinned` state via `updateSession`.
  - `handleRename`: Updates `title` via `updateSession`.

## 3. Verification
- **Manual Test**:
  - Create a new session and verify the custom modal appears.
  - Pin a session and verify it moves to the top of the list.
  - Rename a session and verify the change reflects immediately.
  - Refresh page to ensure persistence.
- **Diagnostics**: Run `lsp_diagnostics` to ensure no type errors in updated files.
