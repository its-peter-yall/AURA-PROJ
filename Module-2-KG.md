# AURA Module-to-Knowledge Graph (M2KG) Implementation Plan

**Document Version:** 1.0
**Author:** Senior Software Architect, AURA Corporation
**Date:** 2026-01-18
**Status:** Draft - For Review
**Classification:** Internal Technical Document

---

## 1. Executive Summary

This document outlines the comprehensive implementation plan for AURA's new **Module-to-Knowledge Graph (M2KG)** feature. This feature enables academic staff to pre-process academic modules into Neo4j knowledge graphs, allowing students to selectively import modules into their study session and engage in contextual AI-powered conversations.

The M2KG feature transforms AURA from a document-processing system into a structured educational knowledge platform where content is organized by academic modules, pre-processed into knowledge graphs, and made available for intelligent retrieval during student study sessions.

### 1.1 Strategic Objectives

| Objective | Description | Success Metric |
|-----------|-------------|----------------|
| **Content Reuse** | Leverage staff-created notes across entire student body | 80% content reuse rate |
| **Study Efficiency** | Enable focused module-specific AI tutoring | 50% reduction in study time |
| **Cross-Module Learning** | Support queries spanning related modules | Native cross-module queries |
| **Scalability** | Support 1000+ modules across 8 semesters | <200ms query response time |
| **Quality Assurance** | Staff review before content goes live | 100% reviewed content |

### 1.2 High-Level Workflow

The system operates through two distinct user journeys:

**Academic Staff Journey:**
1. Staff member creates or updates notes in the existing hierarchical system
2. Staff member selects a module and triggers "Convert to Knowledge Graph"
3. System processes all notes in the module through the document processing pipeline
4. System stores entities, relationships, and chunks in Neo4j with module_id tagging
5. Staff member reviews the generated knowledge graph
6. Staff member publishes the module to make it available to students

**Student Journey:**
1. Student logs into AURA and navigates to "Study" section
2. Student browses available modules organized by department → semester → subject
3. Student selects modules they want to study (e.g., "Database Systems - Module 2")
4. System loads the knowledge graph for those modules into the chat context
5. Student engages with AI tutor, asking questions specific to the selected modules
6. System returns answers with citations pointing to specific module content

---

## 2. Architecture Overview

### 2.1 System Architecture Principles

The M2KG implementation follows these architectural principles:

**Principle 1: Single Graph, Logical Partitioning**
All knowledge graph data resides in a single Neo4j database, logically partitioned by module_id. This approach enables efficient cross-module queries while maintaining clear data boundaries. Each node (Document, Chunk, Entity) carries a module_id property that acts as a partitioning key.

**Principle 2: Separation of Concerns**
The system maintains clear separation between:
- Content creation (existing hierarchy system)
- Knowledge graph processing (M2KG processor)
- Retrieval and generation (RAG engine)
- User interaction (frontend components)

**Principle 3: Event-Driven Processing**
Module processing uses an asynchronous, event-driven architecture via Celery tasks. This ensures that large module processing operations do not block the main application and allows for proper error handling and retry mechanisms.

**Principle 4: Cache-First Architecture**
Frequently accessed module metadata uses Redis caching to reduce database load. The cache layer sits between API endpoints and Neo4j, providing sub-100ms response times for common queries.

### 2.2 Data Flow Architecture

**Staff Side Data Flow:**
```
Notes (PDF/TXT) in Hierarchy System
            │
            ▼
    ┌─────────────────────────┐
    │ Module Selection UI     │
    │ (Staff Portal)          │
    └─────────────────────────┘
            │
            ▼
    ┌─────────────────────────┐
    │ Module Processing Queue │
    │ (Celery Tasks)          │
    └─────────────────────────┘
            │
            ▼
    ┌─────────────────────────┐
    │ Document Processor      │
    │ • Parse text            │
    │ • Extract entities      │
    │ • Create chunks         │
    │ • Generate embeddings   │
    └─────────────────────────┘
            │
            ▼
    ┌─────────────────────────┐
    │ Neo4j Knowledge Graph   │
    │ • Store with module_id  │
    │ • Create relationships  │
    │ • Build entity graph    │
    └─────────────────────────┘
```

