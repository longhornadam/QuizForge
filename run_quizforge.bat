@echo off
echo.
echo ========================================
echo QuizForge - Quiz Processing Pipeline
echo ========================================
echo.

REM Run the orchestrator
py -m engine.orchestrator

echo.
echo Processing complete. Press any key to exit...
pause > nul