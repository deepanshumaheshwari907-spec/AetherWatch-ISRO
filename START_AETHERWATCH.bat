@echo off
setlocal
cd /d "%~dp0"

call .\venv\Scripts\activate.bat

python verify_system.py
if errorlevel 1 (
  echo Verification failed. Review the output above.
  pause
  exit /b 1
)

start "AetherWatch API" /min python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
timeout /t 3 /nobreak >nul
start "AetherWatch Dashboard" /min python -m streamlit run frontend/app.py --server.port 8501

echo API: http://localhost:8000/api/docs
echo Dashboard: http://localhost:8501
echo MOSDAC worker: python -m core.mosdac_worker
endlocal
