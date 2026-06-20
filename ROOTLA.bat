@echo off
REM ============================================================
REM  GM 5 Plus (shamrock) - OTOMATIK ROOT baslatici
REM  Cift tikla. Gercek is auto_root.ps1 icinde.
REM ============================================================
title GM 5 Plus Otomatik Root
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0auto_root.ps1"
pause
