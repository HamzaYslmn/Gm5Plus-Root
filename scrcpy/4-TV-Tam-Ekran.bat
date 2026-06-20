@echo off
REM PC'yi TV'ye HDMI ile bagla, bu tam ekran scrcpy'yi calistir.
REM Telefon ekrani kapali kalir, TV telefonun aynasi olur. Cikis: ekrana tikla + F11 veya pencereyi kapat.
title GM5 - TV Tam Ekran
cd /d "%~dp0"
scrcpy.exe --fullscreen --stay-awake --turn-screen-off --video-bit-rate 8M
