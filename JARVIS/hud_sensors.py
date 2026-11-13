"""
Real hardware telemetry for the JARVIS HUD.

Everything here reads live values from the machine — nothing is faked or
placeholder. Each getter degrades gracefully (returns None / 0) when the
underlying source is unavailable, so the HUD can hide or dim a readout
rather than showing a lie.
"""

from __future__ import annotations

import os
import platform
import re
import shutil
import socket
import subprocess
import threading
import time
from collections import deque
from pathlib import Path

import psutil

_LOCK = threading.Lock()


# --------------------------------------------------------------------------
# CPU
# --------------------------------------------------------------------------
def cpu_percent() -> float:
    try:
        return float(psutil.cpu_percent(interval=None))
    except Exception:
        return 0.0


def cpu_per_core() -> list[float]:
    try:
        return [float(v) for v in psutil.cpu_percent(interval=None, percpu=True)]
    except Exception:
        return []


def cpu_model() -> str:
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                if line.lower().startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    try:
        return platform.processor() or platform.machine() or "CPU"
    except Exception:
        return "CPU"


def cpu_freq_mhz() -> float:
    """Current CPU frequency in MHz (0.0 when it cannot be determined)."""
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                if line.lower().startswith("cpu mhz"):
                    return float(line.split(":", 1)[1].strip())
    except Exception:
        pass
    try:  # fallback: cpufreq
        out = subprocess.run(
            ["bash", "-lc",
             "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq 2>/dev/null"],
            capture_output=True, text=True, timeout=2,
        ).stdout.strip()
        if out.isdigit():
            return float(out) / 1000.0
    except Exception:
        pass
    try:
        f = psutil.cpu_freq()
        return float(f.current) if f else 0.0
    except Exception:
        return 0.0


# --------------------------------------------------------------------------
# Memory
# --------------------------------------------------------------------------
def mem_percent() -> float:
    try:
        return float(psutil.virtual_memory().percent)
    except Exception:
        return 0.0


def mem_detail() -> dict:
    try:
        vm = psutil.virtual_memory()
        return {
            "total": int(vm.total),
            "used": int(vm.used),
            "free": int(vm.free),
            "percent": float(vm.percent),
            "available": int(getattr(vm, "available", vm.free)),
            "swapped": int(getattr(psutil.swap_memory(), "used", 0)),
        }
    except Exception:
        return {"total": 0, "used": 0, "free": 0, "percent": 0.0,
                "available": 0, "swapped": 0}


# --------------------------------------------------------------------------
# GPU
# --------------------------------------------------------------------------
def gpu_info() -> dict:
    """Best-effort GPU model + utilisation via nvidia-smi, else /sys."""
    name, util, mem_used, mem_total, temp = "", None, None, None, None
    try:
        out = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3,
        )
        if out.returncode == 0 and out.stdout.strip():
            parts = [p.strip() for p in out.stdout.strip().splitlines()[0].split(",")]
            name = parts[0]
            util = _to_float(parts[1]) if len(parts) > 1 else None
            mem_used = _to_float(parts[2]) if len(parts) > 2 else None
            mem_total = _to_float(parts[3]) if len(parts) > 3 else None
            temp = _to_float(parts[4]) if len(parts) > 4 else None
    except Exception:
        pass

    if not name:  # DRM sysfs fallback
        try:
            for card in sorted(Path("/sys/class/drm").glob("card*/device/uevent")):
                txt = card.read_text(errors="ignore")
                m = re.search(r"DRIVER=(.+)", txt)
                if m:
                    name = m.group(1).strip()
                    break
        except Exception:
            pass
    if not name:
        try:
            lspci = shutil.which("lspci")
            if lspci:
                out = subprocess.run([lspci], capture_output=True, text=True, timeout=3).stdout
                for line in out.splitlines():
                    if re.search(r"VGA|3D|Display", line):
                        name = line.split(":", 2)[-1].strip()[:48]
                        break
        except Exception:
            pass

    return {"name": name or "GPU", "util": util, "mem_used": mem_used,
            "mem_total": mem_total, "temp": temp,
            "available": util is not None or bool(name)}


# --------------------------------------------------------------------------
# Disk
# --------------------------------------------------------------------------
def disk_percent(path: str = "/") -> float:
    try:
        return float(psutil.disk_usage(path).percent)
    except Exception:
        return 0.0


def disk_detail(path: str = "/") -> dict:
    try:
        d = psutil.disk_usage(path)
        return {"total": int(d.total), "used": int(d.used), "free": int(d.free),
                "percent": float(d.percent)}
    except Exception:
        return {"total": 0, "used": 0, "free": 0, "percent": 0.0}


def disk_io_mbps() -> float:
    """Disk throughput in MB/s over a short sampling window."""
    try:
        a = psutil.disk_io_counters()
        time.sleep(0.12)
        b = psutil.disk_io_counters()
        if not a or not b:
            return 0.0
        read = max(0, b.read_bytes - a.read_bytes)
        write = max(0, b.write_bytes - a.write_bytes)
        return ((read + write) / (1024 * 1024)) / 0.12
    except Exception:
        return 0.0


