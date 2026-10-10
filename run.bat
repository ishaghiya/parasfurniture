@echo off
title Paras Furniture Management System
echo ============================================================
echo Starting Paras Furniture Offline Management Software...
echo ============================================================
echo.

:: Open default browser after 2 seconds in background
start "" http://127.0.0.1:5000

:: Run local Flask application server
python app.py

pause