**Student Side Data Flow:**
```
Student Module Selection
            │
            ▼
    ┌─────────────────────────┐
    │ Session Context Manager │
    │ • Track selected IDs    │
    │ • Maintain chat history │
    │ • Cache module metadata │
    └─────────────────────────┘
            │
            ▼
    ┌─────────────────────────┐
    │ RAG Engine              │
    │ • Build query           │
    │ • Filter by module_id   │
    │ • Retrieve chunks       │
    │ • Expand graph context  │
    └─────────────────────────┘
            │
            ▼
    ┌─────────────────────────┐
    │ LLM Response            │
    │ • Generate answer       │
    │ • Add citations         │
    │ • Return to student     │
    └─────────────────────────┘
```

---

## 3. Data Model Design

### 3.1 Core Design Decision: Single Graph with Property-Based Partitioning

After extensive analysis of Neo4j multi-tenancy patterns, the recommended approach is a **single graph with property-based partitioning** rather than separate databases per module. This decision is based on:

1. **Cross-Module Queries**: Students and staff may need to query across related modules
2. **Operational Simplicity**: Managing 1000+ separate databases is operationally complex
3. **Query Performance**: Native indexes on module_id provide O(log n) filtering
4. **Backup Efficiency**: Single database backup is straightforward
5. **Neo4j Scalability**: Modern Neo4j handles 10M+ nodes efficiently

### 3.2 Node Schema Specifications

**Document Node:**
- `id`: Unique identifier (UUID)
- `title`: Document title
- `module_id`: Reference to parent module (CRITICAL for filtering)
- `subject_id`: Academic subject reference
- `semester`: Semester number (1-8)
- `department`: Department name
- `authors`: Document authors
- `original_filename`: Source file name
- `upload_date`: ISO timestamp
- `kg_processed`: Boolean flag
- `kg_processed_at`: Processing completion timestamp
- `embedding`: 768-dimensional vector
- `content`: Full text content

**Chunk Node:**
- `id`: Unique identifier (UUID)
- `module_id`: Reference to parent module (CRITICAL for filtering)
- `text`: Chunk text content
- `token_count`: Number of tokens
- `index`: Position in document
- `parent_index`: Parent chunk reference
- `embedding`: 768-dimensional vector
- `type`: "parent" or "child"

**Entity Node (Concept, Topic, Methodology, Finding):**
- `id`: Unique identifier (UUID)
- `module_id`: Reference to parent module (CRITICAL for filtering)
- `name`: Entity name
- `definition`: Entity definition
- `category`: Entity category
- `confidence`: Extraction confidence score
- `context`: Source text excerpt
- `embedding`: 768-dimensional vector
- `occurrences`: Frequency count
- `first_mentioned_in`: Reference to chunk

**Module Node (NEW):**
- `id`: Module identifier (matches module_id in other nodes)
- `code`: Module code (e.g., "CS201")
- `name`: Module name
- `subject_id`: Parent subject reference
- `semester`: Semester number
- `department`: Department name
- `description`: Module description
- `note_count`: Number of notes
- `kg_status`: Status (draft, processing, published, archived)
- `kg_processed_at`: Processing timestamp
- `created_by`: Staff creator reference
- `published_at`: Publication timestamp
- `embedding`: Module-level embedding for search

### 3.3 Relationship Schema

**Core Relationships:**
- `(:Document)-[:BELONGS_TO_MODULE]->(:Module)` - Links documents to modules
- `(:Document)-[:HAS_CHUNK]->(:Chunk)` - Links documents to chunks
- `(:ParentChunk)-[:HAS_CHILD]->(:Chunk)` - Parent-child chunk hierarchy
- `(:Chunk)-[:CONTAINS_ENTITY]->(:Entity)` - Links chunks to entities
- `(:Document)-[:ADDRESSES_TOPIC]->(:Topic)` - Document-topic relationship
- `(:Document)-[:MENTIONS_CONCEPT]->(:Concept)` - Document-concept relationship
- `(:Entity)-[:DEFINES|DEPENDS_ON|USES|RELATED_TO]->(:Entity)` - Entity relationships

**Study Session Relationships:**
- `(:Student)-[:STUDIES_MODULE]->(:Module)` - Student's selected modules
- `(:Student)-[:HAS_SESSION]->(:Session)` - Student chat sessions

---

## 4. API Design

### 4.1 API Design Principles

