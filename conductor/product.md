# AURA Product Guide

> **Project:** Module-to-Knowledge Graph (M2KG)
> **Version:** 2.0
> **Last Updated:** 2026-02-02
> **Type:** Dual-Application Monorepo

## Vision

Transform AURA from a **document-centric** to a **module-centric** learning platform where users can organize documents into thematic modules and study within focused, context-aware sessions with interconnected knowledge graphs.

## Product Overview

AURA is a dual-application learning platform designed to enhance academic study through intelligent document organization and AI-powered chat interactions.

### AURA-NOTES-MANAGER (Staff Portal)

Staff-facing application for content management and knowledge graph processing:

- **Document Management**: Create/edit notes in hierarchical system, upload PDFs and text files
- **Module Organization**: Assign documents to modules, create module hierarchy (department → semester → subject → module)
- **Knowledge Graph Processing**: Chunk documents, extract entities/relationships, generate embeddings using Gemini
- **Module Publishing**: Review knowledge graph before publishing to students
- **Audio-to-Notes Pipeline**: Transcribe audio, refine with AI, summarize, generate PDF notes
- **Bulk Operations**: Multi-select documents, bulk delete, bulk download

### AURA-CHAT (Student Chat)

Student-facing application for module-aware study and chat:

- **Module Selection UI**: Modal with 4-level hierarchy (department → semester → subject → module), multi-select support, cross-module discovery
- **Study Sessions**: Persistent chat sessions with message history and context tracking
- **Module-Aware RAG**: Filter queries by module_id, cross-module concept discovery, citations pointing to module content
- **Thinking Mode**: Enhanced reasoning with thought visualization for complex queries
- **Knowledge Graph Visualization**: Interactive 3D WebGL graph with Reagraph

## User Personas

### Staff (Educators/Administrators)

- Create and organize modules by department/semester/subject
- Upload and process learning materials
- Process documents to knowledge graph (chunk, embed, extract entities)
- Review and publish modules (draft → processing → ready → review → published)
- Monitor study session analytics
- Generate notes from audio recordings
- Perform bulk operations on documents

### Students

- Browse available modules with hierarchical navigation
- Select modules for focused study sessions
- Ask contextual questions with AI assistance
- Discover connections across modules
- Visualize knowledge graph connections
- Use thinking mode for complex queries
- Resume previous study sessions with full context

## Core Workflows

### Content Publishing Workflow

1. Staff creates module structure (department → semester → subject → module)
2. Staff uploads documents to the system
3. Staff assigns documents to modules
4. System processes documents (chunk, embed, extract entities)
5. Staff reviews generated knowledge graph
   - 5.5. Review knowledge graph with interactive graph preview
6. Staff publishes module to students

### Study Session Workflow

1. Student selects module(s) from modal
   - 1.5. Module selection modal with 4-level hierarchy (department → semester → subject → module)
2. System loads relevant knowledge graph context
3. Student initiates chat session
4. Student asks questions with module-aware RAG
5. System provides responses with citations
6. Session persists for future reference

### Audio-to-Notes Workflow (NEW)

1. Staff uploads audio recording (lecture, meeting, etc.)
2. System transcribes audio using Deepgram STT
3. System refines transcription with Gemini AI
4. System summarizes content into structured notes
5. System generates PDF with formatted notes
6. Staff reviews and saves to module

## Detailed Feature List

### Recently Implemented Features

#### AURA-CHAT

- **Thinking Mode**: Enhanced reasoning capabilities with Gemini 2.0 Flash Thinking Experimental, visualizes thought process before generating responses
- **Session Management**: Persistent chat sessions stored in Neo4j with full message history, session resume functionality, message ordering via relationships
- **Graph Visualization**: Interactive 3D WebGL knowledge graph using Reagraph, entity and relationship exploration, concept clustering
- **Dual SDK Architecture**: Vertex AI SDK for thinking mode, Google Generative AI SDK for standard chat
- **Modern Frontend**: React 19 + Vite 7 + TypeScript 5.9 with feature-based architecture

#### AURA-NOTES-MANAGER