def disk_devices() -> list[dict]:
    out = []
    try:
        for part in psutil.disk_partitions(all=False):
            if not part.mountpoint:
                continue
            try:
                u = psutil.disk_usage(part.mountpoint)
            except Exception:
                continue
            out.append({
                "device": part.device,
                "mount": part.mountpoint,
                "fstype": part.fstype,
                "total": int(u.total),
                "used": int(u.used),
                "free": int(u.free),
                "percent": float(u.percent),
            })
    except Exception:
        pass
    return out


# --------------------------------------------------------------------------
# Network
# --------------------------------------------------------------------------
def net_percent() -> float:
    """Approximate link utilisation as a percentage of a 100 Mbit/s baseline."""
    try:
        a = psutil.net_io_counters()
        time.sleep(0.12)
        b = psutil.net_io_counters()
        if not a or not b:
            return 0.0
        sent = max(0, b.bytes_sent - a.bytes_sent)
        recv = max(0, b.bytes_recv - a.bytes_recv)
        mbps = ((sent + recv) * 8) / 0.12 / 1_000_000
        return min(100.0, mbps / 100.0 * 100.0)
    except Exception:
        return 0.0


def net_mbps() -> float:
    try:
        a = psutil.net_io_counters()
        time.sleep(0.12)
        b = psutil.net_io_counters()
        if not a or not b:
            return 0.0
        sent = max(0, b.bytes_sent - a.bytes_sent)
        recv = max(0, b.bytes_recv - a.bytes_recv)
        return ((sent + recv) * 8) / 0.12 / 1_000_000
    except Exception:
        return 0.0


