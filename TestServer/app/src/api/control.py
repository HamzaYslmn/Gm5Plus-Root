"""Actuators: torch, vibration, RGB LED, screen brightness.
Fire-and-forget: each endpoint launches the slow termux/su process with Popen and returns in
~milliseconds (no await). The UI updates optimistically, so buttons feel instant.
Note: termux-brightness needs the WRITE_SETTINGS app-op:
  su -c "appops set com.termux.api WRITE_SETTINGS allow"   (or via adb shell)  -- granted on this device."""
import subprocess
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
LED = "/sys/class/leds"
DN = subprocess.DEVNULL

def _fire(*cmd):
    try: subprocess.Popen(cmd, stdout=DN, stderr=DN)  # detached; we don't wait on it
    except Exception: pass

@router.post("/control/torch")
def torch(on: bool = True):
    _fire("termux-torch", "on" if on else "off")
    return {"ok": True, "torch": on}

class Vib(BaseModel):
    ms: int = 300
@router.post("/control/vibrate")
def vibrate(v: Vib):
    _fire("termux-vibrate", "-f", "-d", str(max(1, min(5000, v.ms))))
    return {"ok": True}

class Led(BaseModel):
    r: int = 0
    g: int = 0
    b: int = 0
@router.post("/control/led")
def led(c: Led):
    rgb = [max(0, min(255, c.r)), max(0, min(255, c.g)), max(0, min(255, c.b))]
    cmd = "; ".join(f"echo {v} > {LED}/{n}/brightness" for n, v in zip(("red", "green", "blue"), rgb))
    _fire("su", "-c", cmd)  # RGB LED is root-only sysfs
    return {"ok": True, "led": rgb}

class Bright(BaseModel):
    level: int = 128  # 0-255
@router.post("/control/brightness")
def brightness(b: Bright):
    lvl = max(0, min(255, b.level)); _fire("termux-brightness", str(lvl))
    return {"ok": True, "level": lvl}
