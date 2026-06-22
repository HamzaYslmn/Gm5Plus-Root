"""Camera over HTTP with a decoupled capture pipeline.

A single background capture loop per camera (the camera's own 'core') runs independently of the
request handlers and keeps a latest-frame cache up to date. /stream and /snapshot read that cache,
so HTTP latency is decoupled from the ~3-4s hardware capture time and N viewers share ONE capture
loop instead of each triggering their own.

ponytail: raw JPEG passthrough (no re-encode); termux-camera-photo cold-opens the camera every
frame -> hard FPS ceiling. No OpenCV and no android_camera ffmpeg input exist on this device."""
import asyncio, os, tempfile, time
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, Response

router = APIRouter()
_cams = {}
def _st(cid):
    return _cams.setdefault(cid, {"frame": None, "ts": 0.0, "viewers": 0,
                                  "task": None, "lock": asyncio.Lock()})

async def _capture(cid):
    path = os.path.join(tempfile.gettempdir(), f"cam{cid}.jpg")
    try: os.remove(path)
    except OSError: pass
    proc = await asyncio.create_subprocess_exec(
        "termux-camera-photo", "-c", str(cid), path,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
    try:
        await asyncio.wait_for(proc.wait(), timeout=30)
    except asyncio.TimeoutError:
        proc.kill(); return None
    try:
        with open(path, "rb") as f: return f.read() or None
    except OSError:
        return None

async def _loop(cid):
    st = _st(cid)
    while st["viewers"] > 0:
        data = await _capture(cid)
        if data: st["frame"], st["ts"] = data, time.monotonic()
        else: await asyncio.sleep(0.3)
    st["task"] = None

def _ensure_loop(cid):
    st = _st(cid)
    if not st["task"] or st["task"].done():
        st["task"] = asyncio.create_task(_loop(cid))

@router.get("/camera/{cid}/snapshot")
async def snapshot(cid: int):
    st = _st(cid)
    if st["task"] and not st["task"].done():   # loop already running -> serve freshest cached frame
        for _ in range(60):
            if st["frame"]:
                return Response(st["frame"], media_type="image/jpeg", headers={"Cache-Control": "no-store"})
            await asyncio.sleep(0.1)
    async with st["lock"]:                      # otherwise one-off capture
        data = await _capture(cid)
    if not data:
        return Response("capture failed", status_code=503)
    st["frame"], st["ts"] = data, time.monotonic()
    return Response(data, media_type="image/jpeg", headers={"Cache-Control": "no-store"})

@router.get("/camera/{cid}/stream")
async def stream(cid: int):
    st = _st(cid); st["viewers"] += 1; _ensure_loop(cid)
    async def gen():
        last = 0.0
        try:
            while True:
                if st["frame"] and st["ts"] != last:
                    last = st["ts"]; d = st["frame"]
                    yield (b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                           + str(len(d)).encode() + b"\r\n\r\n" + d + b"\r\n")
                await asyncio.sleep(0.15)
        finally:
            st["viewers"] = max(0, st["viewers"] - 1)
    return StreamingResponse(gen(), media_type="multipart/x-mixed-replace; boundary=frame",
                             headers={"Cache-Control": "no-store"})
