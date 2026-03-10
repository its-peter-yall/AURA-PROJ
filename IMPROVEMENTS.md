# Multi-Provider LLM Support - Base Plan

## Summary of Improvements

### 1. **Multi-Provider LLM Architecture**
Transform from single-provider (Vertex AI only) to multi-provider support allowing use of OpenRouter, Ollama, and future providers.

### 2. **Model Router Abstraction Layer**
Create a centralized `ModelRouter` that provides a unified interface (`generate()`, `embed()`) to all backend components. Core backend will be completely provider-agnostic.

### 3. **Cross-Project Unification**
The Model Router serves **both** AURA-CHAT and AURA-NOTES-MANAGER, replacing duplicate Vertex AI client code in both projects.

### 4. **OpenRouter Integration**
Add OpenRouter as second primary provider with support for 200+ models from Anthropic, OpenAI, Meta, Mistral, etc.

### 5. **Hierarchical Provider Selection UI**
- **Simple providers** (Vertex AI, Ollama): Provider → Model (2 levels)
- **OpenRouter**: Provider → Sub-Provider → Model (3 levels)

### 6. **Unified Configuration System**
Shared UI components and API endpoints across both applications for selecting providers/models, with admin controls and user preferences.

### 7. **Complete Backend Abstraction**
All components (rag_engine, summarizer, kg_processor, entity extractors) pass model references from UI to router without knowing which provider is being used.

---

## Goal

Enable **both AURA-CHAT and AURA-NOTES-MANAGER** to work with multiple LLM providers (Vertex AI, OpenRouter, Ollama, etc.) through a shared, provider-agnostic interface. All model interactions across both projects (chat, entity extraction, summarization, knowledge graph processing, embeddings) should route through a unified Model Router without components knowing which provider is being used.

---

## Core Question

**How do we route LLM requests to different providers without ANY component (RAG engine, entity extractors, summarizers, KG processors, etc.) knowing (or caring) which provider is being used?**

---

## Guiding Principles

1. **Single Interface** - Core backend should use one interface regardless of provider
2. **Provider Isolation** - Provider-specific code stays in provider modules only
3. **Backward Compatible** - Existing Vertex AI code continues to work
4. **Flexible Model Selection** - Users can specify provider/model easily
5. **Feature Parity** - Provider-specific features (thinking mode) remain accessible
6. **Complete Abstraction** - Core backend knows NOTHING about providers, only `generate()` and `embed()` methods with model references passed from UI

---

## High-Level Architecture

### Current State
```
AURA-CHAT:                           AURA-NOTES-MANAGER:
• rag_engine.py                      • coc.py
• llm_entity_extractor.py            • summarizer.py
• llm_gatekeeper.py                  • kg_processor.py
• embeddings.py                      • llm_entity_extractor.py
                                     • embeddings.py
            ↓                                  ↓
    Vertex AI Client                   Vertex AI Client
   (tightly coupled)                 (tightly coupled)
            ↓                                  ↓
    Google Vertex AI SDK              Google Vertex AI SDK
```

### Desired State
```
Admin/User UI
    ↓ (selects provider/model, passes as parameter)
AURA-CHAT Components:              AURA-NOTES Components:
• rag_engine                        • coc.py
• llm_entity_extractor             • summarizer.py
• llm_gatekeeper                   • kg_processor.py
• embeddings                        • llm_entity_extractor
• chat_manager                      • embeddings
            ↓                                  ↓
            └──────────┬───────────────────────┘
                       │
            ┌──────────▼──────────┐
            │   MODEL ROUTER      │  ← Shared across both projects
            │  (generate/embed)   │
            └──────────┬──────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
   │ Vertex  │   │OpenRouter│   │ Ollama  │
   └────┬────┘   └────┬────┘   └────┬────┘
        │             │             │
   Google SDK    OpenRouter API  Local API
```

**Key Insight:** The core backend is completely provider-blind. It only knows:
- `generate(model_ref="openrouter/claude-3.5", messages=[...])`
- `embed(model_ref="ollama/nomic-embed", texts=[...])`

The UI (admin panel or user settings) determines which `model_ref` to use. The router just routes it.

---

## Cross-Project Scope

**Critical:** This model router must work across **BOTH** projects:

