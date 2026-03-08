// algorithms.ts
// Simplified algorithms for AURA system - PowerPoint presentation format
// Maximum 10-12 lines per algorithm

/**
 * LECTURE AUTOMATION PIPELINE – Audio Transcription + AI Summarization
 * 
 * Used for converting lecture recordings into structured study notes
 * 
 * Process:
 * 1. Audio file uploaded (MP3/WAV/M4A, max 100MB)
 * 2. Deepgram Nova-3 transcribes with speaker diarization
 * 3. Gemini 2.5 Pro cleans transcript (removes noise, fillers, interruptions)
 * 4. AI generates university notes: Executive Summary + Core Concepts + Glossary + Key Takeaways
 * 5. PDF generated with formatted notes
 * 6. Notes stored in Firestore; optionally processed into knowledge graph
 * 
 * Output: Structured PDF notes with AI summaries linked to course modules
 */

/**
 * DOCUMENT PROCESSING & GRAPHING PIPELINE – Semantic Chunking + Entity Extraction
 * 
 * Used for transforming documents into searchable knowledge graphs
 * 
 * Process:
 * 1. Document uploaded (PDF/DOCX/TXT)
 * 2. Text extracted and split into hierarchical chunks (1500-token parents, 800-token children)
 * 3. Gemini extracts entities: Topics, Concepts, Methodologies, Findings
 * 4. 768-dim embeddings generated for all chunks and entities
 * 5. Neo4j knowledge graph created with nodes and semantic relationships (DEFINES, DEPENDS_ON, USES, etc.)
 * 6. Vector and fulltext indices built for fast retrieval
 * 
 * Output: Populated knowledge graph with chunks, entities, and relationships ready for RAG queries
 */

/**
 * INTELLIGENT ANSWER RETRIEVAL (RAG) – Hybrid Search + Graph Traversal
 * 
 * Used for answering student questions with cited evidence
 * 
 * Process:
 * 1. Student query received; intent classified (chitchat/simple/deep research)
 * 2. Query expanded with related concepts; 768-dim embedding generated
 * 3. Hybrid search: Vector similarity (70%) + Fulltext keywords (30%)
 * 4. 2-hop graph traversal finds related entities and prerequisite concepts
 * 5. Top relevant chunks assembled into context window
 * 6. Gemini generates answer with inline citations [n] linking to source documents
 * 
 * Output: AI-generated answer with citations, source documents, and related concepts
 */

export const algorithms = {
  lectureAutomation: {
    name: 'Lecture Automation Pipeline',
    mechanisms: ['Audio Transcription', 'AI Summarization'],
    input: 'Lecture audio (MP3/WAV/M4A)',
    output: 'Structured PDF notes'
  },
  documentProcessing: {
    name: 'Document Processing & Graphing',
    mechanisms: ['Semantic Chunking', 'Entity Extraction'],
    input: 'Academic documents (PDF/DOCX/TXT)',
    output: 'Knowledge graph (Neo4j)'
  },
  ragRetrieval: {
    name: 'Intelligent Answer Retrieval (RAG)',
    mechanisms: ['Hybrid Search', 'Graph Traversal'],
    input: 'Student question',
    output: 'Cited AI answer with sources'
  }
};

export default algorithms;
