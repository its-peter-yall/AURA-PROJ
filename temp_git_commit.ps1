$env:SQZ_CMD = ''
Write-Host "=== SQZ_CMD cleared ==="
git status
git add -A
git commit -m "feat: add multi-model chat configuration endpoints and update /chat/config"
.venv\Scripts\Activate.ps1
python -m pytest AURA-CHAT/tests/api/test_multi_model_settings.py -x