### AURA-CHAT (Student Chat Application)
| Component | Current Usage | Model Purpose |
|-----------|--------------|---------------|
| `rag_engine.py` | Chat responses | Generation |
| `llm_entity_extractor.py` | Entity extraction from docs | Generation |
| `llm_gatekeeper.py` | Query validation/access control | Generation |
| `entity_aware_chunker.py` | Intelligent text chunking | Generation |
| `chat_manager.py` | Conversation management | Generation |
| `embeddings.py` | Vector search | Embeddings |

### AURA-NOTES-MANAGER (Staff Portal)
| Component | Current Usage | Model Purpose |
|-----------|--------------|---------------|
| `services/coc.py` | Transcript cleaning/auditing | Generation |
| `services/summarizer.py` | Note generation from transcripts | Generation |
| `services/llm_entity_extractor.py` | Entity extraction | Generation |
| `api/kg_processor.py` | Knowledge graph processing | Generation + Embeddings |
| `services/embeddings.py` | Document/entity embeddings | Embeddings |
| `services/entity_deduplicator.py` | Entity resolution | Generation |

### Shared Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        SHARED MODEL ROUTER                      │
│                  (Located in shared/ or copied)                 │
└───────────────────────────────┬─────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼───────┐      ┌────────▼────────┐     ┌───────▼───────┐
│  AURA-CHAT    │      │  AURA-NOTES-    │     │  Providers    │
│               │      │  MANAGER        │     │               │
│ • rag_engine  │      │ • coc.py        │     │ • Vertex      │
│ • llm_entity  │      │ • summarizer    │     │ • OpenRouter  │
│ • gatekeeper  │      │ • kg_processor  │     │ • Ollama      │
│ • embeddings  │      │ • embeddings    │     │               │
└───────────────┘      └─────────────────┘     └───────────────┘
```

**Important Considerations:**
1. **Code Sharing:** Either put model_router in a shared location both projects import, OR duplicate the code (maintenance tradeoff)
2. **Configuration Sync:** Both projects need to respect the same provider/model configuration
3. **Different Use Cases:** 
   - AURA-CHAT needs low-latency chat models
   - AURA-NOTES needs batch processing for documents
   - May need different default models per project
4. **Credential Management:** Both projects need access to same API keys/credentials

---

## Open Questions for Brainstorming

### 1. Interface Design

- What should the unified interface look like?
- Should it be async generator for streaming?
- How do we handle thinking/reasoning across providers (each does it differently)?
- Should we standardize on OpenAI-style messages or keep it flexible?

### 2. Provider Identification

- How do users specify which provider to use?
  - Option A: `provider/model-name` format (e.g., `openrouter/claude-3.5`)
  - Option B: Separate `provider` and `model` parameters
  - Option C: Model registry that maps names to providers
  
- What about backward compatibility? Existing code uses just model names.

### 3. Configuration

- Where do we configure allowed providers/models?
- How do we handle missing credentials gracefully?
- Should there be a fallback chain (try OpenRouter if Vertex fails)?

### 4. Embeddings

- Do we need the same abstraction for embeddings?
- Can we mix and match (Vertex for generation, Ollama for embeddings)?
- How do we ensure embedding dimension compatibility?

### 5. Provider-Specific Features

- How do we expose Vertex AI's thinking mode through the generic interface?
- What about OpenRouter's model routing features?
- Do we lose functionality by abstracting, or can we expose it cleanly?

### 6. Error Handling

- How do we normalize errors from different providers?
- Should retry logic be in the router or per-provider?
- How do we surface provider-specific errors to users?

### 7. Performance & Cost

- Any latency overhead from the abstraction layer?
- How do we track costs per provider?
- Can we do load balancing across providers?

---

## Design Options

### Option 1: Router with String References

```
model_ref = "openrouter/anthropic/claude-3.5-sonnet"
response = await router.generate(model_ref, messages)
```

**Pros:** Simple, easy to pass around
**Cons:** String parsing, less type safety

### Option 2: Explicit Provider + Model

```
response = await router.generate(
    provider="openrouter",
    model="claude-3.5-sonnet",
    messages=messages
)
```

**Pros:** Clear, extensible
**Cons:** More parameters, backward compat issues

### Option 3: Model Registry Pattern

```
model = registry.get_model("claude-3.5")  # Knows it's OpenRouter
response = await model.generate(messages)
```

**Pros:** Rich model objects, can store metadata
**Cons:** More complex, registry management

### Option 4: Factory Pattern

```
provider = ProviderFactory.create("openrouter")
model = provider.get_model("claude-3.5-sonnet")
response = await model.generate(messages)
```

**Pros:** Clean separation, testable
**Cons:** Multiple steps to generate

---

## Provider Considerations

### Vertex AI (Current)

**Characteristics:**
- Google Cloud authentication (ADC)
- Supports Gemini models
- Has thinking mode (token budget)
- Streaming support
- Embeddings API

**Challenges:**
- Location routing (global vs regional)
- Model name normalization (`models/` prefix)
- Dual SDK support (old `vertexai` vs new `google-genai`)

### OpenRouter

**Characteristics:**
- API key authentication (single key for all providers)
- Access to 200+ models from 20+ providers (Anthropic, OpenAI, Meta, Mistral, etc.)
- Single unified API format (OpenAI-compatible)
- Cost tracking headers and fallthrough routing
- Built-in rate limiting and request queuing
- Automatic failover between providers for same model family

**Model Categories Available:**
```
Top-Tier Reasoning:
- anthropic/claude-3.5-sonnet ($3/$15 per 1M tokens)
- anthropic/claude-3-opus ($15/$75 per 1M tokens)
- openai/gpt-4o ($5/$15 per 1M tokens)