All APIs follow RESTful conventions with:
- Consistent URL naming (plural nouns, kebab-case)
- Standard HTTP methods (GET, POST, PUT, DELETE)
- Proper HTTP status codes (200, 201, 400, 401, 403, 404, 500)
- JSON request/response bodies
- Pagination for list endpoints
- Rate limiting on write operations

### 4.2 Module Management Endpoints

| Endpoint | Method | Description | Auth Level |
|----------|--------|-------------|------------|
| `/api/modules` | GET | List all available modules | Student |
| `/api/modules/{id}` | GET | Get detailed module information | Student |
| `/api/modules/{id}/documents` | GET | List documents in a module | Student |
| `/api/modules/{id}/entities` | GET | List entities extracted from module | Student |
| `/api/modules/{id}/statistics` | GET | Get module processing statistics | Student |
| `/api/modules/{id}/kg-status` | GET | Get KG processing status | Staff |
| `/api/modules/{id}/process` | POST | Trigger KG processing | Staff |
| `/api/modules/{id}/publish` | POST | Publish module to students | Staff |
| `/api/modules/{id}/unpublish` | POST | Unpublish module from students | Staff |
| `/api/modules/{id}` | PUT | Update module metadata | Staff |
| `/api/modules/batch/process` | POST | Batch process multiple modules | Staff |

### 4.3 Student Selection Endpoints

| Endpoint | Method | Description | Auth Level |
|----------|--------|-------------|------------|
| `/api/student/modules/available` | GET | Get modules available to student | Student |
| `/api/student/modules/selected` | GET | Get student's currently selected modules | Student |
| `/api/student/modules/select` | POST | Select modules for study session | Student |
| `/api/student/modules/deselect` | POST | Deselect modules from study session | Student |
| `/api/student/modules/import` | POST | Import selected modules to chat | Student |
| `/api/student/sessions/{id}` | GET | Get session details | Student |
| `/api/student/sessions/{id}/modules` | GET | Get modules in session | Student |

### 4.4 Knowledge Graph Query Endpoints

| Endpoint | Method | Description | Auth Level |
|----------|--------|-------------|------------|
| `/api/kg/search` | POST | Search KG with module filtering | Both |
| `/api/kg/concepts` | GET | Get concepts for module(s) | Both |
| `/api/kg/relationships` | GET | Get relationships for module(s) | Both |
| `/api/kg/cross-module` | POST | Query across multiple modules | Both |
| `/api/kg/entity/{id}` | GET | Get specific entity details | Both |

### 4.5 Chat Integration Endpoints

| Endpoint | Method | Description | Auth Level |
|----------|--------|-------------|------------|
| `/api/chat/query` | POST | Query with active module context | Student |
| `/api/chat/session` | GET | Get current session state | Student |
| `/api/chat/modules` | GET | Get modules in current session | Student |
| `/api/chat/context` | GET | Get retrieval context for session | Student |

---

## 5. Implementation Plan

### 5.1 Phase 1: Foundation (Weeks 1-2)

**Objective:** Establish core data models, database schema, and basic module management

**Deliverables:**
1. Database schema migration script
2. Module node CRUD operations in GraphManager
3. Basic module API endpoints
4. Configuration parameters for M2KG feature

**Key Tasks:**

**Task 1.1: Database Schema Migration**
- Create migration script to add module_id to existing nodes
- Create Module nodes for existing content
- Establish relationships between documents and modules
- Create required indexes for module filtering
- Test migration on staging environment
- Document rollback procedure

**Task 1.2: GraphManager Module Methods**
- Add create_module_node() method
- Add get_module() method
- Add update_module_status() method
- Add get_module_documents() method
- Add get_modules_by_semester() method
- Add get_modules_by_department() method
- Ensure all existing queries respect module boundaries

**Task 1.3: Configuration Updates**
- Add M2KG_ENABLED flag
- Add M2KG_BATCH_SIZE parameter
- Add M2KG_MAX_MODULES_PER_SESSION parameter
- Add M2KG_SESSION_TIMEOUT parameter
- Add M2KG_CACHE_TTL parameter
- Update environment variable documentation

**Task 1.4: Basic API Endpoints**
- Implement GET /api/modules endpoint with filtering
- Implement GET /api/modules/{id} endpoint
- Implement GET /api/modules/{id}/documents endpoint
- Add proper authentication and authorization checks
- Implement pagination for list endpoints

