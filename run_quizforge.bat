@echo off
echo.
echo ========================================
echo QuizForge - Quiz Processing Pipeline
echo ========================================
echo.

REM Run the orchestrator
python -m engine.orchestrator

echo.
echo Processing complete. Press any key to exit...
pause > nul