@echo off
REM Telefonun FIZIKSEL ekrani KAPALI, sen PC'den fareyle kontrol et.
REM (Kirik dokunmatik / gizlilik / pil icin ideal. Cihaz uyanik kalir.)
title GM5 - Ekran Kapali Kontrol
cd /d "%~dp0"
scrcpy.exe --turn-screen-off --stay-awake