**Best Practices to Follow:**
- Use database transactions for all write operations
- Implement idempotent API operations
- Use proper HTTP status codes
- Implement request validation using Pydantic models
- Add comprehensive logging for debugging
- Use connection pooling for Neo4j connections

### 5.2 Phase 2: Knowledge Graph Integration (Weeks 3-5)

**Objective:** Implement module-aware knowledge graph processing and retrieval

**Deliverables:**
1. Enhanced document processor with module awareness
2. Module-filtered RAG retrieval
3. Cross-module query support
4. Performance-optimized queries

**Key Tasks:**

**Task 2.1: Enhanced Document Processor**
- Modify document processor to accept module_id parameter
- Ensure module_id is propagated to all generated nodes
- Add module-level metadata storage
- Implement batch processing for multiple notes in a module
- Add progress tracking for module processing

**Task 2.2: RAG Engine Module Filtering**
- Modify _retrieve_context() to accept module_ids parameter
- Implement module-filtered vector search
- Implement module-filtered fulltext search
- Implement module-filtered entity retrieval
- Ensure all retrieval operations respect module boundaries
- Add fallback behavior when no modules selected

**Task 2.3: Cross-Module Query Support**
- Implement get_cross_module_concepts() method
- Implement related_concepts_across_modules() method
- Support queries like "How does SQL relate to Database Design?"
- Optimize cross-module queries for performance
- Add caching for common cross-module queries

**Task 2.4: Query Optimization**
- Create indexes for module_id on all node types
- Optimize vector search queries with module filtering
- Optimize relationship queries for module-scoped traversal
- Implement query result caching
- Add query performance monitoring

**Best Practices to Follow:**
- Use parameterized queries to prevent injection
- Implement proper index creation and maintenance
- Use query profiling to identify bottlenecks
- Implement circuit breaker pattern for database calls
- Use bulk operations instead of individual queries
- Implement proper error handling and recovery

### 5.3 Phase 3: Processing Pipeline (Weeks 6-7)

**Objective:** Implement asynchronous module processing with Celery

**Deliverables:**
1. Celery tasks for module processing
2. Progress tracking and status updates
3. Error handling and retry mechanisms
4. Batch processing support

**Key Tasks:**

**Task 3.1: Celery Task Implementation**
- Create process_module task
- Create batch_process_modules task
- Create cleanup_failed_processing task
- Implement task retry with exponential backoff
- Add task timeout handling
- Implement task result storage

**Task 3.2: Progress Tracking**
- Update module status during processing (pending → processing → ready/failed)
- Track individual note processing progress
- Store processing statistics (documents processed, entities extracted, chunks created)
- Provide progress updates via API endpoint
- Implement progress visualization in staff portal

**Task 3.3: Error Handling**
- Implement proper exception handling in processing tasks
- Store error details for debugging
- Implement automatic retry for transient failures
- Add alerting for repeated failures
- Create dead letter queue for unprocessable items

**Task 3.4: Module Publication Workflow**
- Implement draft → processing → review → published workflow
- Add staff review interface
- Implement publish/unpublish operations
- Add version tracking for module content
- Implement rollback capability

**Best Practices to Follow:**
- Use idempotent task design
- Implement proper task acknowledgment
- Use task priority queues for urgent processing
- Monitor task queue lengths and processing times
- Implement proper logging for task execution
- Use heartbeats for long-running tasks

### 5.4 Phase 4: Caching Layer (Week 8)

**Objective:** Implement Redis caching for frequently accessed data

**Deliverables:**
1. Module metadata cache
2. Student session cache
3. Query result cache
4. Cache invalidation strategy

**Key Tasks:**

**Task 4.1: Module Metadata Cache**
- Implement ModuleCache class
- Cache module details (name, description, statistics)
- Cache module entity lists
- Implement TTL-based expiration
- Implement cache invalidation on updates

**Task 4.2: Student Session Cache**
- Cache student's selected modules
- Cache active session data
- Implement session timeout handling
- Support session persistence across browser sessions
- Cache chat history for active sessions

**Task 4.3: Query Result Cache**
- Cache frequent search results
- Implement cache key generation
- Set appropriate cache TTLs
- Implement cache warming for popular modules
- Monitor cache hit rates

