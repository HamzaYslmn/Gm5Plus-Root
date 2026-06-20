@echo off
REM Telefon ekranini PC'de goster + fareyle kontrol et (ekran acik kalir)
title GM5 - Ekran Goster
cd /d "%~dp0"
scrcpy.exe --stay-awake
