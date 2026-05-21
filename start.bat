@echo off
if not exist venv (
    echo Run setup.bat first.
    exit /b 1
)

set AGENT=%~1
if "%AGENT%"=="" (
    echo.
    echo Usage:  start.bat ^<agent^>
    echo.
    echo   start.bat mcq          MCQ solver
    echo   start.bat autotype     Types code into the editor
    echo   start.bat combo        MCQ + AutoType together ^(f+g to switch^)
    echo   start.bat general      General Q^&A
    echo   start.bat clipboard    Copies answer to clipboard
    echo.
    echo Hotkeys ^(default^):
    echo   k+,   Screenshot
    echo   k+.   Send to Gemini
    echo   k+/   Clear queue
    echo   a+s   Pause / resume typing
    echo   k+x   Stop typing
    echo   m+n   Toggle overlay
    echo   f+g   Switch MCQ / AutoType ^(combo mode^)
    echo.
    exit /b 0
)

echo.
echo Starting '%AGENT%' agent. Press Ctrl+C to stop.
echo.
venv\Scripts\python main.py --agent %AGENT%
