# Frontend Dependencies Report: kg-query Feature

**Generated:** 2026-01-29  
**Phase:** RC-01 Dependency Mapping  
**Target:** AURA-NOTES-MANAGER/frontend/src/features/kg-query/

---

## Executive Summary

The `kg-query` feature is **fully self-contained** with only one external dependency (route registration in App.tsx). No other features import from kg-query, making it safe for removal. The `EntityGraph` component is suitable for migration to AURA-CHAT with minimal changes.

---

## 1. Complete Feature File Tree

```
AURA-NOTES-MANAGER/frontend/src/features/kg-query/
├── api/
│   └── kg-query.api.ts              # HTTP client for KG query backend (347 lines)
│                                     # Purpose: Typed API calls for search, graph data, feedback
│                                     # Dependencies: @/api/client, ../types/kg-query.types
│                                     # API Base: /v1/kg
│
├── components/
│   ├── EntityGraph.tsx               # ⭐ MIGRATE TO AURA-CHAT (465 lines)
│   │                                 # Purpose: SVG force-directed graph visualization
│   │                                 # Dependencies: lucide-react, ../types (GraphData, GraphNode, GraphEdge)
│   │                                 # No external npm deps (pure SVG + React)
│   │
│   ├── GraphFilterPanel.tsx          # DELETE (355 lines)
│   │                                 # Purpose: Filter panel for UnifiedGraphView
│   │                                 # Used only by UnifiedGraphView
│   │
│   ├── KGSearchBar.tsx               # DELETE (523 lines)
│   │                                 # Purpose: Search UI with module filter + advanced options
│   │                                 # Used only by KGQueryPage
│   │
│   ├── SearchResultsList.tsx         # DELETE (497 lines)
│   │                                 # Purpose: Display search results with feedback UI
│   │                                 # Used only by KGQueryPage
│   │
│   └── UnifiedGraphView.tsx          # DELETE (605 lines)
│                                     # Purpose: Advanced graph viz with filters/export
│                                     # Alternative to EntityGraph (not used by KGQueryPage)
│
├── hooks/
│   └── useKGQuery.ts                 # DELETE (226 lines)
│                                     # Purpose: React Query hooks for search, graph data, feedback
│                                     # Dependencies: @tanstack/react-query, ../api, ../types
│
├── pages/
│   └── KGQueryPage.tsx               # DELETE (386 lines)
│                                     # Purpose: Main KG query page integrating all components
│                                     # Only imported by App.tsx for routing
│
└── types/
    └── kg-query.types.ts             # DELETE (347 lines)
                                      # Purpose: TypeScript interfaces for KG operations
                                      # Only used within kg-query feature
```

**Total:** 9 files, ~3,751 lines of code

---

## 2. Route Registration

**Location:** `AURA-NOTES-MANAGER/frontend/src/App.tsx:42`

```tsx
<Route path="/kg-query" element={<KGQueryPage />} />
```

**Import:** Line 35
```tsx
import { KGQueryPage } from './features/kg-query/pages/KGQueryPage'
```

**Removal Steps:**
1. Delete Route element (line 42)
2. Delete import statement (line 35)
3. Remove JSDoc reference (line 25)

---

## 3. Navigation References

**Summary:** No navigation links found in UI components.

**Analysis:**
- ✅ No sidebar/header menu links to `/kg-query`
- ✅ No `navigate('/kg-query')` calls in other features
- ✅ No `<Link to="/kg-query">` in other components
- ✅ Route only accessible via direct URL navigation

**Files Checked:**
- `components/layout/Header.tsx` - No references
- `components/layout/Sidebar.tsx` - No references
- `pages/ExplorerPage.tsx` - No references (implicit root check)

**Conclusion:** Users cannot navigate to kg-query from the UI. Removal will not break navigation flows.

---

## 4. EntityGraph Migration Requirements

### 4.1 Component Overview

**File:** `components/EntityGraph.tsx`  
**Lines:** 465  
**Purpose:** SVG-based force-directed graph visualization with zoom/pan controls

### 4.2 External Dependencies

**NPM Packages:**
- ✅ `react` (already in AURA-CHAT)
- ✅ `lucide-react` (already in AURA-CHAT)

**No additional npm installs required.**

### 4.3 Internal Dependencies

**Within kg-query feature:**
- `../types/kg-query.types` → Import `GraphData`, `GraphNode`, `GraphEdge`