def ip_address() -> str:
    """Primary outbound IP (falls back to the hostname address)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.4)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        pass
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return "0.0.0.0"


def active_adapter() -> str:
    """Name of the primary non-loopback, up network interface."""
    try:
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        fallback = ""
        for name, info in stats.items():
            if not getattr(info, "isup", False):
                continue
            if name == "lo" or name.startswith("lo"):
                continue          # never report loopback as "the adapter"
            has_v4 = any(
                getattr(a, "address", "").count(".") == 3
                for a in (addrs.get(name) or [])
            )
            if has_v4:
                return name
            fallback = fallback or name
        if fallback:
            return fallback
    except Exception:
        pass
    return "offline"


def wifi_ssid() -> str:
    try:
        out = subprocess.run(
            ["nmcli", "-t", "-f", "ACTIVE,SSID", "device", "wifi"],
            capture_output=True, text=True, timeout=3,
        )
        for line in out.stdout.splitlines():
            if line.startswith("yes:"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return ""


def ping_ms(host: str = "8.8.8.8") -> float | None:
    """Latency in ms, or None when unreachable."""
    try:
        out = subprocess.run(
            ["ping", "-c", "1", "-W", "1", host],
            capture_output=True, text=True, timeout=3,
        )
        m = re.search(r"time=([\d.]+)\s*ms", out.stdout)
        if m:
            return float(m.group(1))
    except Exception:
        pass
    return None


# --------------------------------------------------------------------------
# Temperature
# --------------------------------------------------------------------------
_TEMP_LABEL = (
    "package", "core 0", "tctl", "cpu", "soc", "acpitz", "thermal", "gpu", "nvme",
)


def temperatures() -> list[dict]:
    """All readable temperature sensors: [{label, celsius, high, critical}].

    ``psutil.sensors_temperatures(chip)`` returns a *list* in some psutil
    versions and a *dict* in others, so both shapes are normalised here.
    """
    out: list[dict] = []
    try:
        all_sensors = psutil.sensors_temperatures() or {}
    except Exception:
        all_sensors = {}

    for name, entries in all_sensors.items():
        if isinstance(entries, dict):
            iterable = list(entries.values())
        elif isinstance(entries, (list, tuple)):
            iterable = list(entries)
        else:
            continue
        for entry in iterable:
            cur = getattr(entry, "current", None)
            if cur is None:
                continue
            try:
                cur = float(cur)
            except (TypeError, ValueError):
                continue
            if cur <= 0:      # many drivers report 0 for unpopulated sensors
                continue
            out.append({
                "chip": str(name),
                "label": str(getattr(entry, "label", "") or name),
                "celsius": cur,
                "high": float(getattr(entry, "high", 0) or 0),
                "critical": float(getattr(entry, "critical", 0) or 0),
            })

    if not out:  # raw sysfs fallback
        for base in ("/sys/class/hwmon", "/sys/class/thermal"):
            p = Path(base)
            if not p.is_dir():
                continue
            files = sorted(p.glob("**/temp*_input")) + sorted(p.glob("**/temp"))
            for f in files:
                try:
                    raw = float(f.read_text().strip())
                except Exception:
                    continue
                if raw <= 0:
                    continue
                # hwmon uses tempN_input in millidegrees; thermal zones use a
                # plain `temp` file already expressed in degrees.
                celsius = raw / 1000.0 if f.name.endswith("_input") else raw
                out.append({
                    "chip": base.rsplit("/", 1)[-1],
                    "label": f.parent.name,
                    "celsius": celsius,
                    "high": 0.0,
                    "critical": 0.0,
                })
    return out


def cpu_temperature() -> float | None:
    """Representative CPU/package temperature, or None if no sensor exists."""
    sensors = temperatures()
    if not sensors:
        return None
    for pref in _TEMP_LABEL:
        for s in sensors:
            if pref in s["label"].lower() or pref in s["chip"].lower():
                return s["celsius"]
    return sensors[0]["celsius"]


def temperature_label() -> str:
    """Human label for whichever sensor cpu_temperature() picked."""
    sensors = temperatures()
    if not sensors:
        return "NO SENSOR"
    for pref in _TEMP_LABEL:
        for s in sensors:
            if pref in s["label"].lower() or pref in s["chip"].lower():
                return (s["label"] or s["chip"])[:18].upper()
    return (sensors[0]["label"] or sensors[0]["chip"])[:18].upper()


def temperature_summary() -> dict:
    """Label + value + a coarse band used to colour the HUD gauge."""
    c = cpu_temperature()
    if c is None:
        return {"celsius": None, "label": "NO SENSOR", "band": "none"}
    if c < 45:
        band = "cool"
    elif c < 70:
        band = "fair"
    elif c < 85:
        band = "warm"
    else:
        band = "hot"
    return {"celsius": c, "label": band.upper(), "band": band,
            "sensor": temperature_label()}


# --------------------------------------------------------------------------
# Host / power / battery
# --------------------------------------------------------------------------
def hostname() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return "localhost"


def username() -> str:
    try:
        return os.environ.get("USER") or os.environ.get("LOGNAME") or "user"
    except Exception:
        return "user"


def home_dir() -> str:
    return str(Path.home())


def uptime_human() -> str:
    try:
        secs = int(time.time() - psutil.boot_time())
        d, rem = divmod(secs, 86400)
        h, rem = divmod(rem, 3600)
        m = rem // 60
        if d:
            return f"{d}d {h}h {m}m"
        if h:
            return f"{h}h {m}m"
        return f"{m}m"
    except Exception:
        return "--"


def battery() -> dict:
    try:
        b = psutil.sensors_battery()
    except Exception:
        b = None
    if b is None:
        return {"present": False, "percent": None, "plugged": None}
    return {"present": True,
            "percent": round(float(b.percent), 1) if b.percent is not None else None,
            "plugged": bool(b.power_plugged)}


def load_average() -> tuple[float, float, float]:
    try:
        a = os.getloadavg()
        return float(a[0]), float(a[1]), float(a[2])
    except Exception:
        return 0.0, 0.0, 0.0


def host_summary() -> dict:
    """One-shot snapshot of everything the HUD needs."""
    with _LOCK:
        return {
            "host": hostname(),
            "user": username(),
            "ip": ip_address(),
            "adapter": active_adapter(),
            "uptime": uptime_human(),
            "load": load_average(),
            "cpu_pct": cpu_percent(),
            "cpu_mhz": cpu_freq_mhz(),
            "mem": mem_detail(),
            "disk": disk_detail("/"),
            "net_pct": net_percent(),
            "temp": temperature_summary(),
            "gpu": gpu_info(),
            "battery": battery(),
        }


# --------------------------------------------------------------------------
# Rolling history for sparklines
# --------------------------------------------------------------------------
class Series:
    """Fixed-length rolling sample buffer for a sparkline."""

    __slots__ = ("_buf", "_max", "_lock")

    def __init__(self, length: int = 90) -> None:
        self._buf: deque[float] = deque([0.0] * length, maxlen=length)
        self._max = length
        self._lock = threading.Lock()

    def push(self, value: float) -> None:
        try:
            v = float(value)
        except (TypeError, ValueError):
            v = 0.0
        with self._lock:
            self._buf.append(max(0.0, min(100.0, v)))

    def values(self) -> list[float]:
        with self._lock:
            return list(self._buf)

    def last(self) -> float:
        with self._lock:
            return self._buf[-1] if self._buf else 0.0

    def peak(self) -> float:
        with self._lock:
            return max(self._buf) if self._buf else 0.0


def human_bytes(n: float | int | None) -> str:
    if not n:
        return "0B"
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if abs(n) < 1024.0:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}EB"


def human_rate(mbps: float | None) -> str:
    if mbps is None:
        return "--"
    if mbps >= 1.0:
        return f"{mbps:.1f}Mb"
    return f"{mbps * 1000:.0f}Kb"


def _to_float(text: str):
    try:
        return float(str(text).strip().rstrip("%"))
    except (TypeError, ValueError):
        return None