Fast & Cost-Effective:
- anthropic/claude-3.5-haiku ($0.25/$1.25 per 1M tokens)
- openai/gpt-4o-mini ($0.15/$0.60 per 1M tokens)
- meta-llama/llama-3.1-70b ($0.50/$0.60 per 1M tokens)

Code-Specialized:
- anthropic/claude-3.5-sonnet (best for code)
- mistralai/codestral-22b (code completion)
- deepseek/deepseek-chat (general purpose)

Local/Free Options:
- meta-llama/llama-3.1-8b (free tier available)
- google/gemma-2-9b-it (free tier available)
```

**OpenRouter API Endpoints:**

```python
# Fetch all available models
GET https://openrouter.ai/api/v1/models
Response: {
  "data": [
    {
      "id": "anthropic/claude-3.5-sonnet",
      "name": "Anthropic: Claude 3.5 Sonnet",
      "description": "Latest Claude model with advanced reasoning",
      "pricing": {"prompt": "0.000003", "completion": "0.000015"},
      "context_length": 200000,
      "architecture": {"modality": "text+image->text"}
    },
    ...
  ]
}

# Fetch provider-specific info
GET https://openrouter.ai/api/v1/models/{model_id}

# Generation endpoint (OpenAI-compatible)
POST https://openrouter.ai/api/v1/chat/completions
Headers: {"Authorization": "Bearer sk-or-v1-..."}
Body: {
  "model": "anthropic/claude-3.5-sonnet",
  "messages": [{"role": "user", "content": "Hello"}],
  "temperature": 0.7,
  "stream": false
}
```

**UI Integration for OpenRouter:**

Challenge: OpenRouter has 200+ models. We need graceful presentation.

**Approach 1: Categorized Dropdown**
```
Provider: OpenRouter ▼

Model Category: [Smart & Reasoning ▼]
├─ Claude 3.5 Sonnet    $3/$15 per 1M  ★ Recommended
├─ Claude 3 Opus        $15/$75 per 1M  (Best quality)
├─ GPT-4o               $5/$15 per 1M
└─ GPT-4 Turbo          $10/$30 per 1M

Model Category: [Fast & Affordable ▼]
├─ Claude 3.5 Haiku     $0.25/$1.25 per 1M  ★ Recommended
├─ GPT-4o Mini          $0.15/$0.60 per 1M
├─ Llama 3.1 70B        $0.50/$0.60 per 1M
└─ Mixtral 8x22B        $0.60/$0.60 per 1M

Model Category: [Code & Technical ▼]
├─ Claude 3.5 Sonnet    $3/$15 per 1M  ★ Best for code
├─ Codestral 22B        $0.50/$0.50 per 1M
└─ DeepSeek Coder       $0.30/$0.30 per 1M

Model Category: [Free Tier ▼]
├─ Llama 3.1 8B         FREE
├─ Gemma 2 9B           FREE
└─ Qwen 2.5 7B          FREE
```

**Approach 2: Smart Search with Filters**
```
Search Models: [___________] 🔍

Filters: [All Providers ▼] [Any Price ▼] [Any Context ▼] [Capabilities ▼]

