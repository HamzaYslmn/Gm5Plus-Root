"""Live-video proxy for the forked android-ip-camera app (https on :4444).

The app runs ON-DEMAND: started on the first viewer, force-stopped ~IDLE_STOP s after the last one
leaves (zero idle power). Four GET endpoints:

  /api/video/cameras           -> [{"id","facing","sizes":[{"w","h"},...]}, ...]  (per-camera properties)
  /api/video/controls?backend= -> [{"key","label","type","value",values|min/max/step}, ...]  (per-API supported controls)
  /api/video/stream            -> hardware H.264 stream (browser plays it via jMuxer)
  /api/video/status            -> {"up": bool, "viewers": int, "flash_max": int}
  /api/video/control?<k>=<v>   -> forward a control to the app. keys:
        torch=on|off  focus=1  camera=<id>  backend=camera1-gl|camera2-gl|camerax-gl|camerax-analysis
        size=WxH (from a camera's sizes list)  resolution=480|720|1080  zoom=1..8
        exposure=<ev index>  fps=1..60 (cap; lower = brighter)  iso=0(auto)|>0  (manual exposure, native backends)
        flash=0..flash_max  (LED torch brightness; routed via app HAL while streaming, sysfs when idle)
"""
import asyncio, subprocess, time
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, Response

# --- config ---
PKG = "com.github.digitallyrefined.androidipcamera"
BASE = "https://127.0.0.1:4444"
IDLE_STOP = 8.0                       # seconds after last viewer before force-stopping the app
LED = "/sys/class/leds"              # torch LED sysfs root
LED_MAX = f"{LED}/led:torch_0/max_brightness"
LED_T0 = f"{LED}/led:torch_0/brightness"
LED_T1 = f"{LED}/led:torch_1/brightness"
LED_SW = f"{LED}/led:switch/brightness"
SIZE_CAP = 4096                       # generous size passthrough cap for the termux fallback

router = APIRouter()
_V = {"viewers": 0, "last": 0.0, "lock": asyncio.Lock(), "reaper": None}
_flash_max = None                     # cached torch max brightness (queried once via su)

def _su(cmd):  # fire-and-forget root shell command
    try: subprocess.Popen(["su", "-c", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception: pass

def flash_max():
    """Torch max brightness, read once from sysfs via su and cached (fallback 255 if unreadable)."""
    global _flash_max
    if _flash_max is None:
        _flash_max = 255
        try:
            out = subprocess.run(["su", "-c", f"cat {LED_MAX}"], capture_output=True, text=True, timeout=4).stdout
            n = int(out.strip())
            if n > 0: _flash_max = n
        except Exception: pass
    return _flash_max

async def _is_up():
    try:
        _, w = await asyncio.wait_for(asyncio.open_connection("127.0.0.1", 4444), timeout=1.5)
        w.close(); return True
    except Exception:
        return False

async def _ensure_app():
    if await _is_up(): return True
    _su(f"am start -n {PKG}/.activities.MainActivity")
    for _ in range(60):
        await asyncio.sleep(0.25)
        if await _is_up(): return True
    return False

async def _reaper():
    while True:
        await asyncio.sleep(2)
        if _V["viewers"] <= 0 and time.monotonic() - _V["last"] > IDLE_STOP:
            _su(f"am force-stop {PKG}")
            _V["reaper"] = None
            return

def _touch():
    _V["last"] = time.monotonic()
    if _V["reaper"] is None or _V["reaper"].done():
        _V["reaper"] = asyncio.create_task(_reaper())

async def _app_get(path):
    """One-off GET to the app over its self-signed TLS. Returns (status_code, json_or_None)."""
    try:
        async with httpx.AsyncClient(verify=False, timeout=6) as c:
            r = await c.get(f"{BASE}{path}")
            try: return r.status_code, r.json()
            except Exception: return r.status_code, None
    except Exception:
        return 0, None

@router.get("/video/cameras")
async def cameras():
    # per-camera properties incl. each camera's own supported sizes; fall back to termux-camera-info.
    # The app already caps sizes to the encoder max, so just pass them through.
    code, data = await _app_get("/cameras")
    if code == 200 and data:
        return data
    import json
    try:
        out = subprocess.run(["termux-camera-info"], capture_output=True, text=True, timeout=8).stdout
        result = []
        for c in json.loads(out):
            sizes = [{"w": s["width"], "h": s["height"]} for s in c.get("jpeg_output_sizes", [])
                     if s["width"] <= SIZE_CAP and s["height"] <= SIZE_CAP]
            result.append({"id": str(c.get("id")), "facing": c.get("facing", "?"), "sizes": sizes})
        return result
    except Exception:
        return []

@router.get("/video/controls")
async def controls(request: Request):
    # Per-API supported image controls for the current camera (the app reports what each backend can do).
    backend = request.query_params.get("backend", "camera1-gl")
    code, data = await _app_get(f"/controls?backend={backend}")
    return data if code == 200 and data is not None else []

@router.get("/video/stream")
async def stream():
    async with _V["lock"]:
        if not await _ensure_app():
            return Response("camera app failed to start", status_code=503)
    _V["viewers"] += 1; _touch()
    client = httpx.AsyncClient(verify=False, timeout=None)
    try:
        resp = await client.send(client.build_request("GET", f"{BASE}/h264"), stream=True)
    except Exception:
        _V["viewers"] = max(0, _V["viewers"] - 1); _touch(); await client.aclose()
        return Response("camera stream unavailable", status_code=502)
    async def gen():
        try:
            async for chunk in resp.aiter_raw():
                _V["last"] = time.monotonic()
                yield chunk
        finally:
            await resp.aclose(); await client.aclose()
            _V["viewers"] = max(0, _V["viewers"] - 1); _touch()
    return StreamingResponse(gen(), media_type=resp.headers.get("content-type", "video/h264"),
                             headers={"Cache-Control": "no-store"})

@router.get("/video/control")
async def control(request: Request):
    qs = request.url.query
    if not qs:
        return {"ok": False, "err": "no params"}
    # Flash brightness needs root LED sysfs (no torch-strength API < Android 13). Dual-mode:
    #   streaming -> the camera HAL owns the flash, so toggle the app's own torch (on/off);
    #   idle      -> drive the LED sysfs directly, clamped to the queried max brightness.
    if qs.startswith("flash="):
        try: n = int(qs.split("=", 1)[1])
        except ValueError: return {"ok": False, "err": "bad flash"}
        n = max(0, min(flash_max(), n))
        if _V["viewers"] > 0:
            code, _ = await _app_get(f"/?torch={'on' if n > 0 else 'off'}")
            return {"ok": code == 200, "mode": "torch"}
        off = f"echo 0 > {LED_SW}; echo 0 > {LED_T0}; echo 0 > {LED_T1}"
        # 0->N latch quirk: write 0 first, then N to both torch LEDs, then 2 to the switch.
        cmd = off if n == 0 else f"{off}; echo {n} > {LED_T0}; echo {n} > {LED_T1}; echo 2 > {LED_SW}"
        _su(cmd)
        return {"ok": True, "mode": "brightness"}
    code, _ = await _app_get(f"/?{qs}")
    return {"ok": code == 200, "code": code}

@router.get("/video/status")
async def status():
    return {"up": await _is_up(), "viewers": _V["viewers"], "flash_max": flash_max()}
