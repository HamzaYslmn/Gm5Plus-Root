#!/data/data/com.termux/files/usr/bin/bash
# restart the dashboard server + clean up orphaned termux-api helpers from the previous run
pkill -f "uvicorn" 2>/dev/null
pkill -f "src/main.py" 2>/dev/null
pkill -f "termux-sensor" 2>/dev/null
pkill -f "termux-api Sensor" 2>/dev/null
termux-sensor -c >/dev/null 2>&1
sleep 2
cd ~/app/src
setsid uv run uvicorn main:app --host 0.0.0.0 --port 8001 >~/srv.log 2>&1 </dev/null &
echo "started"
