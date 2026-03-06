---
phase: quick
plan: 6
type: execute
wave: 1
depends_on: []
files_modified:
  - AURA-CHAT/backend/document_processor.py
  - AURA-CHAT/backend/llm_entity_extractor.py
autonomous: true
requirements:
  - FIX-ASYNC-AWAIT
  - FIX-JSON-PARSING
  - FIX-RETRY-LOGIC
must_haves:
  truths:
    - Document nodes are created in Neo4j when processing completes
    - Entity nodes are created in Neo4j when processing completes
    - Relationship nodes are created in Neo4j when processing completes
    - LLM JSON responses are parsed correctly without 'Expecting delimiter' errors
    - Retry logic uses improved prompt/strategy, not just delay
  artifacts:
    - path: AURA-CHAT/backend/document_processor.py
      provides: "Async/await fixes for GraphManager calls"
      min_changes: 7 locations with await added
    - path: AURA-CHAT/backend/llm_entity_extractor.py
      provides: "JSON repair and improved retry logic"
      contains: "_repair_json_string enhanced, _extract_with_repair method"
  key_links:
    - from: document_processor.py line 760
      to: graph_manager.create_document_node
      via: await
    - from: llm_entity_extractor.py _extract_from_batch
      to: json.loads
      via: _repair_json_string fallback
---

<objective>
Fix critical async/await bugs in document processor and JSON parsing issues in entity extractor.

Purpose: Documents currently process but never appear in Neo4j because async GraphManager methods are called without await. Additionally, LLM returns malformed JSON causing 0 entity extraction.

Output: Working document processing pipeline with proper Neo4j persistence and robust JSON parsing.
</objective>

<execution_context>
@./.claude/get-shit-done/workflows/execute-plan.md
@./.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@AURA-CHAT/backend/document_processor.py
@AURA-CHAT/backend/llm_entity_extractor.py

## Critical Issues Found

### 1. Async/Await Bug (document_processor.py)
The following GraphManager method calls are missing `await`:
- Line 760: `graph_manager.create_document_node(doc_params)`
- Line 786: `create_func(entity)` (inside _get_or_create_entity)
- Line 788: `graph_manager.store_entity_embedding(...)`
- Line 856: `graph_manager.store_embedding(...)`
- Line 883: `graph_manager.execute_query(...)` (parent chunk)
- Line 897: `graph_manager.execute_query(...)` (doc-parent link)
- Line 923: `graph_manager.execute_query(...)` (child chunk)
- Line 938: `graph_manager.execute_query(...)` (doc-chunk link)
- Line 951: `graph_manager.execute_query(...)` (parent-child link)

These methods are async (defined with `async def` in graph_manager.py) but are being called synchronously, causing coroutines to be discarded without execution.

### 2. JSON Parsing Issues (llm_entity_extractor.py)
- Lines 599-614: JSONDecodeError handling only retries with delay, doesn't fix the JSON
- The `_repair_json_string` function exists (lines 122-182) but is NOT called in the error handler
- Retry logic at lines 599-614 and 616-631 just retries with same malformed prompt

### 3. Ineffective Retry Logic
- Current retry only adds exponential backoff (line 604: `wait_time = base_backoff * (2**retry_count)`)
- Same prompt sent to LLM, same malformed JSON likely to return
- No JSON repair attempted before retry
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix async/await bugs in document_processor.py</name>
  <files>AURA-CHAT/backend/document_processor.py</files>
  <action>
Add `await` keyword to all async GraphManager method calls in the _store_in_graph method.

Specific lines to fix:
1. Line 760: Change `graph_manager.create_document_node(doc_params)` to `await graph_manager.create_document_node(doc_params)`
2. Line 786: Change `create_func(entity)` to `await create_func(entity)` (inside _get_or_create_entity helper)
3. Line 788: Change `graph_manager.store_entity_embedding(...)` to `await graph_manager.store_entity_embedding(...)`
4. Line 856: Change `graph_manager.store_embedding(...)` to `await graph_manager.store_embedding(...)`
5. Line 883: Change `graph_manager.execute_query(...)` to `await graph_manager.execute_query(...)`
6. Line 897: Change `graph_manager.execute_query(...)` to `await graph_manager.execute_query(...)`
7. Line 923: Change `graph_manager.execute_query(...)` to `await graph_manager.execute_query(...)`
8. Line 938: Change `graph_manager.execute_query(...)` to `await graph_manager.execute_query(...)`
9. Line 951: Change `graph_manager.execute_query(...)` to `await graph_manager.execute_query(...)`

Also ensure the `_get_or_create_entity` helper function properly awaits the async `create_func` callback.

Verify the method signature of `_store_in_graph` is `async def` (it should already be, but confirm).
  </action>
  <verify>
    <automated>cd AURA-CHAT && python -c "import ast; tree = ast.parse(open('backend/document_processor.py').read()); print('Syntax OK')"</automated>
    <manual>Search for 'graph_manager.' in document_processor.py and verify all calls to async methods are awaited</manual>
  </verify>
  <done>All GraphManager async method calls in _store_in_graph have await keyword; no syntax errors</done>
</task>

