"""Live sensors via ONE background `termux-sensor` reader that auto-stops when idle.
Values are trimmed to the meaningful count per sensor type (many sensors pad a fixed 16-float
array with zeros/junk), so the UI stays clean.
ponytail: -a opens every sensor (battery/CPU cost on this slow phone), so the reader self-terminates
after IDLE seconds with no /api/sensors request, and `termux-sensor -c` releases the HAL."""
import json, math, re, subprocess, threading, time
from fastapi import APIRouter

router = APIRouter()
IDLE = 15.0
_S = {"data": {}, "proc": None, "last": 0.0, "lock": threading.Lock(), "started": 0.0}

def _reader(proc):
    buf, depth = "", 0
    for line in proc.stdout:
        if time.monotonic() - _S["last"] > IDLE:
            break
        buf += line; depth += line.count("{") - line.count("}")
        if depth <= 0 and buf.strip():
            try:
                obj = json.loads(buf)
                for k, v in obj.items():
                    if isinstance(v, dict) and "values" in v:
                        _S["data"][k] = v["values"]
            except Exception: pass
            buf, depth = "", 0
    try: proc.terminate()
    except Exception: pass
    subprocess.run(["termux-sensor", "-c"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    _S["proc"] = None; _S["data"] = {}

def _ensure():
    _S["last"] = time.monotonic()
    with _S["lock"]:
        if _S["proc"] and _S["proc"].poll() is None:
            return
        try:
            p = subprocess.Popen(["termux-sensor", "-a", "-d", "1000"],
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        except Exception:
            return
        _S["proc"] = p; _S["started"] = time.monotonic()
        threading.Thread(target=_reader, args=(p,), daemon=True).start()

# --- naming / units / value count ---
def _norm(name):
    nl = re.sub(r"[-_ ]*\b(non[- ]?wakeup|wake[- ]?up|wakeup|uncalibrated|secondary)\b[-_ ]*", " ", name.lower())
    return re.sub(r"\s+", " ", nl).strip(" -_")
def _rank(name):
    nl = name.lower()
    return (("uncalib" in nl) + ("wake" in nl) + ("secondary" in nl) + ("dummy" in nl), len(name))
def _clean(name):  # drop repeated tokens: "MMC3524xPJ MMC3524xPJ" -> "MMC3524xPJ"
    out = []
    for p in name.split():
        if not out or out[-1].lower() != p.lower(): out.append(p)
    return " ".join(out)
def _unit(nl):
    if "rotat" in nl or "game" in nl: return "quat"      # rotation vectors before magn (GeoMagnetic Rotation Vector)
    if "gyro" in nl: return "rad/s"
    if "accel" in nl or "linear" in nl or "gravity" in nl: return "m/s2"
    if "magn" in nl or "mmc" in nl: return "uT"
    if "orient" in nl: return "deg"
    if "light" in nl or "als" in nl or "ltr" in nl: return "lux"
    if "prox" in nl: return "cm"
    if "step" in nl or "pedom" in nl: return "steps"
    if "press" in nl or "baro" in nl: return "hPa"
    return ""
_NCOUNT = {"quat": 4, "m/s2": 3, "rad/s": 3, "uT": 3, "deg": 3, "lux": 1, "cm": 1, "steps": 1, "hPa": 1}
def _trim(vals, unit):
    v = list(vals[:_NCOUNT.get(unit, 3)])
    while len(v) > 1 and abs(v[-1]) < 1e-6: v.pop()   # drop zero padding
    return [round(x, 3) for x in v]

def _merged():
    best = {}
    for k, v in _S["data"].items():
        nk, rk = _norm(k), _rank(k)
        if nk not in best or rk < best[nk][0]: best[nk] = (rk, k, v)
    return [(k, v) for _, k, v in sorted(best.values(), key=lambda r: r[1].lower())]

@router.get("/sensors")
def sensors():
    _ensure()
    merged = _merged()
    rows = []
    for k, v in merged:
        unit = _unit(k.lower())
        rows.append({"name": _clean(k), "values": _trim(v, unit), "unit": unit})
    derived = []
    mag = next((v for k, v in merged if "magn" in k.lower() or "mmc" in k.lower()), None)
    if mag and len(mag) >= 2:
        az = math.degrees(math.atan2(-mag[1], mag[0])) % 360
        derived.append({"name": "Compass", "values": [round(az, 1)], "unit": "deg"})
    warming = (not rows) and (time.monotonic() - _S["started"] < 4)
    return {"sensors": rows, "derived": derived, "count": len(rows),
            "status": "warming up" if warming else ("ok" if rows else "no data (termux-api?)")}