Results:
☐ Claude 3.5 Sonnet - Anthropic
   Context: 200K | $3/$15 per 1M | Vision, Code, Reasoning
   
☐ GPT-4o - OpenAI  
   Context: 128K | $5/$15 per 1M | Vision, JSON Mode
   
☐ Llama 3.1 70B - Meta
   Context: 128K | $0.50/$0.60 per 1M | Open weights
```

**Backend Model Discovery API:**

```python
# backend/api/models.py
@router.get("/ai/providers/openrouter/models")
async def get_openrouter_models(
    category: Optional[str] = None,  # "reasoning", "fast", "code", "free"
    max_price: Optional[float] = None,
    capabilities: Optional[List[str]] = None,  # ["vision", "code", "json_mode"]
):
    """
    Fetch and cache OpenRouter models with our categorization.
    Cache TTL: 1 hour (models don't change often)
    """
    models = await openrouter_client.fetch_models()
    
    # Apply our categorization logic
    categorized = {
        "reasoning": filter_top_tier_reasoning(models),
        "fast": filter_fast_affordable(models),
        "code": filter_code_specialized(models),
        "free": filter_free_tier(models),
    }
    
    return {
        "categories": categorized,
        "all_models": models,
        "last_updated": datetime.now(),
    }
```

**Model Categorization Strategy:**

We should manually curate recommended models rather than showing all 200+:

```python
# config/openrouter_recommended_models.py
OPENROUTER_RECOMMENDED = {
    "chat": {
        "default": "anthropic/claude-3.5-sonnet",
        "options": [
            {
                "id": "anthropic/claude-3.5-sonnet",
                "name": "Claude 3.5 Sonnet",
                "description": "Best balance of quality and speed",
                "category": "smart",
                "cost_tier": "$$",
                "context_length": 200000,
                "best_for": ["reasoning", "analysis", "general_chat"],
            },
            {
                "id": "anthropic/claude-3.5-haiku",
                "name": "Claude 3.5 Haiku",
                "description": "Fast responses, cost-effective",
                "category": "fast",
                "cost_tier": "$",
                "context_length": 200000,
                "best_for": ["quick_answers", "simple_tasks"],
            },
            {
                "id": "openai/gpt-4o",
                "name": "GPT-4o",
                "description": "OpenAI's latest with vision",
                "category": "smart",
                "cost_tier": "$$",
                "context_length": 128000,
                "best_for": ["vision", "multimodal", "coding"],
            },
            # ... 10-15 carefully selected models
        ]
    },
    "embeddings": {
        "default": "openai/text-embedding-3-small",
        "options": [...]
    }
}
```

**Challenges:**
- Rate limits vary by upstream provider (need per-provider retry logic)
- Different models have different capabilities (some don't support JSON mode)
- Error handling depends on upstream provider
- Model IDs can change when providers update versions
- Pricing updates frequently

**Opportunities:**
- Built-in model routing (fallthrough if one provider is down)
- Cost optimization (cheapest provider for same model)
- Free tier models for testing/low-priority tasks
- Easy A/B testing between model families

### Ollama (Local)

**Characteristics:**
- Local HTTP API
- No authentication (local)
- Supports many open models
- Lower latency, no API costs
- Limited by local hardware

**Challenges:**
- Model availability (must be pulled first)
- Resource constraints
- Different API format than OpenAI
- No built-in thinking mode support

### Potential Future Providers

- **Anthropic Direct** - Native Claude API
- **OpenAI Direct** - Native GPT API
- **Groq** - Fast inference
- **AWS Bedrock** - Enterprise models
- **Azure OpenAI** - Microsoft cloud

---

## Interface Requirements

### Must Support

1. **Text generation** with streaming
2. **System prompts** / instruction tuning
3. **Temperature** and other generation params
4. **Token limits** (input/output)
5. **Error handling** with retry logic
6. **Thinking/reasoning** mode (where supported)

### Nice to Have

1. **Function calling** / tool use
2. **JSON mode** / structured output
3. **Logprobs** / token probabilities
4. **Usage tracking** (tokens, cost)
5. **Batch processing**

### Embeddings Specific

1. **Batch embedding** (multiple texts)
2. **Dimension control**
3. **Model compatibility** (same provider as generation?)

---

## Migration Strategy Thoughts

### Approach A: Gradual Migration

1. Create router alongside existing code
2. Migrate components one at a time
3. Keep old code working during transition
4. Remove old code once everything migrated

**Pros:** Low risk, incremental
**Cons:** Maintenance overhead during transition

### Approach B: Wrapper Pattern

1. Make existing `vertex_ai_client` implement new interface
2. Update all code to use interface
3. Add new providers to same interface

**Pros:** No code duplication
**Cons:** Interface constrained by existing code

### Approach C: Clean Slate

1. Design ideal interface
2. Implement router + providers fresh
3. Gradually move components over
4. Deprecate old client

**Pros:** Clean design, no legacy constraints
**Cons:** More work, potential breaking changes

---

## Configuration Strategy

### Option A: Environment Variables

```bash
DEFAULT_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-...
OLLAMA_URL=http://localhost:11434
```

**Pros:** 12-factor app compliant
**Cons:** Less dynamic, can't change at runtime

### Option B: Config File

```yaml
providers:
  vertex:
    enabled: true
    default_model: gemini-2.5-flash-lite
  openrouter:
    enabled: true
    api_key: ${OPENROUTER_API_KEY}
    default_model: claude-3.5-sonnet
