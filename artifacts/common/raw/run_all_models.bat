@echo off
echo ===================================
echo Starting All Model Processing
echo ===================================
echo.
echo This will run 3 models in parallel:
echo 1. google/gemini-3-pro-preview
echo 2. qwen/qwen3-32b
echo 3. anthropic/claude-sonnet-4
echo.
echo Output files will be saved in 'compare' folder
echo Logs will be saved as model_name_log.txt
echo.
echo Press Ctrl+C in any window to stop that specific model
echo.
pause

REM Start all three models in separate windows
start "Gemini 3 Pro" cmd /k "python run_model_gemini_3_pro.py"
timeout /t 2 /nobreak >nul

start "Qwen 32B" cmd /k "python run_model_qwen_32b.py"
timeout /t 2 /nobreak >nul

start "Claude Sonnet 4" cmd /k "python run_model_claude_sonnet.py"

echo.
echo All models started in separate windows!
echo Check the 'compare' folder for outputs and logs
echo.
