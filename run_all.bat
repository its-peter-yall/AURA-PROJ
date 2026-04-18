@echo off
setlocal
set SQZ_CMD=
cd /d "D:\Peter\AURA Twin Proj\AURA-PROJ"

echo === SQZ_CMD Cleared ===
echo Current SQZ_CMD: %SQZ_CMD%

echo.
echo === Git Status ===
git status

echo.
echo === Git Add All ===
git add -A

echo.
echo === Git Commit ===
git commit -m "feat: add multi-model chat configuration endpoints and update /chat/config"

echo.
echo === Running Tests ===
call .venv\Scripts\activate.bat
python -m pytest AURA-CHAT\tests\api\test_multi_model_settings.py -x

endlocal
