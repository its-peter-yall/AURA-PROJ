# 09-04-SUMMARY: Entity-Entity Relationship Extraction

**Status:** ✅ COMPLETE  
**Date:** January 24, 2026  
**Plan:** `09-04-PLAN.md`

---

## Objective

Added entity-entity relationship extraction to AURA-NOTES-MANAGER to enable multi-hop graph reasoning by extracting semantic relationships between entities (DEFINES, DEPENDS_ON, USES, etc.).

---

## Changes Made

### 1. AURA-NOTES-MANAGER/services/llm_entity_extractor.py

**New Configuration Constants:**
```python
LLM_RELATIONSHIP_MIN_CONFIDENCE = 0.3
LLM_RELATIONSHIP_MAX_PER_DOCUMENT = 50
LLM_RELATIONSHIP_MAX_PER_ENTITY = 10
RELATIONSHIP_TYPES = [
    "DEFINES", "DEPENDS_ON", "USES", "SUPPORTS", "CONTRADICTS",
    "EXTENDS", "IMPLEMENTS", "REFERENCES", "RELATED_TO"
]
```

**New Pydantic Model - `Relationship`:**
```python
class Relationship(BaseModel):
    source_entity: str      # Name of the source entity
    target_entity: str      # Name of the target entity
    relationship_type: Literal[...]  # One of 9 relationship types
    confidence: float       # 0.0-1.0 confidence score
    evidence: Optional[str] # Text supporting the relationship (max 300 chars)
```

**New Methods Added:**
| Method | Purpose |
|--------|---------|
| `_build_relationship_prompt()` | Builds LLM prompt with entity context |
| `_flatten_entities()` | Converts entity dict to flat list |
| `_build_entity_name_map()` | Case-insensitive name lookup map |
| `extract_relationships()` | Main relationship extraction (2nd pass) |
| `_extract_relationships_via_llm()` | LLM call with retry logic |
| `_validate_relationships()` | Filters invalid relationships |
| `_deduplicate_relationships()` | Removes duplicates, limits per-entity |
| `extract_entities_and_relationships()` | Combined two-pass extraction |
| `_build_test_relationships()` | Mock relationships for test mode |

### 2. AURA-NOTES-MANAGER/api/kg_processor.py

**Updated Imports:**
```python
from services.llm_entity_extractor import (
    LLMEntityExtractor,
    ExtractedEntity,
    Relationship as EntityRelationship,  # NEW
)
```

**New Processing Step (Step 4.5):**
- Added entity-entity relationship extraction after entity extraction
- Calls `_llm_extractor.extract_relationships()` with text and entities
- Adds `relationship_count` to processing result

**New Storage Step (Step 5.5):**
- Stores entity-entity relationships in Neo4j after entity storage
- Calls `_store_entity_relationships()` method

**New Methods Added:**
| Method | Purpose |
|--------|---------|
| `_prepare_entities_for_relationship_extraction()` | Converts Entity objects to dict format |
| `_build_entity_name_to_id_map()` | Maps entity names to IDs |
| `_get_entity_type_by_name()` | Looks up entity type by name |
| `_store_entity_relationships()` | Stores relationships as Neo4j edges |
| `_create_entity_relationship()` | Creates single Neo4j edge with properties |

---

## Relationship Types Supported

| Type | Description | Example |
|------|-------------|---------|
| DEFINES | A defines/explains B | "Neural Network defines hidden layers" |
| DEPENDS_ON | A requires/needs B | "CNN depends on backpropagation" |
| USES | A uses/applies B | "Model uses gradient descent" |
| SUPPORTS | A provides evidence for B | "Results support hypothesis" |
| CONTRADICTS | A conflicts with B | "Study contradicts prior findings" |
| EXTENDS | A builds upon B | "ResNet extends CNN architecture" |
| IMPLEMENTS | A is implementation of B | "TensorFlow implements autodiff" |
| REFERENCES | A cites/mentions B | "Paper references Smith et al." |
| RELATED_TO | Generic relationship | Fallback for unclear relationships |

---

## Two-Pass Extraction Approach

```
┌─────────────────────────────────────────────────────────┐
│                  PASS 1: ENTITY EXTRACTION               │
│                                                          │
│  Text ──► extract_entities() ──► {concepts, topics, ...} │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│               PASS 2: RELATIONSHIP EXTRACTION            │
│                                                          │
│  Text + Entities ──► extract_relationships() ──► [Rel]   │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              COMBINED CONVENIENCE METHOD                 │
│                                                          │
│  extract_entities_and_relationships() ──► (entities, rels)│
└─────────────────────────────────────────────────────────┘
```

---

## Neo4j Relationship Storage

**Cypher Pattern:**
```cypher
MATCH (source:{SourceType} {id: $source_id, module_id: $module_id})
MATCH (target:{TargetType} {id: $target_id, module_id: $module_id})
MERGE (source)-[r:{REL_TYPE}]->(target)
SET r.confidence = $confidence,
    r.evidence = $evidence,
    r.created_at = datetime()
```

**Properties Stored:**
- `confidence`: Float 0.0-1.0
- `evidence`: Text snippet (max 300 chars)
- `created_at`: Timestamp

---

## Validation Rules

1. **Self-relationships filtered**: A → A relationships are skipped
2. **Entity existence checked**: Both source and target must exist in extracted entities
3. **Relationship type validated**: Must be one of 9 defined types
4. **Confidence threshold**: Only relationships with confidence ≥ 0.3 stored
5. **Deduplication**: Duplicate (source, target, type) tuples keep highest confidence
6. **Per-entity limit**: Max 10 relationships per source entity
7. **Per-document limit**: Max 50 relationships per document

---

## Success Criteria Verification

- [x] `extract_relationships()` method added to LLMEntityExtractor
- [x] `Relationship` Pydantic model with all required fields
- [x] All 9 relationship types extractable
- [x] Two-pass extraction (entities then relationships) works
- [x] Entity-entity edges stored in Neo4j
- [x] Relationship properties (confidence, evidence) present
- [x] Invalid relationships filtered out
- [x] `py_compile` passes for all files

---

## Verification Commands

```bash
# Syntax check
python -m py_compile AURA-NOTES-MANAGER/services/llm_entity_extractor.py
python -m py_compile AURA-NOTES-MANAGER/api/kg_processor.py

# After processing a document, verify in Neo4j:
# Count relationships
MATCH (e1:Entity)-[r]->(e2:Entity) RETURN count(r)

# Relationship types
MATCH (e1)-[r]->(e2) 
WHERE e1:Topic OR e1:Concept OR e1:Methodology OR e1:Finding
RETURN DISTINCT type(r)

# Relationship properties
MATCH (e1:Concept)-[r]->(e2:Concept) 
RETURN r.confidence, r.evidence LIMIT 5
```

---

## Next Steps

- **09-05-PLAN**: Add entity embeddings for Topic, Concept, Methodology, Finding
- **09-06-PLAN**: Add semantic deduplication with 0.85 cosine threshold
