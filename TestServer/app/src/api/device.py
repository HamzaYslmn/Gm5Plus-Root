"""Static device identity + live network interfaces + wifi."""
import json, os, subprocess
from functools import lru_cache
from fastapi import APIRouter

router = APIRouter()

def _getprop(k):
    try: return subprocess.run(["getprop", k], capture_output=True, text=True, timeout=4).stdout.strip()
    except Exception: return ""

@lru_cache(maxsize=1)
def _info():
    keys = {
        "model": "ro.product.model", "brand": "ro.product.brand", "device": "ro.product.device",
        "manufacturer": "ro.product.manufacturer", "android": "ro.build.version.release",
        "sdk": "ro.build.version.sdk", "security_patch": "ro.build.version.security_patch",
        "build": "ro.build.display.id", "abi": "ro.product.cpu.abi",
        "hardware": "ro.hardware", "board": "ro.product.board", "bootloader": "ro.bootloader",
    }
    out = {k: _getprop(v) for k, v in keys.items()}
    try: out["kernel"] = open("/proc/version").read().strip()
    except Exception: pass
    try:
        for line in open("/proc/cpuinfo"):
            if line.lower().startswith("hardware"):
                out["soc"] = line.split(":", 1)[1].strip()
    except Exception: pass
    return out

@router.get("/device")
def device():
    try: up = float(open("/proc/uptime").read().split()[0])
    except Exception: up = 0.0
    return {**_info(), "uptime": up}

def _iface(name):
    base = f"/sys/class/net/{name}/"
    def r(p, d=""):
        try: return open(base + p).read().strip()
        except Exception: return d
    return {"name": name, "state": r("operstate", "?"), "mac": r("address"),
            "mtu": r("mtu"), "speed": r("speed"),
            "rx": int(r("statistics/rx_bytes", "0") or 0),
            "tx": int(r("statistics/tx_bytes", "0") or 0)}

@router.get("/network")
def network():
    ifaces = []
    try:
        for n in sorted(os.listdir("/sys/class/net")):
            i = _iface(n)
            if i["name"] == "lo" or i["state"] == "up" or i["rx"] or i["tx"]:
                ifaces.append(i)
    except Exception: pass
    wifi = None
    try:
        wifi = json.loads(subprocess.run(["termux-wifi-connectioninfo"],
                          capture_output=True, text=True, timeout=6).stdout)
    except Exception: pass
    return {"interfaces": ifaces, "wifi": wifi}