**Migration Strategy:**
1. Copy `EntityGraph.tsx` to `AURA-CHAT/client/src/features/graph/components/`
2. Copy type definitions:
   ```typescript
   // Extract from kg-query.types.ts lines 142-166
   export interface GraphNode {
     id: string;
     label: string;
     name: string;
     type: string;
     properties: Record<string, unknown>;
     x?: number;
     y?: number;
   }

   export interface GraphEdge {
     id: string;
     source: string;
     target: string;
     type: string;
     properties: Record<string, unknown>;
   }

   export interface GraphData {
     nodes: GraphNode[];
     edges: GraphEdge[];
     nodeCount: number;
     edgeCount: number;
     moduleId?: string;
   }
   ```
3. Create `AURA-CHAT/client/src/features/graph/types/graph.types.ts` with these types

### 4.4 Entity Colors

**Defined in EntityGraph.tsx (lines 35-44):**
```typescript
const ENTITY_COLORS: Record<string, string> = {
    Topic: '#4CAF50',
    Concept: '#2196F3',
    Methodology: '#FF9800',
    Finding: '#9C27B0',
    Chunk: '#607D8B',
    ParentChunk: '#795548',
    Document: '#E91E63',
    default: '#999999',
};
```

**Recommendation:** Update `Topic` color to `#FFD400` (Cyber Yellow) to match AURA-CHAT theme.

### 4.5 API Endpoint Changes

**Current (NOTES-MANAGER):**
```
GET /v1/kg/graph/data?module_id={id}&entity_types={types}&limit={limit}
```

**AURA-CHAT Equivalent:**
- If graph preview API exists: Use that endpoint
- If not: AURA-CHAT's existing RAG backend should provide similar graph data
- Check `AURA-CHAT/server/routers/` for graph endpoints

**Action Required:** Verify AURA-CHAT has graph data endpoint or create one.

### 4.6 Styling Considerations

**Current:** Uses inline CSS-in-JS with CSS variables:
- `var(--surface-1)` - Background colors
- `var(--border-1)` - Border colors
- `var(--text-1/2/3)` - Text colors
- `var(--primary)` - Highlight color

**AURA-CHAT Compatibility:**
- ✅ Both apps use CSS variable patterns
- ⚠️ Verify AURA-CHAT defines same CSS variables
- If not: Update EntityGraph's inline styles to match AURA-CHAT's variables

**Recommended:** Extract styles to separate CSS module for easier theming.

### 4.7 Functional Features

**Included:**
- ✅ Force-directed layout with physics simulation
- ✅ Zoom in/out controls
- ✅ Pan with mouse drag
- ✅ Node selection with Cyber Yellow highlight
- ✅ Hover highlighting with connected nodes
- ✅ Entity type legend with color indicators
- ✅ Graph statistics (node/edge count)
- ✅ Fit-to-view auto-scaling

**Does NOT include:**
- ❌ Filter panel (separate component: GraphFilterPanel)
- ❌ Export functionality (in UnifiedGraphView)
- ❌ Multiple layout algorithms (force-directed only)

**Conclusion:** EntityGraph is feature-complete for basic visualization. Advanced features (filters, export) can be added later if needed.

### 4.8 Migration Complexity Assessment

**Complexity:** ⭐⭐☆☆☆ (Low-Medium)

**Reasons:**
- ✅ Self-contained component with no complex dependencies
- ✅ Pure SVG rendering (no D3.js or external graph libs)
- ✅ All NPM dependencies already in AURA-CHAT
- ⚠️ Minor: Need to verify CSS variables match
- ⚠️ Minor: Need to adapt API endpoint calls

**Estimated Effort:** 1-2 hours
1. Copy component file (10 min)
2. Create types file (15 min)
3. Update import paths (5 min)
4. Verify CSS variables (20 min)
5. Create/adapt API endpoint (30 min)
6. Test in AURA-CHAT (20 min)

---

## 5. Shared Utilities Check

**Query:** Find all imports of kg-query from outside the feature

**Command:**
```bash
grep -rn "from.*kg-query\|from.*features/kg-query" AURA-NOTES-MANAGER/frontend/src/ \
  --include="*.tsx" --include="*.ts" | grep -v "^AURA-NOTES-MANAGER/frontend/src/features/kg-query/"
```

**Result:**
```
AURA-NOTES-MANAGER/frontend/src/App.tsx:35:import { KGQueryPage } from './features/kg-query/pages/KGQueryPage'
```

**Conclusion:**
- ✅ **Zero shared utilities** - kg-query exports nothing used by other features
- ✅ **Zero shared types** - No other features import kg-query types
- ✅ **Zero shared components** - EntityGraph not used elsewhere in app
- ✅ **Safe for removal** - Deleting kg-query will not break other features

