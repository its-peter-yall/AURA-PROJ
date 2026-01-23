# AURA Product Guide

> **Project:** Module-to-Knowledge Graph (M2KG)
> **Version:** 1.0
> **Type:** Dual-Application Monorepo

## Vision

Transform AURA from a **document-centric** to a **module-centric** learning platform where users can organize documents into thematic modules and study within focused, context-aware sessions with interconnected knowledge graphs.

## Product Overview

AURA is a dual-application learning platform designed to enhance academic study through intelligent document organization and AI-powered chat interactions.

### AURA-NOTES-MANAGER (Staff Portal)

Staff-facing application for content management and knowledge graph processing:

- **Document Management**: Create/edit notes in hierarchical system, upload PDFs and text files
- **Module Organization**: Assign documents to modules, create module hierarchy (department → semester)
- **Knowledge Graph Processing**: Chunk documents, extract entities/relationships, generate embeddings using Gemini
- **Module Publishing**: Review knowledge graph before publishing to students

### AURA-CHAT (Student Chat)

Student-facing application for module-aware study and chat:

- **Module Selection UI**: Dropdown to select published modules, multi-select support, cross-module discovery
- **Study Sessions**: Persistent chat sessions with message history and context tracking
- **Module-Aware RAG**: Filter queries by module_id, cross-module concept discovery, citations pointing to module content

## User Personas

### Staff (Educators/Administrators)

- Create and organize modules by department/semester
- Upload and process learning materials
- Review and publish knowledge graphs
- Monitor study session analytics

### Students

- Browse available modules
- Select modules for focused study sessions
- Ask contextual questions with AI assistance
- Discover connections across modules

## Core Workflows

### Content Publishing Workflow

1. Staff creates module structure (department → semester → topic)
2. Staff uploads documents to the system
3. Staff assigns documents to modules
4. System processes documents (chunk, embed, extract entities)
5. Staff reviews generated knowledge graph
6. Staff publishes module to students

### Study Session Workflow

1. Student selects module(s) from dropdown
2. System loads relevant knowledge graph context
3. Student initiates chat session
4. Student asks questions with module-aware RAG
5. System provides responses with citations
6. Session persists for future reference

## Success Metrics

| Metric | Target |
|--------|--------|
| Module creation latency | < 100ms |
| Document assignment | < 50ms |
| Knowledge graph processing | < 60s per document |
| RAG query (single module) | < 2s |
| RAG query (multi-module) | < 3s |
| Test coverage | > 90% |

## Current State

The project is in active development with:
- Core dual-application architecture established
- Database schema planning complete (Phase 1)
- Knowledge graph processor design complete (Phase 2)
- Module management design in progress (Phase 3)
- Existing CLAUDE.md files with coding standards per application

## Key Files

| Purpose | Location |
|---------|----------|
| Architecture Brief | `.planning/BRIEF.md` |
| Research Notes | `.planning/RESEARCH.md` |
| Roadmap | `.planning/ROADMAP.md` |
| AURA-CHAT Standards | `AURA-CHAT/client/CLAUDE.md` |
| AURA-NOTES Standards | `AURA-NOTES-MANAGER/frontend/CLAUDE.md` |
| Root Standards | `CLAUDE.md` |