```

**Pros:** Structured, hierarchical
**Cons:** Another config file to manage

### Option C: Database/Runtime Config

Store provider configs in database, configurable via UI

**Pros:** Dynamic, per-user settings possible
**Cons:** More complex, requires UI

---

## Error Handling Strategy

### Questions

1. **Normalization** - Should all providers return same error types?
2. **Transparency** - Should users know which provider failed?
3. **Retry Logic** - Should router retry with different provider on failure?
4. **Fallback Chain** - Define priority order of providers?

### Error Types to Consider

- Authentication failures (bad API key)
- Rate limiting (429 errors)
- Context length exceeded
- Model not found
- Timeout / network errors
- Content policy violations

---

## Testing Strategy

### Unit Tests

- Mock each provider client
- Test router dispatch logic
- Test error handling

### Integration Tests

- Test with real provider APIs (optional)
- Test fallback behavior
- Test configuration loading

### E2E Tests

- Full RAG pipeline with different providers
- Chat streaming with each provider
- Error scenarios

---

## Security Considerations

1. **API Keys** - Secure storage, rotation
2. **Input Validation** - Sanitize before sending to providers
3. **Output Filtering** - Provider responses may need filtering
4. **Data Residency** - Some providers process data in specific regions
5. **Audit Logging** - Track which provider handled each request

---

## Cost Management

1. **Cost Tracking** - Per-provider usage metrics
2. **Budget Controls** - Limits per provider or model
3. **Smart Routing** - Route to cheapest provider that can handle request
4. **Caching** - Cache responses to reduce API calls

---

## Future Extensions

### Model Routing Intelligence

- Route based on query complexity (simple → cheap model, complex → powerful model)
- Route based on context (code → code-specialized model)
- A/B testing different providers

### Multi-Provider Features

- Ensemble responses (query multiple providers, combine answers)
- Provider fallback chains
- Load balancing across providers

### User Preferences

- Let users choose their preferred provider
- Provider-specific settings per user
- Cost vs quality preferences

---

## UI/UX Considerations

### Goal
Create a unified interface for selecting AI providers and models that works across both AURA-CHAT and AURA-NOTES-MANAGER.

### Key Requirements

1. **Unified Configuration** - Same provider/model selection UI in both apps
2. **Task-Specific Selection** - Separate choices for generation vs embeddings
3. **Provider Discovery** - Show available providers based on configured credentials
4. **Model Discovery** - Dynamically fetch available models from each provider
5. **Smart Defaults** - Suggest optimal provider/model combinations
6. **Cost Transparency** - Show estimated costs or provider pricing tiers
7. **Performance Indicators** - Show latency/speed expectations per provider

### UI Placement Options

#### Option A: Global Settings Page
Single configuration page accessible from both apps' settings.

**Pros:**
- Centralized management
- Consistent across apps
- Easy to find

**Cons:**
- Less contextual
- Requires navigating away from current task

#### Option B: Contextual Selectors
Provider/model pickers appear inline where AI is used:
- Chat input area (generation model)
- Document upload (embedding model)
- Study session setup

**Pros:**
- Context-aware selections
- Quick switching per task
- Immediate feedback

**Cons:**
- Cluttered UI if too many selectors
- Inconsistent settings across sessions

#### Option C: Hybrid Approach
- Global defaults in settings
- Override capability in contextual locations
- "Use default" vs "Custom" toggle

**Pros:**
- Best of both worlds
- Power users can customize per-task
- Casual users set once and forget

**Cons:**
- More complex UI logic
- Need to communicate inheritance clearly

### UI Component Design

#### Provider Selector (Step 1)
```
┌─────────────────────────────┐
│ AI Provider              ▼  │
├─────────────────────────────┤
│ ◉ Google Vertex AI          │
│ ○ OpenRouter (Multi)        │
│ ○ Local Ollama              │
└─────────────────────────────┘
```

- Icons for each provider
- Status indicator (connected/error)
- Cost tier badge (Free/$$$/$$$$)
- Latency indicator (Fast/Medium/Slow)

#### Sub-Provider Selector (OpenRouter Only - Step 2)
```
┌─────────────────────────────┐
│ OpenRouter Provider      ▼  │
├─────────────────────────────┤
│ ◉ Anthropic                 │
│ ○ OpenAI                    │
│ ○ Meta                      │
│ ○ Mistral                   │
│ ○ Google                    │
│ ○ Microsoft                 │
│ ○ Amazon                    │
└─────────────────────────────┘
```

- Shows only when OpenRouter is selected
- Groups models by upstream provider
- Helps users find models from their preferred AI company

#### Model Selector (Step 2 or 3)

**For Vertex AI / Ollama (2-level hierarchy):**
```
┌─────────────────────────────┐
│ Model                    ▼  │
├─────────────────────────────┤
│ Gemini 2.5 Flash Lite  ★    │  ← Recommended
│ Gemini 2.5 Flash            │
│ Gemini 3 Flash Preview      │
└─────────────────────────────┘
```

**For OpenRouter (3-level hierarchy):**
```
OpenRouter → Anthropic → Model Selector
┌─────────────────────────────┐
│ Model                    ▼  │
├─────────────────────────────┤
│ Claude 3.5 Sonnet       ★   │  ← Recommended
│ Claude 3.5 Haiku            │
│ Claude 3 Opus               │
│ Claude 3 Sonnet             │
│ Claude 3 Haiku              │
└─────────────────────────────┘
```

**Alternative: Flat Model List with Provider Prefix**
```
┌─────────────────────────────┐
│ Model                    ▼  │
├─────────────────────────────┤
│ anthropic/claude-3.5-sonnet │  ★ Recommended
│ anthropic/claude-3.5-haiku  │
│ openai/gpt-4o               │
│ openai/gpt-4o-mini          │
│ meta-llama/llama-3.1-70b    │
│ mistralai/mistral-large     │
└─────────────────────────────┘
```

**Model Display Features:**
- Model capabilities icons (thinking 💭, vision 👁️, code </>, json {})
- Performance metrics (tokens/sec)
- Cost per 1M tokens (input/output)
- "Recommended" badge based on use case
- Context length indicator (128K, 200K, etc.)

**OpenRouter Model Fetching Strategy:**

```python
# When user selects OpenRouter as provider
async def on_openrouter_selected():
    # Fetch all models from OpenRouter
    models = await fetch_openrouter_models()
    
    # Group by upstream provider
    grouped = {
        "anthropic": [
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3.5-haiku",
            "anthropic/claude-3-opus",
        ],
        "openai": [
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "openai/gpt-4-turbo",
        ],
        "meta": [
            "meta-llama/llama-3.1-405b",
            "meta-llama/llama-3.1-70b",
            "meta-llama/llama-3.1-8b",
        ],
        "mistral": [...],
        "google": [...],
        # ... etc
    }
    
    # Show sub-provider selector first
    show_sub_provider_selector(grouped.keys())
    
    # Then show models for selected sub-provider
    show_model_selector(grouped[selected_sub_provider])