---

## 6. Removal Steps

### 6.1 File Deletions

**Delete entire feature directory:**
```bash
rm -rf AURA-NOTES-MANAGER/frontend/src/features/kg-query/
```

**Files to remove:** 9 files, ~3,751 lines

### 6.2 App.tsx Updates

**File:** `AURA-NOTES-MANAGER/frontend/src/App.tsx`

**Changes:**
1. **Line 25** - Remove JSDoc dependency reference:
   ```diff
   - *    - Internal: pages/ExplorerPage, features/kg-query/pages/KGQueryPage
   + *    - Internal: pages/ExplorerPage
   ```

2. **Line 35** - Remove import:
   ```diff
   - import { KGQueryPage } from './features/kg-query/pages/KGQueryPage'
   ```

3. **Line 42** - Remove route:
   ```diff
   -                 <Route path="/kg-query" element={<KGQueryPage />} />
   ```

**Verification:**
```bash
npm run build          # Should build successfully
npm run type-check     # Should pass type checking
```

### 6.3 Navigation Menu Updates

**None required.** No navigation menus link to kg-query.

### 6.4 Verification Checklist

After removal, verify:
- [ ] `npm run build` succeeds
- [ ] `npm run type-check` passes
- [ ] `npm run lint` passes
- [ ] No TypeScript errors in IDE
- [ ] App loads successfully at `/`
- [ ] Navigating to `/kg-query` shows 404 (expected)
- [ ] No console errors in browser
- [ ] Git status shows only expected deletions

---

## 7. EntityGraph Migration Checklist

For Phase RC-03 (Frontend Migration):

**Preparation:**
- [ ] Verify AURA-CHAT has graph data API endpoint
- [ ] Confirm CSS variables match between apps
- [ ] Check `lucide-react` version compatibility

**Migration Steps:**
- [ ] Create `AURA-CHAT/client/src/features/graph/` directory
- [ ] Copy `EntityGraph.tsx` to `features/graph/components/`
- [ ] Create `types/graph.types.ts` with GraphData/Node/Edge types
- [ ] Update import paths in EntityGraph
- [ ] Update ENTITY_COLORS (change Topic to #FFD400)
- [ ] Update API endpoint to AURA-CHAT's graph API
- [ ] Test graph rendering with sample data
- [ ] Integrate with AURA-CHAT study session UI

**Testing:**
- [ ] Graph renders with correct colors
- [ ] Zoom/pan controls work
- [ ] Node selection works
- [ ] Hover highlighting works
- [ ] Graph statistics display correctly
- [ ] Mobile responsive (if required)

---

## 8. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Missing CSS variables in AURA-CHAT | Low | Low | Verify and add missing variables to AURA-CHAT theme |
| Graph API endpoint missing | Medium | Medium | Use Phase RC-02 graph preview API or create endpoint |
| Type incompatibility | Low | Low | Types are simple interfaces, easy to adapt |
| Regression in other features | Very Low | High | Zero shared dependencies, isolated removal |
| EntityGraph doesn't render | Low | Medium | Test with sample data before integration |

**Overall Risk:** ⭐⭐☆☆☆ (Low)

---

## 9. Dependencies Summary

### External (npm)
- None unique to kg-query
- All dependencies already in AURA-CHAT

### Internal (within NOTES-MANAGER)
- `@/api/client` - Generic fetch wrapper (stays)
- `@/components/ui/button` - Shared UI component (stays)
- No other features depend on kg-query

### Backend API
- `/v1/kg/*` endpoints - TO REMOVE from NOTES-MANAGER API
- Backend dependency analysis in RC-01-01-PLAN.md

---

## 10. Conclusion

**Removal Safety:** ✅ **SAFE**
- Fully self-contained feature
- Zero shared utilities
- Zero dependent features
- Only impact: users lose access to KG query UI in NOTES-MANAGER

**Migration Viability:** ✅ **VIABLE**
- EntityGraph is well-architected
- No complex external dependencies
- Simple type requirements
- Straightforward API integration

**Next Steps:**
1. ✅ Complete backend dependency mapping (RC-01-01)
2. → Create graph preview API in NOTES-MANAGER (RC-02)
3. → Migrate EntityGraph to AURA-CHAT (RC-03)
4. → Remove kg-query feature (RC-04)
5. → Verify both apps work correctly (RC-05)

---

**Report Generated:** 2026-01-29  
**Analyst:** OpenCode Agent  
**Phase:** RC-01-02 (Frontend Dependency Mapping)