- **Audio Pipeline**: Deepgram STT for transcription, Gemini for refinement and summarization, automated PDF generation
- **KG Processing UI**: Batch document processing, real-time status tracking (draft → processing → ready → published), graph preview before publishing
- **Bulk Operations**: Multi-select documents with checkbox interface, bulk delete with confirmation, bulk download as ZIP
- **Module Publishing Workflow**: Draft → Processing → Ready → Review → Published status transitions with review step
- **4-Level Hierarchy**: Department → Semester → Subject → Module navigation

## Success Metrics

| Metric | Target |
|--------|--------|
| Module creation latency | < 100ms |
| Document assignment | < 50ms |
| Knowledge graph processing | < 60s per document |
| RAG query (single module) | < 2s |
| RAG query (multi-module) | < 3s |
| Test coverage | > 90% |
| Frontend TTI (Time to Interactive) | < 1.5s |

## Current State

### Implementation Status

- **Phase 1 (Database Schema)**: COMPLETED ✓
  - Neo4j knowledge graph schema finalized
  - Firestore document hierarchy implemented
  - Module-Session-Message relationships defined

- **Phase 2 (KG Processor)**: COMPLETED ✓
  - Document chunking pipeline operational
  - Entity/relationship extraction with Gemini
  - Embedding generation and vector storage

- **Phase 3 (Module Management)**: COMPLETED ✓
  - 4-level hierarchy (department → semester → subject → module)
  - Module CRUD operations
  - Document assignment workflow

- **Phase 4 (AURA-CHAT Integration)**: COMPLETED ✓
  - Module-aware RAG implementation
  - Module selection UI with hierarchy
  - Cross-module concept discovery

- **Phase 5 (Study Sessions)**: COMPLETED ✓
  - Persistent session storage in Neo4j
  - Message history with relationship ordering
  - Session resume functionality

- **Phase 6 (Frontend Implementation)**: IN PROGRESS
  - AURA-CHAT: Modern React client (completed)
  - AURA-NOTES-MANAGER: KG processing UI (completed)
  - Graph visualization (completed)
  - Audio pipeline UI (completed)

- **Phase 7 (Testing & Optimization)**: PLANNED
  - Performance optimization
  - Load testing with Locust
  - E2E test completion
  - Documentation finalization

## Key Files

| Purpose | Location |
|---------|----------|
| Architecture Brief | `.planning/BRIEF.md` |
| Research Notes | `.planning/RESEARCH.md` |
| Roadmap | `.planning/ROADMAP.md` |
| AURA-CHAT Standards | `AURA-CHAT/client/CLAUDE.md` |
| AURA-NOTES Standards | `AURA-NOTES-MANAGER/frontend/CLAUDE.md` |
| Root Standards | `CLAUDE.md` |

### AURA-NOTES-MANAGER Key Implementation Files

| Component | Path | Description |
|-----------|------|-------------|
| KG Processor | `AURA-NOTES-MANAGER/api/kg_processor.py` | Document processing pipeline (chunk, embed, extract) |
| Module Publishing | `AURA-NOTES-MANAGER/api/modules/publishing.py` | Module publishing workflow with status transitions |
| KG UI Components | `AURA-NOTES-MANAGER/frontend/src/features/kg/` | React components for KG processing and visualization |
| STT Service | `AURA-NOTES-MANAGER/services/stt.py` | Deepgram speech-to-text integration |
| Summarizer | `AURA-NOTES-MANAGER/services/summarizer.py` | AI-powered note generation from transcripts |
| PDF Generator | `AURA-NOTES-MANAGER/services/pdf_generator.py` | PDF creation from structured notes |

### AURA-CHAT Key Implementation Files

| Component | Path | Description |
|-----------|------|-------------|
| RAG Engine | `AURA-CHAT/backend/rag_engine.py` | Module-aware RAG with hybrid search |
| Session Manager | `AURA-CHAT/backend/session_manager.py` | Session persistence in Neo4j |
| Gemini Service | `AURA-CHAT/server/services/gemini_service.py` | Dual SDK (Vertex AI + Google GenAI) |
| Graph Visualization | `AURA-CHAT/client/src/features/graph/` | 3D WebGL graph with Reagraph |
| Study Sessions | `AURA-CHAT/client/src/features/study-sessions/` | Chat sessions with message history |
| Module Selection | `AURA-CHAT/client/src/features/modules/` | 4-level hierarchy modal |