**Task 4.4: Cache Invalidation**
- Implement automatic invalidation on updates
- Support selective invalidation by module
- Implement event-driven cache invalidation
- Add cache monitoring and statistics
- Implement cache warming strategies

**Best Practices to Follow:**
- Use appropriate TTL values for different data types
- Implement cache key versioning
- Use connection pooling for Redis
- Implement proper error handling for cache failures
- Monitor cache memory usage
- Use compression for large cached objects

### 5.5 Phase 5: Frontend Development (Weeks 9-10)

**Objective:** Build user interface for module browsing and study sessions

**Deliverables:**
1. Module browser component
2. Module selection interface
3. Study session chat interface
4. Staff administration interface

**Key Tasks:**

**Task 5.1: Module Browser Component**
- Create hierarchical module navigation (Department → Semester → Subject → Module)
- Display module cards with status indicators
- Implement search and filtering
- Show module statistics and KG status
- Add loading states and error handling

**Task 5.2: Module Selection Interface**
- Implement multi-select functionality
- Display selected modules summary
- Show module compatibility indicators
- Implement import to session functionality
- Add selection persistence

**Task 5.3: Study Session Chat**
- Create chat interface with module context
- Display active modules in sidebar
- Show citations pointing to modules
- Implement conversation history
- Add module switching during chat

**Task 5.4: Staff Administration Interface**
- Create module processing queue view
- Implement bulk actions (batch process, publish, unpublish)
- Display processing progress
- Show error logs for failed processing
- Implement module comparison view

**Best Practices to Follow:**
- Use proper component composition
- Implement proper state management
- Add loading and error states
- Use responsive design principles
- Implement proper accessibility
- Add proper keyboard navigation

### 5.6 Phase 6: Testing (Week 11)

**Objective:** Comprehensive testing of all components

**Deliverables:**
1. Unit test suite
2. Integration test suite
3. Performance test suite
4. User acceptance testing

**Key Tasks:**

**Task 6.1: Unit Testing**
- Write tests for all GraphManager module methods
- Write tests for RAG engine module filtering
- Write tests for API endpoints
- Write tests for caching layer
- Achieve minimum 90% code coverage

**Task 6.2: Integration Testing**
- Test complete module processing flow
- Test module selection to chat integration
- Test cross-module query functionality
- Test error handling and recovery
- Test authentication and authorization

**Task 6.3: Performance Testing**
- Measure API response times under load
- Test module processing throughput
- Measure query performance with large datasets
- Test caching effectiveness
- Establish performance baselines

**Task 6.4: User Acceptance Testing**
- Create test scenarios for staff workflow
- Create test scenarios for student workflow
- Conduct user testing sessions
- Gather feedback and iterate
- Sign off on feature completion

**Best Practices to Follow:**
- Use pytest for test framework
- Implement fixtures for test data
- Use mocking for external dependencies
- Implement test parallelization
- Use continuous integration for test automation
- Maintain test data factories

### 5.7 Phase 7: Deployment (Week 12)

**Objective:** Deploy feature to production

**Deliverables:**
1. Production deployment
2. Monitoring setup
3. Documentation completion
4. Training completion

**Key Tasks:**

**Task 7.1: Pre-Deployment**
- Complete all code reviews
- Run full test suite
- Create production database backup
- Update configuration for production
- Set up monitoring dashboards

**Task 7.2: Database Migration**
- Run schema migration script
- Verify migration success
- Test rollback procedure
- Monitor database performance post-migration

**Task 7.3: Service Deployment**
- Deploy backend services
- Deploy frontend assets
- Verify health checks
- Monitor error logs
- Verify all endpoints functional

**Task 7.4: Post-Deployment**
- Monitor system metrics
- Address any production issues
- Collect user feedback
- Complete documentation
- Conduct training sessions

**Best Practices to Follow:**
- Use blue-green deployment strategy
- Implement proper monitoring and alerting
- Use feature flags for gradual rollout
- Maintain rollback capability
- Document all configuration changes
- Communicate changes to stakeholders

---

## 6. Security Design

### 6.1 Access Control Matrix