```

### Configuration Levels

#### Level 1: Global Defaults (Admin/Organization)
- Set organization-wide default provider
- Restrict allowed providers (compliance)
- Budget limits per provider

#### Level 2: User Preferences
- Each user chooses their defaults
- Override global defaults
- Save frequently-used combinations as presets

#### Level 3: Session/Task Override
- Change provider for specific chat/document
- Temporary override without changing defaults
- "Use for this session only" checkbox

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                          UI Layer                           │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │   Provider     │  │  Sub-Provider  │  │     Model      │ │
│  │   Selector     │  │   (Optional)   │  │   Selector     │ │
│  │                │  │                │  │                │ │
│  │ • Vertex AI    │  │ [If OpenRouter]:│  │ • Gemini 2.5   │ │
│  │ • OpenRouter ──┼──┼─→ Anthropic    │  │ • Claude 3.5   │ │
│  │ • Ollama       │  │ • OpenAI       │  │ • GPT-4o       │ │
│  │                │  │ • Meta         │  │ • Llama 3.1    │ │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘ │
└──────────┼───────────────────┼───────────────────┼──────────┘
           │                   │                   │
           └───────────────────┴───────────────────┘
                               │
              ┌────────────────┴────────────────┐
              │      Configuration API          │
              │  - Validate credentials         │
              │  - Fetch provider/sub/models    │
              │  - Store preferences            │
              └────────────────┬────────────────┘
                               │
              ┌────────────────▼────────────────┐
              │     Backend Router Layer        │
              │  - Route to provider            │
              │  - Handle auth                  │
              │  - Standardize responses        │
              └─────────────────────────────────┘
```

