---
phase: rc-03-frontend-migration
type: execute
plan: RC-03-04
---

<objective>
Integrate module filtering into AURA-CHAT GraphPage frontend.

Purpose: Make graph visualization respect selected module, matching chat feature's module-aware behavior.
Output: Updated `GraphPage.tsx` reading module from localStorage and passing to API, with module indicator in UI.
</objective>

<execution_context>
@~/.config/opencode/skills/create-plans/workflows/execute-phase.md
@~/.config/opencode/skills/create-plans/templates/summary.md
</execution_context>

<context>
@.planning/phases/rc-03-frontend-migration/MODULE-FILTERING-DECISION.md
@.planning/phases/rc-03-frontend-migration/RC-03-03-PLAN.md
@AURA-CHAT/client/src/features/graph/GraphPage.tsx
@AURA-CHAT/client/src/types/api.ts
@AURA-CHAT/client/src/features/chat/ChatPage.tsx
</context>

<prerequisites>
RC-03-03 (Backend module filtering) must be completed first.
The `/graph/data` endpoint must accept `module_id` query parameter.
</prerequisites>

<tasks>

<task type="auto">
  <name>Task 1: Analyze ChatPage module selection implementation</name>
  <files>AURA-CHAT/client/src/features/chat/ChatPage.tsx</files>
  <action>
    Read ChatPage.tsx to understand how module selection works:
    1. How is the selected module stored? (localStorage key?)
    2. What is the storage format? (string ID or full object?)
    3. How is module selection UI triggered?
    4. What is the module object structure (HierarchyModule)?
    
    Document the localStorage key and retrieval pattern for reuse in GraphPage.
  </action>
  <verify>Documented localStorage key and module retrieval pattern</verify>
  <done>Know how to read selected module in GraphPage</done>
</task>

<task type="auto">
  <name>Task 2: Update GraphQueryParams type</name>
  <files>AURA-CHAT/client/src/types/api.ts</files>
  <action>
    Add module_id to the GraphQueryParams interface:
    
    ```typescript
    export interface GraphQueryParams {
        document_id?: string;
        module_id?: string;     // NEW - Filter by selected module
        node_types?: string[];
        depth?: number;
        limit?: number;
    }
    ```
    
    This enables the API client to pass module_id to the backend.
  </action>
  <verify>TypeScript compiles without errors</verify>
  <done>GraphQueryParams includes module_id field</done>
</task>

<task type="auto">
  <name>Task 3: Create module storage utility function</name>
  <files>AURA-CHAT/client/src/lib/utils.ts OR AURA-CHAT/client/src/features/graph/GraphPage.tsx</files>
  <action>
    Create a reusable function to load selected module from localStorage:
    
    ```typescript
    // If ChatPage already has this in a shared location, import it
    // Otherwise, create inline in GraphPage or in lib/utils.ts
    
    interface StoredModule {
        id: string;
        name: string;
        code?: string;
    }
    
    function loadSelectedModule(): StoredModule | null {
        try {
            const stored = localStorage.getItem('aura_selected_module');
            if (!stored) return null;
            return JSON.parse(stored);
        } catch {
            return null;
        }
    }
    ```
    
    Check ChatPage.tsx first for existing implementation to avoid duplication.
  </action>
  <verify>Function exists and retrieves module correctly</verify>
  <done>Module retrieval utility available for GraphPage</done>
</task>

<task type="auto">
  <name>Task 4: Update GraphPage to use module filter</name>
  <files>AURA-CHAT/client/src/features/graph/GraphPage.tsx</files>
  <action>
    Modify GraphPage to read and apply module filter:
    
    1. Add state for selected module:
       ```typescript
       const [selectedModule, setSelectedModule] = useState<StoredModule | null>(null);
       ```
    
    2. Load module on mount:
       ```typescript
       useEffect(() => {
           const module = loadSelectedModule();
           setSelectedModule(module);
           if (module) {
               setFilters(prev => ({ ...prev, module_id: module.id }));
           }
       }, []);
       ```
    
    3. Listen for storage changes (if module changed in ChatPage):
       ```typescript
       useEffect(() => {
           const handleStorageChange = (e: StorageEvent) => {
               if (e.key === 'aura_selected_module') {
                   const module = loadSelectedModule();
                   setSelectedModule(module);
                   setFilters(prev => ({ 
                       ...prev, 
                       module_id: module?.id 
                   }));
               }
           };
           window.addEventListener('storage', handleStorageChange);
           return () => window.removeEventListener('storage', handleStorageChange);
       }, []);
       ```
    
    4. Update initial filters state:
       ```typescript
       const [filters, setFilters] = useState<GraphQueryParams>(() => {
           const module = loadSelectedModule();
           return {
               limit: 500,
               depth: 2,
               module_id: module?.id,
           };
       });
       ```
  </action>
  <verify>GraphPage loads with module_id in filters</verify>
  <done>GraphPage reads module from storage and applies to filters</done>
</task>

