@echo off
title FINBLIX - Master Startup Script
echo ======================================================================
echo                     FINBLIX ANALYTICS ENGINE
echo       Platform Analisis Data Pasar Finansial, Simulasi What-If,
echo                 serta Visualisasi Interaktif Pro
echo ======================================================================
echo.

echo [1/3] Memeriksa koneksi database MySQL XAMPP...
netstat -ano | findstr :3306 >nul
if errorlevel 1 (
    echo [PERINGATAN] Port 3306 tidak terdeteksi!
    echo Pastikan module MySQL di XAMPP Control Panel sudah dalam status START.
    echo.
) else (
    echo [OK] MySQL XAMPP terdeteksi aktif pada port 3306.
)

echo [2/3] Menjalankan Server Backend (FastAPI)...
start "Finblix Backend [FastAPI]" cmd /k "cd /d %~dp0\backend && venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [3/3] Menjalankan Server Frontend (React + Vite)...
start "Finblix Frontend [Vite]" cmd /k "cd /d %~dp0\frontend && npm run dev"

timeout /t 3 >nul

echo.
echo ======================================================================
echo FINBLIX BERHASIL DIJALANKAN!
echo.
echo  - Frontend Dashboard : http://localhost:5173
echo  - Backend REST API   : http://localhost:8000
echo  - API Swagger Docs   : http://localhost:8000/docs
echo ======================================================================
echo.
start http://localhost:5173
pause