**Selection Flow Examples:**

**Simple (Vertex AI):**
```
1. Provider: Vertex AI
2. Model: Gemini 2.5 Flash
3. Use: vertex/gemini-2.5-flash
```

**Nested (OpenRouter):**
```
1. Provider: OpenRouter
2. Sub-Provider: Anthropic
3. Model: Claude 3.5 Sonnet
4. Use: openrouter/anthropic/claude-3.5-sonnet
```

### Cross-Application Consistency

#### Shared Components
Create a shared component library (or duplicate with same design):
- `ProviderSelector` - Dropdown with provider info
- `ModelSelector` - Model picker with metadata
- `AISettingsPanel` - Complete configuration UI
- `CostEstimator` - Real-time cost preview

#### Shared API
Single backend endpoint both apps use:
```
GET  /api/ai/providers                         # List available providers
GET  /api/ai/providers/{id}/models             # List models for provider
GET  /api/ai/providers/openrouter/subproviders # List OpenRouter sub-providers
GET  /api/ai/providers/openrouter/models?provider=anthropic  # List models for sub-provider
POST /api/ai/config                            # Save user preferences
GET  /api/ai/config                            # Get current configuration
```

**API Response Examples:**

```json
// GET /api/ai/providers
{
  "providers": [
    {
      "id": "vertex",
      "name": "Google Vertex AI",
      "type": "direct",
      "requires_subprovider": false,
      "status": "connected"
    },
    {
      "id": "openrouter",
      "name": "OpenRouter",
      "type": "aggregator",
      "requires_subprovider": true,
      "status": "connected"
    },
    {
      "id": "ollama",
      "name": "Local Ollama",
      "type": "local",
      "requires_subprovider": false,
      "status": "connected"
    }
  ]
}

// GET /api/ai/providers/openrouter/subproviders
{
  "subproviders": [
    {
      "id": "anthropic",
      "name": "Anthropic",
      "description": "Claude family of models",
      "model_count": 5
    },
    {
      "id": "openai",
      "name": "OpenAI",
      "description": "GPT family of models",
      "model_count": 8
    },
    {
      "id": "meta",
      "name": "Meta",
      "description": "Llama open-weight models",
      "model_count": 12
    }
  ]
}

// GET /api/ai/providers/openrouter/models?provider=anthropic
{
  "provider": "openrouter",
  "subprovider": "anthropic",
  "models": [
    {
      "id": "anthropic/claude-3.5-sonnet",
      "name": "Claude 3.5 Sonnet",
      "context_length": 200000,
      "pricing": {"input": 0.000003, "output": 0.000015},
      "capabilities": ["vision", "code", "reasoning"],
      "recommended": true
    },
    {
      "id": "anthropic/claude-3.5-haiku",
      "name": "Claude 3.5 Haiku",
      "context_length": 200000,
      "pricing": {"input": 0.00000025, "output": 0.00000125},
      "capabilities": ["fast", "cheap"],
      "recommended": false
    }
  ]
}
```

#### State Management
- **AURA-CHAT**: Store in Zustand/React context
- **AURA-NOTES-MANAGER**: Store in Zustand/React context
- **Backend**: Store in Firestore per user
- **Sync**: Real-time sync across tabs/sessions

### User Experience Flows

