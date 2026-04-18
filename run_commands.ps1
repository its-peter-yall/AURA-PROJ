#!/usr/bin/env pwsh
$env:SQZ_CMD = ''
Set-Location "D:\Peter\AURA Twin Proj\AURA-PROJ"

Write-Host "=== SQZ_CMD cleared ===" -ForegroundColor Green
Write-Host "Current SQZ_CMD: '$($env:SQZ_CMD)'" -ForegroundColor Yellow

Write-Host "`n=== Git Status ===" -ForegroundColor Green
git status

Write-Host "`n=== Git Add All ===" -ForegroundColor Green
git add -A

Write-Host "`n=== Git Commit ===" -ForegroundColor Green
git commit -m "feat: add multi-model chat configuration endpoints and update /chat/config"

Write-Host "`n=== Running Tests ===" -ForegroundColor Green
& ".venv\Scripts\python.exe" -m pytest AURA-CHAT\tests\api\test_multi_model_settings.py -x