| Resource | Staff Role | Student Role | Admin Role |
|----------|------------|--------------|------------|
| Module CRUD | Read/Write (own dept) | Read (published only) | Full |
| Module Processing | Write (own dept) | None | Full |
| Module Publish | Write (own dept) | None | Full |
| Student Selection | None | Write (own) | Read (all) |
| Study Session | None | Write (own) | Read (all) |
| Statistics | Read (own dept) | Read (selected) | Full |
| System Config | None | None | Full |

### 6.2 Authentication and Authorization

**Authentication:**
- All API endpoints require JWT authentication
- Tokens include user role and department
- Tokens expire after configurable duration

**Authorization:**
- Middleware checks user role before processing requests
- Staff members can only access modules in their department
- Students can only access published modules
- All write operations require authentication

### 6.3 Data Validation

**Input Validation Rules:**
- Module codes must be alphanumeric (uppercase)
- Module IDs must be valid UUIDs
- Module selection limited to maximum 10 modules per session
- Query parameters must be within allowed ranges
- File uploads validated for type and size

**Validation Libraries:**
- Use Pydantic models for request validation
- Implement custom validators for business logic
- Return clear error messages for validation failures

### 6.4 Audit Logging

**Logged Events:**
- Module creation and modification
- Module processing initiation and completion
- Module publication and unpublication
- Student module selection and deselection
- Chat queries with context
- Authentication failures
- Authorization failures

**Log Format:**
```json
{
  "timestamp": "2026-01-18T10:30:00Z",
  "user_id": "user_123",
  "action": "module.process",
  "resource": "mod_cs_001",
  "department": "Computer Science",
  "result": "success",
  "details": {...}
}
```

---

## 7. Performance Considerations

### 7.1 Index Strategy

**Required Indexes:**

1. **Primary Lookup Indexes:**
   - `CREATE INDEX document_module_id_index FOR (d:Document) ON (d.module_id)`
   - `CREATE INDEX chunk_module_id_index FOR (c:Chunk) ON (c.module_id)`
   - `CREATE INDEX entity_module_id_index FOR (e:Entity) ON (e.module_id)`
   - `CREATE INDEX module_id_index FOR (m:Module) ON (m.id)`

2. **Vector Indexes:**
   - `CREATE VECTOR INDEX chunk_vector_index FOR (c:Chunk) ON (c.embedding)`
   - `CREATE VECTOR INDEX entity_embedding_index FOR (e:Entity) ON (e.embedding)`

3. **Fulltext Indexes:**
   - `CREATE FULLTEXT INDEX chunk_text_index FOR (c:Chunk) ON (c.text)`

### 7.2 Query Optimization Guidelines

**Do:**
- Always filter by module_id early in queries
- Use indexed properties for lookups
- Limit result sets with LIMIT clause
- Use OPTIONAL MATCH for optional relationships
- Profile queries before deployment

**Don't:**
- Use variable-length paths without bounds
- Perform full graph scans
- Return unnecessary properties
- Chain multiple OPTIONAL MATCH clauses
- Use COLLECT without LIMIT

### 7.3 Caching Strategy

**Cache Layers:**
1. **Redis Cache:** Module metadata, student selections, query results
2. **Application Cache:** Embedding vectors, frequently accessed entities
3. **Database Cache:** Neo4j internal cache for hot nodes

**Cache Invalidation:**
- Automatic TTL-based expiration (5 minutes default)
- Event-driven invalidation on data updates
- Manual invalidation for administrative actions

### 7.4 Performance Targets

| Operation | Target P95 | Target P99 |
|-----------|------------|------------|
| Module List API | <100ms | <200ms |
| Module Detail API | <50ms | <100ms |
| Vector Search with Filter | <150ms | <300ms |
| Cross-Module Query | <300ms | <500ms |
| Module Processing (per note) | <5s | <10s |
| Full Module Processing | <30s | <60s |

---

## 8. Affected Files Reference

### 8.1 AURA-PROTO-2 Backend Files (To Modify)

