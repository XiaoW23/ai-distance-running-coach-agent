@echo off
echo ========================================================
echo   Running Agent Startup Script
echo ========================================================
echo.

REM 激活虚拟环境
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] 虚拟环境不存在，请先创建: python -m venv .venv
    pause
    exit /b 1
)

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