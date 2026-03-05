#!/usr/bin/env python3
"""
battery.py

Collects complete Windows battery telemetry.
"""

import os
import sys
import json
import subprocess
import datetime
import tempfile
import re
from pathlib import Path
import time
import uuid
from config import DEVICE_ID

# Optional imports
try:
    import psutil
except Exception:
    psutil = None

try:
    import ctypes
    from ctypes import Structure, byref
except Exception:
    ctypes = None

try:
    import wmi
except Exception:
    wmi = None


def now_iso():
    return datetime.datetime.now().astimezone().isoformat()


def get_psutil_info():
    if psutil is None:
        return {"available": False, "reason": "psutil not installed"}
    try:
        bat = psutil.sensors_battery()
        if bat is None:
            return {"available": False, "reason": "no battery detected"}
        return {
            "available": True,
            "percent": bat.percent if bat.percent is not None else "unknown",
            "secsleft": bat.secsleft if bat.secsleft != psutil.POWER_TIME_UNLIMITED else -1,
            "power_plugged": bool(bat.power_plugged),
        }
    except Exception as e:
        return {"available": False, "error": str(e)}


def query_wmic():
    data = {"available": False, "source": "wmic", "properties": {}}
    try:
        cmd = ["wmic", "path", "Win32_Battery", "get", "/format:list"]
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        props = {}
        for ln in lines:
            if "=" in ln:
                k, v = ln.split("=", 1)
                props[k.strip()] = v.strip() or "N/A"
        if props:
            data["available"] = True
            data["properties"] = props
        else:
            data["reason"] = "no properties"
    except Exception as e:
        data["reason"] = str(e)
    return data


def generate_battery_report(output_path: Path):
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.check_output(
            ["powercfg", "/batteryreport", "/output", str(output_path)],
            stderr=subprocess.DEVNULL,
            text=True
        )
        return str(output_path) if output_path.exists() else None
    except Exception:
        return None


def parse_battery_report_html(html_text):
    result = {}
    t = re.sub(r">\s+<", "><", html_text)

    def find_after(label):
        pattern = re.compile(
            re.escape(label) + r".{0,80}?>([\d,]+)\s*mWh",
            re.IGNORECASE | re.DOTALL
        )
        m = pattern.search(t)
        if m:
            try:
                return int(m.group(1).replace(",", ""))
            except ValueError:
                return None
        return None

    result["design_capacity_mwh"] = find_after("DESIGN CAPACITY")
    result["full_charge_capacity_mwh"] = find_after("FULL CHARGE CAPACITY")

    m = re.search(r"CYCLE COUNT[^<]{0,60}?>([\d,]+)<", t, re.IGNORECASE)
    if m:
        try:
            result["cycle_count"] = int(m.group(1).replace(",", ""))
        except ValueError:
            result["cycle_count"] = None

    for label in ("Manufacturer", "Model", "Serial Number", "Battery name"):
        m = re.search(
            re.escape(label) + r"\s*</th>\s*<td[^>]*>\s*([^<]+)\s*</td>",
            t,
            re.IGNORECASE
        )
        if m:
            result[label.lower().replace(" ", "_")] = m.group(1).strip()

    return result


def get_report_info():
    tmp = Path(tempfile.gettempdir()) / f"battery_report_{os.getpid()}.html"
    path = generate_battery_report(tmp)
    if not path:
        return {"available": False, "reason": "could not generate battery report"}
    try:
        text = tmp.read_text(encoding="utf-8", errors="ignore")
        parsed = parse_battery_report_html(text)
        parsed["report_path"] = str(tmp)
        parsed["available"] = True
        return parsed
    except Exception as e:
        return {"available": False, "reason": str(e)}


class SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [
        ("ACLineStatus", ctypes.c_byte),
        ("BatteryFlag", ctypes.c_byte),
        ("BatteryLifePercent", ctypes.c_byte),
        ("Reserved1", ctypes.c_byte),
        ("BatteryLifeTime", ctypes.c_ulong),
        ("BatteryFullLifeTime", ctypes.c_ulong),
    ]


def get_system_power_status():
    if ctypes is None or os.name != "nt":
        return {"available": False}
    try:
        status = SYSTEM_POWER_STATUS()
        if not ctypes.windll.kernel32.GetSystemPowerStatus(byref(status)):
            return {"available": False}
        return {
            "available": True,
            "ACLineStatus": int(status.ACLineStatus),
            "BatteryFlag": int(status.BatteryFlag),
            "BatteryLifePercent": int(status.BatteryLifePercent),
            "BatteryLifeTime_seconds": int(status.BatteryLifeTime),
            "BatteryFullLifeTime_seconds": int(status.BatteryFullLifeTime),
        }
    except Exception as e:
        return {"available": False, "error": str(e)}


def query_wmi_root_wmi():
    data = {"available": False, "source": "root\\WMI", "classes": {}}
    if wmi is None:
        data["reason"] = "python-wmi not installed"
        return data
    try:
        c = wmi.WMI(namespace="root\\WMI")
        classes = [
            "BatteryStatus",
            "BatteryStaticData",
            "BatteryFullChargedCapacity",
            "BatteryCycleCount",
            "BatteryTemperature",
            "BatteryManufactureDate",
            "BatteryUniqueID",
            "BatteryRemainingCapacity",
        ]
        for cls in classes:
            try:
                instances = c.instances(cls)
                if instances:
                    data["classes"][cls] = [
                        {k: getattr(i, k, None) for k in i.properties}
                        for i in instances
                    ]
            except Exception:
                pass
        data["available"] = bool(data["classes"])
    except Exception as e:
        data["reason"] = str(e)
    return data


def collect_battery_snapshot():
    full_object = {
        "timestamp": now_iso(),
        "platform": sys.platform,
        "psutil": get_psutil_info(),
        "wmic": query_wmic(),
        "system_power_status": get_system_power_status(),
        "battery_report": get_report_info(),
        "root_wmi": query_wmi_root_wmi(),
    }

    return {
        "device_id": DEVICE_ID,
        "timestamp": int(time.time()),
        "battery_data": full_object,
    }
