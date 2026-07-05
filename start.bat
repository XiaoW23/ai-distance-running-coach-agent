@echo off
echo ========================================================
echo   Running Agent Startup Script
echo ========================================================
echo.
echo [INFO] Please ensure DEEPSEEK_API_KEY is configured in .env
echo [INFO] Once started, open your browser at: http://localhost:8000
echo.
echo [INFO] Verifying dependencies (silent)...
pip install -r requirements.txt --quiet --disable-pip-version-check
echo.
echo Starting uvicorn server...
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
pause