<task type="auto">
  <name>Task 2: Fix JSON parsing with repair fallback</name>
  <files>AURA-CHAT/backend/llm_entity_extractor.py</files>
  <action>
Modify the JSON parsing logic in `_extract_from_batch` method (around lines 552-567) to use the existing `_repair_json_string` function when JSON parsing fails.

Current code (lines 552-567):
```python
try:
    extracted = json.loads(response_text)
    logger.info(f"Successfully parsed JSON: {list(extracted.keys())}")
except json.JSONDecodeError as e:
    # Fallback: try to extract JSON from response if model includes extra text
    json_start = response_text.find("{")
    json_end = response_text.rfind("}") + 1
    if json_start >= 0 and json_end > json_start:
        json_str = response_text[json_start:json_end]
        extracted = json.loads(json_str)
        logger.info(f"Extracted JSON via fallback: {list(extracted.keys())}")
    else:
        raise e
```

Change to:
```python
try:
    extracted = json.loads(response_text)
    logger.info(f"Successfully parsed JSON: {list(extracted.keys())}")
except json.JSONDecodeError as e:
    # Try to repair JSON first
    logger.warning(f"JSON parse error, attempting repair: {e}")
    repaired = _repair_json_string(response_text)
    try:
        extracted = json.loads(repaired)
        logger.info(f"Successfully parsed repaired JSON: {list(extracted.keys())}")
    except json.JSONDecodeError:
        # Fallback: try to extract JSON from response if model includes extra text
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            # Try to repair the extracted substring too
            repaired_json_str = _repair_json_string(json_str)
            extracted = json.loads(repaired_json_str)
            logger.info(f"Extracted and repaired JSON via fallback: {list(extracted.keys())}")
        else:
            raise e
```

This ensures the existing `_repair_json_string` function (which uses both regex fixes and the json-repair library) is actually invoked when parsing fails.
  </action>
  <verify>
    <automated>cd AURA-CHAT && python -c "import ast; tree = ast.parse(open('backend/llm_entity_extractor.py').read()); print('Syntax OK')"</automated>
    <manual>Verify _repair_json_string is called in the JSONDecodeError handler</manual>
  </verify>
  <done>JSON repair function is invoked when JSON parsing fails; syntax is valid</done>
</task>

<task type="auto">
  <name>Task 3: Improve retry logic with prompt variation</name>
  <files>AURA-CHAT/backend/llm_entity_extractor.py</files>
  <action>
Modify the retry logic in `_extract_from_batch` (lines 599-631) to use a simpler, more explicit prompt on retry instead of just delaying.

Current retry logic just retries with the same prompt and exponential backoff. Change it to:

1. On retry (retry_count > 0), use a simplified prompt that emphasizes JSON format:

```python
def _extract_from_batch(self, batch_text: str, retry_count: int = 0, user_id: str = "") -> Dict[str, List[Dict[str, Any]]]:
    """Extract entities from a single batch with retry logic."""
    max_retries = 3
    base_backoff = 2.0  # seconds

    # Use a simpler prompt on retry to improve JSON compliance
    if retry_count > 0:
        prompt = f"""Extract academic entities from this text into valid JSON.

Categories: concepts, topics, methodologies, findings

Required JSON format:
{{
  "concepts": [{{"name": "...", "definition": "...", "category": "...", "confidence": 0.9, "context": "..."}}],
  "topics": [],
  "methodologies": [],
  "findings": []
}}

Text to analyze:
{batch_text[:2000]}  # Truncate on retry for simplicity

IMPORTANT: Return ONLY valid JSON. No markdown, no explanations."""
    else:
        # Use original full prompt for first attempt
        prompt = f"""<instruction>
... original prompt ...
</instruction>
..."""
```

2. Also truncate batch_text on retry to reduce token count and complexity.

3. Keep the exponential backoff but add the prompt variation strategy.

This ensures retries have a higher chance of success by:
- Using a simpler, more explicit prompt
- Reducing text length to process
- Emphasizing JSON-only output
  </action>
  <verify>
    <automated>cd AURA-CHAT && python -c "import ast; tree = ast.parse(open('backend/llm_entity_extractor.py').read()); print('Syntax OK')"</automated>
    <manual>Verify retry logic uses different prompt on retry_count > 0</manual>
  </verify>
  <done>Retry logic uses simplified prompt and truncated text on retries; syntax is valid</done>
</task>

</tasks>

<verification>
1. All async/await bugs fixed - document_processor.py compiles without errors
2. JSON repair is invoked - llm_entity_extractor.py uses _repair_json_string on parse failure
3. Retry logic improved - uses simplified prompt on retry attempts
4. Integration test: Document processing should now create nodes in Neo4j
</verification>

<success_criteria>
- document_processor.py has `await` before all GraphManager async method calls
- llm_entity_extractor.py calls `_repair_json_string` when JSON parsing fails
- Retry logic in llm_entity_extractor.py uses simplified prompt on retries
- No syntax errors in modified files
- Documents processed after fix appear in Neo4j (verified via Documents Page)
</success_criteria>

<output>
After completion, create `.planning/quick/6-fix-async-await-bugs-and-json-parsing-in/6-SUMMARY.md`
</output>