| File | Impact Level | Key Changes |
|------|--------------|-------------|
| `backend/graph_manager.py` | **CRITICAL** | Add module_id to all nodes, add Module CRUD methods, optimize queries |
| `backend/rag_engine.py` | **CRITICAL** | Add module_ids parameter to retrieval, implement module-filtered search |
| `backend/document_processor.py` | **HIGH** | Add module_id propagation, enhance batch processing |
| `backend/llm_entity_extractor.py` | **MEDIUM** | Add module_id to entity output |
| `backend/entity_aware_chunker.py` | **LOW** | Preserve module_id through processing |
| `backend/semantic_chunker.py` | **LOW** | Preserve module_id through processing |
| `backend/utils/config.py` | **LOW** | Add M2KG configuration parameters |
| `backend/utils/embeddings.py` | **LOW** | Add batch embedding support |

### 8.2 AURA-PROTO-2 Backend Files (To Create)

| File | Purpose |
|------|---------|
| `backend/module_manager.py` | Module CRUD and state management service |
| `backend/kg_processor.py` | Module-aware knowledge graph processing |
| `backend/session_manager.py` | Student session and module selection management |
| `backend/module_querier.py` | Module-aware knowledge graph queries |
| `backend/tasks/module_processing_tasks.py` | Celery tasks for async processing |
| `backend/cache/module_cache.py` | Redis caching for module data |
| `backend/middleware/auth_module_filter.py` | Access control middleware |
| `backend/validators/module_validators.py` | Input validation models |
| `schemas/module.py` | Pydantic models for module API |
| `schemas/study_session.py` | Pydantic models for sessions |
| `routers/modules.py` | Module management API endpoints |
| `routers/study_sessions.py` | Session management endpoints |
| `scripts/migrate_add_module_partitioning.py` | Database migration script |

### 8.3 AURA-PROTO Frontend Files (To Modify)

| File | Impact Level | Key Changes |
|------|--------------|-------------|
| `frontend/src/App.tsx` | **HIGH** | Add Study routes and module pages |
| `frontend/src/components/layout/Sidebar.tsx` | **MEDIUM** | Add Module and Study navigation |
| `frontend/src/pages/ExplorerPage.tsx` | **MEDIUM** | Add Convert to KG context menu option |
| `frontend/src/components/explorer/ContextMenu.tsx` | **MEDIUM** | Add KG processing actions |
| `frontend/src/api/explorerApi.ts` | **LOW** | Add module selection endpoints |

### 8.4 AURA-PROTO Frontend Files (To Create)

| File | Purpose |
|------|---------|
| `frontend/src/components/modules/ModuleBrowser.tsx` | Hierarchical module browsing UI |
| `frontend/src/components/modules/ModuleCard.tsx` | Module display card component |
| `frontend/src/components/modules/ModuleSelector.tsx` | Multi-select module UI component |
| `frontend/src/components/modules/ModuleKGStatus.tsx` | KG processing status display |
| `frontend/src/components/study/StudySession.tsx` | Study session wrapper component |
| `frontend/src/components/study/ModuleChat.tsx` | Chat with module context |
| `frontend/src/components/study/SessionSidebar.tsx` | Module selection sidebar |
| `frontend/src/hooks/useModule.ts` | Module API data hook |
| `frontend/src/hooks/useStudySession.ts` | Session management hook |
| `frontend/src/store/modules.ts` | Zustand store for modules |
| `frontend/src/types/module.ts` | TypeScript type definitions |
| `frontend/src/api/modulesApi.ts` | Module API client |

---

## 9. Best Practices Summary

### 9.1 Code Quality

1. **Follow PEP 8 Style Guide** for Python code
2. **Use TypeScript strict mode** for frontend code
3. **Write descriptive variable and function names**
4. **Keep functions small and focused** (single responsibility)
5. **Add docstrings to all public functions and classes**
6. **Use constants for magic numbers and strings**
7. **Implement proper error handling** (no bare except clauses)
8. **Use logging instead of print statements**

### 9.2 Database Operations

1. **Always use parameterized queries** to prevent injection
2. **Create appropriate indexes** before deploying
3. **Use transactions** for multi-operation workflows
4. **Implement connection pooling** for database connections
5. **Use bulk operations** instead of loops for batch inserts
6. **Profile queries** before deployment using EXPLAIN
7. **Implement proper cleanup** of resources (context managers)

### 9.3 API Design

1. **Use RESTful conventions** consistently
2. **Implement proper HTTP status codes**
3. **Add request validation** using Pydantic models
4. **Implement pagination** for list endpoints
5. **Add rate limiting** for write operations
6. **Use proper versioning** for API endpoints
7. **Document all endpoints** using OpenAPI/Swagger