#### First-Time Setup
1. User opens settings
2. Sees "AI Configuration" section
3. System detects available providers (checks env vars/credentials)
4. Suggests optimal default based on use case
5. User can accept or customize

#### Changing Provider (Simple - Vertex AI/Ollama)
1. User opens chat/document
2. Clicks model indicator in toolbar
3. Quick switcher dropdown appears
4. Shows recently used + all available models
5. On selection, shows "Model changed" toast
6. Optionally: "Apply to future sessions?"

#### Changing Provider (Nested - OpenRouter)
1. User opens chat/document
2. Clicks model indicator in toolbar
3. Provider selector appears (Vertex/OpenRouter/Ollama)
4. User selects OpenRouter
5. Sub-provider selector appears (Anthropic/OpenAI/Meta/...)
6. User selects Anthropic
7. Model selector appears (Claude 3.5 Sonnet/Haiku/Opus/...)
8. User selects model, confirms change
9. Shows "Model changed" toast with full path: "Using Claude 3.5 Sonnet via OpenRouter"

#### Embedding Document
1. User uploads document
2. Before processing, shows:
   - Current embedding model
   - Estimated tokens/cost
   - Option to change provider
3. User confirms or switches
4. Processing begins with selected provider

### Error Handling in UI

#### Provider Unavailable
```
┌──────────────────────────────┐
│ ⚠️  OpenRouter Unavailable   │
│                              │
│ API key invalid or expired.  │
│ [Check Settings] [Use Vertex]│
└──────────────────────────────┘
```

#### Model Not Available
- Show "Model unavailable in your region" warning
- Suggest alternative models
- Link to provider documentation

#### Cost Budget Exceeded
```
┌──────────────────────────────┐
│ 💰 Monthly Budget Reached    │
│                              │
│ You've used $50 of $50       │
│ budget for OpenRouter.       │
│ [View Usage] [Switch to      │
│  Vertex AI]                  │
└──────────────────────────────┘
```

### Advanced Features

#### Smart Recommendations
```
┌─────────────────────────────────────┐
│ 🤖 Suggested for Code Questions     │
│                                     │
│ Based on your query, we recommend   │
│ Claude 3.5 Sonnet for better        │
│ code understanding.                 │
│ [Use Claude] [Keep Current]         │
└─────────────────────────────────────┘
```

#### Usage Dashboard
```
┌─────────────────────────────────────┐
│ AI Usage This Month                 │
│                                     │
│ Vertex AI     ████████░░ $32.50     │
│ OpenRouter    ███░░░░░░░ $18.20     │
│ Ollama        ░░░░░░░░░░ $0.00      │
│                                     │
│ Total: $50.70 / $100 budget         │
└─────────────────────────────────────┘
```

#### Preset Configurations
Save named configurations:
- "Fast & Cheap" → Ollama local
- "High Quality" → Claude via OpenRouter
- "Balanced" → Gemini Flash

### Accessibility Considerations

- Clear labels for all providers/models
- Keyboard navigation for selectors
- Screen reader announcements for changes
- High contrast mode support
- Mobile-responsive design

### Mobile Experience

- Bottom sheet for provider/model selection
- Swipe between provider tabs
- Compact view for current selection
- Quick actions in chat toolbar

---

## Discussion Points

Add thoughts, concerns, ideas below:

### [Topic 1]: Interface Simplicity vs Power

How simple should the interface be? Do we lose valuable features by abstracting too much?

### [Topic 2]: Embedding Strategy

Should embeddings use the same router or separate? Can we mix providers (Vertex generation + Ollama embeddings)?

### [Topic 3]: Thinking Mode Standardization

Vertex has thinking tokens, Claude has reasoning blocks. How do we expose this cleanly?

### [Topic 4]: Configuration Complexity

How much configuration is too much? Should it "just work" with sensible defaults?

### [Topic 5]: Backward Compatibility

How do we migrate without breaking existing deployments? Grace period?

### [Topic 6]: Provider Maintenance

Who maintains provider implementations? Core team or community?

### [Topic 7]: Performance Overhead

What's acceptable overhead for the abstraction layer? 10ms? 100ms?

---

## Next Steps

1. Discuss and debate the open questions above
2. Choose between design options
3. Define the interface contract
4. Create proof-of-concept with 2 providers
5. Evaluate based on criteria (complexity, performance, maintainability)
6. Decide on implementation approach

---

*This is a living document. Add your thoughts, concerns, and ideas as we brainstorm.*
