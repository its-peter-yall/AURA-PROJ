# Phase 2: UI Design Contract

**Phase:** 2 — Fixes for all the identified security, performance, and reliability issues
**Date:** 2026-05-03
**Scope:** Graph visualization progressive loading UX

---

## Overview

This phase includes minimal frontend changes to the AURA-CHAT graph explorer to support progressive loading. The primary goal is reducing initial data load to prevent WebGL memory issues on dense graphs.

---

## Changes

### GraphPage.tsx — Default Parameters

| Parameter | Current | New |
|-----------|---------|-----|
| `limit` | 500 | 100 |
| `depth` | 2 | 1 |

**Rationale:** Dense graphs with 500 nodes overwhelm WebGL client memory. Lower initial defaults with on-demand expansion provide better UX.

### Graph Controls — "Load More" Interaction

Add a "Load More" or "Expand" control to the graph toolbar:
- **Trigger:** User clicks "Expand" on a selected node or uses a "Load More" button in the controls panel
- **Behavior:** Re-queries the API with the same node as seed but `depth + 1` (up to max 3)
- **Visual feedback:** Loading spinner on the control; new nodes/edges fade in
- **State:** Track `currentDepth` in component state; disable expand when `currentDepth >= 3`

### API Contract

The backend already supports `depth` and `limit` query parameters:
- `GET /graph/data?depth={1-5}&limit={1-1000}`
- No API changes required

---

## Accessibility

- "Load More" button must have `aria-label="Expand graph to show more connections"`
- Focus must return to the graph canvas after load completes

---

## Responsive

No responsive changes needed. Graph canvas is already responsive.

---

*Minimal UI contract — Phase 2 is primarily a backend hardening phase.*