<task type="auto">
  <name>Task 5: Add module indicator to GraphPage header</name>
  <files>AURA-CHAT/client/src/features/graph/GraphPage.tsx</files>
  <action>
    Display the selected module in the page header:
    
    Find the header section (likely near the page title) and add:
    
    ```tsx
    {/* Page Header */}
    <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
            <Network className="w-6 h-6 text-primary" />
            <div>
                <h1 className="text-2xl font-bold">Knowledge Graph</h1>
                {selectedModule && (
                    <p className="text-sm text-muted-foreground">
                        Filtered by: {selectedModule.name}
                        {selectedModule.code && ` (${selectedModule.code})`}
                    </p>
                )}
                {!selectedModule && (
                    <p className="text-sm text-muted-foreground">
                        Showing all modules
                    </p>
                )}
            </div>
        </div>
        {/* existing buttons... */}
    </div>
    ```
  </action>
  <verify>Module name displays in header when selected</verify>
  <done>Module indicator visible in GraphPage header</done>
</task>

<task type="auto">
  <name>Task 6: Add "Clear Module Filter" button</name>
  <files>AURA-CHAT/client/src/features/graph/GraphPage.tsx</files>
  <action>
    Add a button to clear the module filter and show full graph:
    
    ```tsx
    {selectedModule && (
        <button
            onClick={() => {
                setSelectedModule(null);
                setFilters(prev => {
                    const newFilters = { ...prev };
                    delete newFilters.module_id;
                    return newFilters;
                });
            }}
            className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-secondary hover:bg-secondary/80 rounded"
        >
            <X className="w-3 h-3" />
            Clear filter
        </button>
    )}
    ```
    
    Place this near the module indicator or in the filter sidebar.
    
    Note: This only affects the graph view - it doesn't clear the globally
    stored module selection (which affects chat too).
  </action>
  <verify>Clear filter button appears and works</verify>
  <done>"Clear Module Filter" button functional</done>
</task>

<task type="auto">
  <name>Task 7: Update filter sidebar (optional enhancement)</name>
  <files>AURA-CHAT/client/src/features/graph/GraphPage.tsx</files>
  <action>
    Optionally display module info in the filter sidebar:
    
    In the filter section (likely toggleable with Filter icon), add:
    
    ```tsx
    {/* Module Filter Info */}
    <div className="space-y-2 mb-4 pb-4 border-b border-border">
        <label className="text-xs font-medium text-muted-foreground uppercase">
            Module Filter
        </label>
        {selectedModule ? (
            <div className="flex items-center justify-between bg-secondary/50 rounded px-2 py-1.5">
                <span className="text-sm">{selectedModule.name}</span>
                <button
                    onClick={clearModuleFilter}
                    className="text-muted-foreground hover:text-foreground"
                >
                    <X className="w-4 h-4" />
                </button>
            </div>
        ) : (
            <p className="text-sm text-muted-foreground">
                No module selected (showing all)
            </p>
        )}
    </div>
    ```
    
    This is optional if header indicator is sufficient.
  </action>
  <verify>Filter sidebar shows module info (if implemented)</verify>
  <done>Filter sidebar updated with module info</done>
</task>

<task type="auto">
  <name>Task 8: Verify graph data refetches on module change</name>
  <files>AURA-CHAT/client/src/hooks/useGraphQuery.ts</files>
  <action>
    Ensure useGraphQuery properly refetches when module_id changes:
    
    Check that the query key includes module_id:
    ```typescript
    // useGraphQuery should have query key like:
    queryKey: ['graphData', filters]
    // or
    queryKey: ['graphData', filters.module_id, filters.node_types, ...]
    ```
    
    If filters object is in query key, changes should trigger refetch automatically.
    
    If not, update the query key to include module_id.
  </action>
  <verify>Changing module_id triggers graph data refetch</verify>
  <done>Query refetches when module changes</done>
</task>

<task type="auto">
  <name>Task 9: Build and type check</name>
  <files>AURA-CHAT/client/</files>
  <action>
    Run TypeScript compilation and verify no errors:
    
    ```bash
    cd AURA-CHAT/client && npm run build
    ```
    
    Fix any TypeScript errors before proceeding.
  </action>
  <verify>Build completes without errors</verify>
  <done>Frontend builds successfully with module filtering changes</done>
</task>

<task type="auto">
  <name>Task 10: Manual end-to-end verification</name>
  <files>N/A</files>
  <action>
    Test the complete module filtering flow:
    
    1. Start backend server:
       ```bash
       cd AURA-CHAT/server && python main.py
       ```
    
    2. Start frontend dev server:
       ```bash
       cd AURA-CHAT/client && npm run dev
       ```
    
    3. Test scenarios:
       a. Open ChatPage, select a module from hierarchy
       b. Navigate to GraphPage - should show module name in header
       c. Graph should only show entities from selected module
       d. Click "Clear filter" - graph should show all modules
       e. Return to ChatPage, select different module
       f. Navigate back to GraphPage - should reflect new module
    
    4. Verify browser console has no errors
    
    Document results.
  </action>
  <verify>End-to-end flow works: select module → graph filters correctly</verify>
  <done>Full integration verified working</done>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] GraphQueryParams type includes module_id
- [ ] GraphPage reads module from localStorage
- [ ] GraphPage passes module_id to useGraphQuery
- [ ] Module name displayed in GraphPage header
- [ ] "Clear filter" button works
- [ ] Graph refetches when module changes
- [ ] Build passes without TypeScript errors
- [ ] Manual E2E test confirms functionality
</verification>

<success_criteria>
- All tasks completed
- Graph filters to selected module's entities
- Module indicator visible in GraphPage header
- User can clear module filter to see full graph
- No TypeScript or runtime errors
- Chat and Graph share same module selection (consistent UX)
</success_criteria>

<output>
After completion, create `.planning/phases/rc-03-frontend-migration/RC-03-04-SUMMARY.md`
</output>
