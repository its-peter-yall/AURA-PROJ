# Phase 01 Validation Strategy: Multi-model Chat Configuration

**Phase:** 01 - multi-model-chat-configuration  
**Research:** [01-RESEARCH.md](./01-RESEARCH.md)  
**Created:** 2026-04-18

## Phase Goal
Enable configuration of 1-5 chat models with default selection, and update chat page to use the configured defaults.

## Dimension 1: Structural Coverage

### Module Inventory
| Module | Test File Exists | Test Type | Priority |
|--------|------------------|-----------|----------|
| SettingsStore multi-model | ❌ Wave 0 | Unit | P0 |
| API validation (1-5 limit) | ❌ Wave 0 | Unit | P0 |
| /chat/config endpoint | ❌ Wave 0 | Integration | P1 |
| ChatModelsSection UI | ❌ Wave 0 | Component | P1 |
| InlineModelPicker integration | ✅ existing | E2E | P2 |

### Critical Paths (Nyquist Sampling)
| User Flow | Happy Path Test | Edge Cases |
|-----------|-----------------|------------|
| Admin configures 1 model | Save → Verify stored | Empty array rejection |
| Admin configures 5 models | Save → All 5 stored | 6th model rejection |
| Set default model | Default_index updated | Out of bounds rejection |
| Chat loads config | allowed_models returned | Empty config fallback |
| User picks non-default | Session uses selected | Invalid model rejection |

## Dimension 2: Behavioral Contracts

### Expected vs Actual Behaviors

| Contract | Expected | Test Method |
|----------|----------|-------------|
| Model count limit | 1-5 models accepted, 0 or 6+ rejected | Unit: `test_model_count_validation` |
| Default index bounds | default_index < len(models) enforced | Unit: `test_default_index_validation` |
| Backward compatibility | Legacy {provider, model} still works | Integration: `test_legacy_format_read` |
| API response format | `allowed_models` array in /chat/config | Integration: `test_chat_config_response` |
| UI model display | Only allowed models shown in picker | E2E: `test_model_picker_limited` |

### Wave 0 Gaps
- [ ] `shared/model_router/tests/test_multi_model_config.py` — unit tests for new methods
- [ ] `AURA-CHAT/server/tests/test_settings_router.py` — test PUT /defaults/chat/models
- [ ] `AURA-CHAT/client/src/features/settings/components/ChatModelsSection.test.tsx` — UI tests

## Dimension 3: Input Partitioning

### Input Categories

| Category | Valid Inputs | Invalid Inputs | Boundary Tests |
|----------|--------------|----------------|----------------|
| Model count | 1, 2, 3, 4, 5 models | 0, 6, null | Exactly 5, exactly 1 |
| Provider string | "vertex_ai", "openrouter", "ollama" | "", "invalid", null | Case sensitivity |
| Model identifier | Valid model strings | "", null, 123 | Special chars |
| Default index | 0 to len(models)-1 | -1, len(models), null | Exactly at bounds |
| Array order | Any valid order | Malformed JSON | Empty models array |

### Equivalence Classes
- **EC1**: Valid multi-model config (1-5 models, valid default_index)
- **EC2**: Legacy single-model config (backward compatibility)
- **EC3**: Empty/missing config (error or fallback)
- **EC4**: Too many models (>5, error)
- **EC5**: Invalid default index (out of bounds, error)

## Dimension 4: State Space Coverage

### State Variables
- `models`: Array of {provider, model} objects (length 0-5)
- `default_index`: Integer pointing to default model
- `legacy_format`: Boolean for backward compatibility mode

### Transitions
| From State | Event | To State | Test |
|------------|-------|----------|------|
| Empty config | Add 1st model | 1 model, default=0 | `test_add_first_model` |
| 1 model | Add 2nd model | 2 models, default unchanged | `test_add_second_model` |
| N models (N<5) | Add (N+1)th model | N+1 models | `test_add_up_to_five` |
| 5 models | Add 6th model | Error: limit exceeded | `test_sixth_model_rejected` |
| Multi-model | Set default_index=K | New default selected | `test_change_default` |
| Legacy config | Read operation | Converted to array format | `test_legacy_migration` |

## Dimension 5: Risk-Based Prioritization

| Risk Area | Likelihood | Impact | Test Depth |
|-----------|------------|--------|------------|
| API validation bypass | Medium | High | Fuzz testing, boundary tests |
| UI/Backend sync issues | Medium | Medium | E2E tests, state transition tests |
| Backward compatibility break | Low | High | Migration tests, dual-format tests |
| Default index out of bounds | Low | Medium | Bounds checking, error handling |
| Model ordering not preserved | Low | Low | Order verification in integration tests |

### High-Risk Tests
1. `test_api_validation_enforced` — Verify 1-5 limit at API level, not just UI
2. `test_backward_compatibility` — Legacy configs still work
3. `test_default_bounds_enforced` — Out-of-bounds default_index rejected
4. `test_chat_uses_allowed_models` — Chat page respects admin configuration

## Dimension 6: Regression Prevention

### Existing Functionality to Protect
| Feature | Protection Test | When to Run |
|---------|-----------------|-------------|
| Single model selection | `test_single_model_still_works` | Every wave |
| Settings persistence | `test_settings_persist` | Every wave |
| Model routing | `test_model_routing_unaffected` | Per-wave merge |
| Chat streaming | `test_chat_streaming_works` | Phase gate |

### Pre-Commit Regression Suite
```bash
# Backend (run before any commit to shared/model_router)
python -m pytest shared/model_router/tests/test_settings_store.py -x

# Frontend (run before any commit to AURA-CHAT/client)
npm test -- --run ChatModelsSection
```

## Dimension 7: Coverage Criteria

### Coverage Targets
| Metric | Target | Measurement |
|--------|--------|-------------|
| Line coverage | >85% | `pytest --cov` |
| Branch coverage | >80% | `pytest --cov-branch` |
| E2E critical paths | 100% | Manual test list |
| API contract tests | All endpoints | Postman/HTTP tests |

### Coverage Gaps to Close
- Multi-model config edge cases (empty array, malformed)
- Concurrent update scenarios (race conditions)
- Migration path from legacy to new format

## Dimension 8: Environment Parity

### Test Environments
| Environment | Purpose | Data Strategy |
|-------------|---------|---------------|
| Local dev | Fast feedback | In-memory Redis, mocked AI |
| CI | Gate check | Docker compose with Redis |
| Staging | Pre-prod validation | Production-like data |

### Environment Variables
| Variable | Local | CI | Staging |
|----------|-------|-----|---------|
| `REDIS_URL` | `redis://localhost:6379` | `redis://test-redis:6379` | AWS ElastiCache |
| `TEST_MODE` | `true` | `true` | `false` |

### Sampling Rate
- **Per task commit:** `pytest test_settings_store.py -x` (backend), `npm test -- ChatModelsSection` (frontend)
- **Per wave merge:** Full backend + frontend test suites
- **Phase gate:** All tests green before `/gsd-verify-work`

---

*Generated from RESEARCH.md validation architecture section*
*Part of Nyquist validation framework - Dimension 8 coverage*
