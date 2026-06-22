"""System telemetry from /sys + /proc. Collectors ported from extras/system.py, plus per-core freq/governor."""
import glob, os, time
from fastapi import APIRouter

router = APIRouter()

def _read(p, d=""):
    try:
        with open(p) as f: return f.read().strip()
    except Exception: return d
def _ri(p, d=0):
    try: return int(_read(p))
    except Exception: return d
def _zt(x): return x / 1000.0 if abs(x) >= 1000 else float(x)

def thermal_rows():
    out = []
    for z in glob.glob("/sys/class/thermal/thermal_zone*"):
        t = _read(z + "/type"); v = _ri(z + "/temp")
        if t and v: out.append((t, _zt(v)))
    return sorted(out, key=lambda x: -x[1])

def cpu_temps():
    cpu, pm = [], None
    for t, x in thermal_rows():
        if t.startswith("tsens_tz_sensor"): cpu.append(x)
        elif t == "pm8950_tz": pm = x
    return (sum(cpu) / len(cpu) if cpu else 0.0), (max(cpu) if cpu else 0.0), pm

def online_cpus():
    s = _read("/sys/devices/system/cpu/online", ""); out = set()
    for part in s.split(","):
        if "-" in part:
            try: a, b = part.split("-"); out.update(range(int(a), int(b) + 1))
            except Exception: pass
        elif part.strip():
            try: out.add(int(part))
            except Exception: pass
    return out

def _cpufreq(n):
    b = f"/sys/devices/system/cpu/cpu{n}/cpufreq/"
    return _ri(b + "scaling_cur_freq"), _ri(b + "scaling_max_freq"), _read(b + "scaling_governor")

_pstat = {}  # ponytail: module-level delta state; first call reads 0%, frontend polls so it self-corrects
def cpu_stats():
    on = online_cpus(); per, busy, tot = [], 0, 0
    for line in _read("/proc/stat").splitlines():
        p = line.split()
        if not p or not p[0].startswith("cpu") or p[0] == "cpu": continue
        try: n = int(p[0][3:]); v = list(map(int, p[1:8]))
        except Exception: continue
        idle = v[3] + v[4]; total = sum(v)
        pt, pi = _pstat.get(n, (total, idle)); _pstat[n] = (total, idle)
        dt, di = total - pt, idle - pi
        online = n in on
        load = max(0.0, min(1.0, 1 - di / dt)) if (online and dt > 0) else 0.0
        cur, mx, gov = _cpufreq(n)
        per.append({"cpu": n, "load": load, "online": online, "mhz": cur // 1000, "max_mhz": mx // 1000, "gov": gov})
        if online and dt > 0: busy += dt - di; tot += dt
    per.sort(key=lambda d: d["cpu"])
    return (busy / tot if tot > 0 else 0.0), per

KGSL = "/sys/class/kgsl/kgsl-3d0/"
def gpu_info():
    frac = 0.0
    try:
        b, tot = map(int, _read(KGSL + "gpubusy").split()); frac = b / tot if tot else 0.0
    except Exception: pass
    cur = _ri(KGSL + "devfreq/cur_freq") or _ri(KGSL + "gpuclk")
    mx = _ri(KGSL + "devfreq/max_freq") or _ri(KGSL + "max_gpuclk")
    return frac, cur, mx

def battery():
    b = "/sys/class/power_supply/battery/"
    cap = _ri(b + "capacity"); status = _read(b + "status", "?"); health = _read(b + "health", "?")
    temp = _ri(b + "temp"); temp = temp / 10.0 if abs(temp) >= 100 else float(temp)
    volt = _ri(b + "voltage_now"); volt = volt / 1e6 if volt > 100000 else volt / 1000.0
    cur = _ri(b + "current_now"); cur = cur / 1000.0 if abs(cur) >= 1000 else float(cur)
    tech = _read(b + "technology", "?")
    return cap, status, health, temp, volt, cur, tech

_net = {"t": 0.0}
def net_rate():
    rx = _ri("/sys/class/net/wlan0/statistics/rx_bytes"); tx = _ri("/sys/class/net/wlan0/statistics/tx_bytes")
    now = time.monotonic(); dt = (now - _net["t"]) or 1.0
    rr = max(0.0, (rx - _net.get("rx", rx)) / dt); tr = max(0.0, (tx - _net.get("tx", tx)) / dt)
    _net.update(rx=rx, tx=tx, t=now); return rr, tr, rx, tx

def wifi_link():
    for line in _read("/proc/net/wireless").splitlines():
        s = line.split()
        if s and s[0] == "wlan0:":
            try: return float(s[2].rstrip(".")), float(s[3].rstrip("."))
            except Exception: break
    return None, None

def disk_free(path="/data"):
    try:
        s = os.statvfs(path); tot = s.f_blocks * s.f_frsize
        return tot, tot - s.f_bavail * s.f_frsize, s.f_bavail * s.f_frsize
    except Exception: return 0, 0, 0

def mem():
    m = {}
    for line in _read("/proc/meminfo").splitlines():
        k, _, v = line.partition(":"); parts = v.split()
        if parts: m[k] = int(parts[0]) * 1024
    tot = m.get("MemTotal", 0)
    avail = m.get("MemAvailable")
    if avail is None:  # older Android kernels omit MemAvailable; approximate like `free`
        avail = m.get("MemFree", 0) + m.get("Buffers", 0) + m.get("Cached", 0) + m.get("SReclaimable", 0)
    swt = m.get("SwapTotal", 0); swf = m.get("SwapFree", 0)
    return tot, tot - avail, avail, swt, swt - swf

@router.get("/stats")
def stats():
    cu, per = cpu_stats(); gf, gc, gm = gpu_info(); cavg, cmax, pm = cpu_temps()
    cap, st, hl, bt, vo, cr, tech = battery()
    rr, tr, trx, ttx = net_rate(); _lq, lv = wifi_link()
    dtot, dused, dfree = disk_free(); mtot, mused, mfree, swt, swu = mem()
    up = _read("/proc/uptime").split()
    return {
        "time": time.time(),
        "uptime": float(up[0]) if up else 0,
        "loadavg": _read("/proc/loadavg").split()[:3],
        "cpu": {"load": cu, "per": per, "online": sum(1 for d in per if d["online"]),
                "count": len(per), "temp_avg": cavg, "temp_max": cmax, "pmic": pm},
        "gpu": {"load": gf, "cur_mhz": gc // 1000000, "max_mhz": gm // 1000000},
        "battery": {"capacity": cap, "status": st, "health": hl, "temp": bt,
                    "voltage": vo, "current": cr, "power": vo * cr / 1000.0, "tech": tech},
        "net": {"rx_rate": rr, "tx_rate": tr, "rx_total": trx, "tx_total": ttx, "signal_dbm": lv},
        "disk": {"total": dtot, "used": dused, "free": dfree},
        "mem": {"total": mtot, "used": mused, "free": mfree, "swap_total": swt, "swap_used": swu},
    }

@router.get("/thermal")
def thermal():
    return [{"type": t, "temp": v} for t, v in thermal_rows()]
