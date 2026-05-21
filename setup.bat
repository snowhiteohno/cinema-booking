@echo off
echo === Helfi Setup ===

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: python not found. Install Python 3.10+ from python.org
    exit /b 1
)

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Installing Python dependencies...
venv\Scripts\pip install --upgrade pip -q
venv\Scripts\pip install -r requirements.txt -q

if not exist .env (
    copy .env.example .env
    echo.
    echo ^>^>^> Created .env - open it and paste your Gemini API key.
    echo ^>^>^> Then run: start.bat mcq
) else (
    echo .env already exists.
    echo ^>^>^> Run: start.bat mcq
)

echo.
echo === Setup complete ===
