@echo off
echo 🎓 ProfAI Full Stack Launcher
echo ============================

cd /d "%~dp0"

echo 📦 Installing frontend dependencies...
cd frontend
call npm install
if %errorlevel% neq 0 (
    echo ❌ Failed to install frontend dependencies
    pause
    exit /b 1
)

echo 🚀 Starting servers...
cd ..

:: Start backend in new window
start "ProfAI Backend" cmd /k "set PYTHONPATH=src && python -m uvicorn profai.server:app --reload --host 0.0.0.0 --port 8000"

:: Wait a bit for backend to start
timeout /t 3 /nobreak >nul

:: Start frontend in new window  
start "ProfAI Frontend" cmd /k "cd frontend && npm start"

echo ✅ Servers starting in separate windows...
echo 📊 Backend API: http://localhost:8000
echo ⚛️  Frontend UI: http://localhost:3000
echo 📝 API docs: http://localhost:8000/docs
echo.
echo 💡 Close the terminal windows to stop the servers
pause
