@echo off
set SQZ_CMD=
cd /d "D:\Peter\AURA Twin Proj\AURA-PROJ"
echo === Git Status ===
git status
echo === Git Add All ===
git add -A
echo === Git Commit ===
git commit -m "feat: add multi-model chat configuration endpoints and update /chat/config"
echo === Activate venv and run tests ===
call .venv\Scripts\activate.bat
python -m pytest AURA-CHAT\tests\api\test_multi_model_settings.py -x
pause
