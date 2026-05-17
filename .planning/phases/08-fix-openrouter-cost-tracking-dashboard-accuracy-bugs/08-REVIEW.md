---
status: issues
files_reviewed: 1
findings:
  critical: 0
  warning: 2
  info: 1
  total: 3
---

## Summary
Reviewed the chat router implementation. The core routing logic is coherent, but there are two behavioral issues (one error-handling bug and one access-control gap) plus a minor information disclosure risk.

## Findings
### WR-1 Chitchat errors are silently ignored in non-streaming `/chat`
**Location:** `AURA-CHAT/server/routers/chat.py:L583-L600`, `L362-L368`  
`stream_chitchat_response` emits `{type: "error"}` on exceptions, but the non-streaming `/chat` handler only processes `content` and `complete` chunks. If an error occurs, the handler returns `success=True` with an empty answer, masking failures and making debugging difficult.

### WR-2 Conversation history endpoints lack ownership validation
**Location:** `AURA-CHAT/server/routers/chat.py:L916-L972`  
`get_history` and `clear_history` only require an authenticated user; they do not verify that the `session_id` belongs to the requesting user. If session IDs are guessable or shared, a user could access or clear another user's history.

### INFO-1 Internal error details are exposed to clients
**Location:** `AURA-CHAT/server/routers/chat.py:L362-L368`, `L646-L654`  
Both `stream_chitchat_response` and the `/chat` exception path return `str(e)` to clients. This can leak internal error details; consider logging full exceptions server-side and returning a generic message.

## Recommendations
- Handle `{type: "error"}` in the non-streaming chitchat path by raising an `HTTPException` or returning `success=False` with a safe message.
- Add a session ownership check in `get_history` and `clear_history` (and potentially on chat requests) to ensure session access is scoped to the authenticated user.
- Sanitize error payloads returned to clients; keep detailed error messages only in logs.
