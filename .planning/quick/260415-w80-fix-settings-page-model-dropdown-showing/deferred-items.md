# Deferred Items

## Out-of-scope verification blockers observed

1. Backend settings test command from the plan (`python -m pytest ... -k settings`) fails during collection due to existing import-path/environment issues unrelated to this quick task:
   - `ModuleNotFoundError: No module named 'model_router.settings_store'`
   - `ModuleNotFoundError: No module named 'services.llm_entity_extractor'`

These issues prevented executing the full backend settings suite in this environment.
The implemented endpoint behavior is still covered by added/updated tests in
`AURA-NOTES-MANAGER/api/tests/test_settings_router.py`, but full backend suite execution remains deferred until test environment/path wiring is corrected.
