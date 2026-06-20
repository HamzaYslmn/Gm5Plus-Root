@echo off
REM Ekran goruntusu al ve ac (ekran kapali olsa bile, cihaz uyanikken dolu gelir)
title GM5 - Ekran Goruntusu
cd /d "%~dp0"
set OUT=%USERPROFILE%\Desktop\gm5_ekran.png
adb.exe exec-out screencap -p > "%OUT%"
echo Kaydedildi: %OUT%
start "" "%OUT%"
