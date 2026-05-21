@echo off
if not exist venv (
    echo Run setup.bat first.
    exit /b 1
)

set AGENT=%~1
if "%AGENT%"=="" (
    echo.
    echo Opening Helfi launcher. Press Ctrl+C in this window to stop.
    echo.
    echo   Headless agents:
    echo     start.bat mcq          MCQ solver
    echo     start.bat autotype     Types code into the editor
    echo     start.bat combo        MCQ + AutoType together ^(f+g to switch^)
    echo     start.bat general      General Q^&A
    echo     start.bat clipboard    Copies answer to clipboard
    echo     start.bat multifile    Multi-file LLD code generation
    echo     start.bat full_control Unified assistant ^(screenshots + chat + audio^)
    echo.
    echo   Hotkeys ^(default^):
    echo     k+,   Screenshot         k+.   Send to Gemini
    echo     k+/   Clear queue        a+s   Pause / resume typing
    echo     k+x   Stop typing        m+n   Toggle overlay
    echo     f+g   Switch MCQ / AutoType ^(combo mode^)
    echo.
    venv\Scripts\python main.py
    exit /b %ERRORLEVEL%
)

echo.
echo Starting '%AGENT%' agent. Press Ctrl+C to stop.
echo.
venv\Scripts\python main.py --agent %AGENT%