### 9.4 Security

1. **Authenticate all requests** except public endpoints
2. **Validate all inputs** on the server side
3. **Implement proper authorization** checks
4. **Use HTTPS** for all communications
5. **Store secrets** in environment variables or vaults
6. **Implement audit logging** for all security-sensitive operations
7. **Follow principle of least privilege** for all roles

### 9.5 Performance

1. **Implement caching** for frequently accessed data
2. **Use async/await** for I/O-bound operations
3. **Profile code** to identify bottlenecks
4. **Use appropriate data structures** for the use case
5. **Implement pagination** for large result sets
6. **Use background tasks** for long-running operations
7. **Monitor performance** in production

### 9.6 Testing

1. **Write tests before implementing** (TDD approach)
2. **Achieve minimum 90% code coverage**
3. **Use mocking** for external dependencies
4. **Test edge cases** and error conditions
5. **Implement integration tests** for critical flows
6. **Use continuous integration** for automated testing
7. **Maintain test data factories** for reproducibility

### 9.7 Documentation

1. **Document all APIs** using OpenAPI specification
2. **Add inline comments** for complex logic
3. **Maintain README files** for each component
4. **Document configuration** requirements
5. **Keep changelog** for version tracking
6. **Document architecture decisions** (ADRs)
7. **Update documentation** with code changes

---

## 10. Risk Assessment

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|---------------------|
| Neo4j performance degradation with module filtering | Medium | High | Proper indexing; query optimization; connection pooling |
| Migration data loss or corruption | Low | Critical | Full backup before migration; test on staging; rollback plan |
| Staff adoption resistance | Medium | Medium | Training sessions; gradual rollout; feedback collection |
| Student session overload (too many modules) | Medium | Medium | Limit max modules per session; queue system; performance monitoring |
| KG processing timeouts for large modules | Medium | Medium | Celery tasks with timeouts; batch processing; progress tracking |
| Cross-module query complexity explosion | High | Low | Limit to 2-hop traversals; pre-compute relationships; query timeouts |
| Cache invalidation complexity | Medium | Medium | Event-driven invalidation; TTL-based fallback; monitoring |
| Security vulnerability in module processing | Low | High | Input validation; authentication; authorization; audit logging |

---

## 11. Success Metrics

### 11.1 Technical Metrics

| Metric | Target | Measurement Tool |
|--------|--------|------------------|
| API Response Time (P95) | <200ms | Prometheus |
| Module Processing Time | <30s per module | Celery task metrics |
| RAG Query Response | <2s total | Application metrics |
| Search Precision | >85% | User feedback |
| System Uptime | >99.5% | Uptime monitoring |
| Cache Hit Rate | >80% | Redis monitoring |

### 11.2 Business Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Content Reuse Rate | 80% | Module vs Note ratio |
| Student Engagement | +50% increase | Chat sessions per student |
| Module Adoption | 70% of students | Students using M2KG |
| Staff Efficiency | +40% increase | Notes processed per hour |
| Student Satisfaction | >4.5/5 | User surveys |

---

## 12. Timeline

| Phase | Duration | Start | End |
|-------|----------|-------|-----|
| Phase 1: Foundation | 2 weeks | Week 1 | Week 2 |
| Phase 2: KG Integration | 3 weeks | Week 3 | Week 5 |
| Phase 3: Processing Pipeline | 2 weeks | Week 6 | Week 7 |
| Phase 4: Caching Layer | 1 week | Week 8 | Week 8 |
| Phase 5: Frontend | 2 weeks | Week 9 | Week 10 |
| Phase 6: Testing | 1 week | Week 11 | Week 11 |
| Phase 7: Deployment | 1 week | Week 12 | Week 12 |

**Total Duration: 12 weeks**

---

## 13. Approval

This implementation plan has been reviewed and approved by:

| Role | Name | Signature | Date |
|------|------|-----------|------|
| VP Engineering | _______________ | _______________ | __________ |
| Product Manager | _______________ | _______________ | __________ |
| Lead Architect | _______________ | _______________ | __________ |
| Security Lead | _______________ | _______________ | __________ |

---

*This document is a living specification and will be updated as the project evolves. All stakeholders should review and approve before implementation begins.*

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-18 | Senior Architect | Initial draft |

---

**End of Document**
