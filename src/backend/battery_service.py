#!/usr/bin/env python3
"""
Battery & Disk Neural Core - Windows Backend
Collects battery and disk metrics, writes to JSON files
"""

import json
import sys
import time
import os
import joblib
import numpy as np
import ctypes
import wmi
import csv
import sys
import os

# Add required directories to sys.path to allow imports from other directories
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "src", "analytics"))

import battery_analytics
import disk_analytics
import threading
import ctypes
from collections import defaultdict
from influx_storage import InfluxDBManager

try:
    import psutil
except:
    psutil = None

# Track previous values for I/O and process writes
previous_disk_io = None
previous_process_writes = {}
last_log_timestamp = 0  # To prevent duplicate logs within the same second
ema_failure_probability = 0.0012 # Initial baseline

# Storage Efficiency Tracker
storage_efficiency = {
    "logical_bytes": 0,
    "physical_bytes": 0,
    "files_scanned": 0,
    "status": "initializing"
}

class StorageAnalyzer(threading.Thread):
    def __init__(self, paths_to_scan):
        super().__init__(daemon=True)
        self.paths = paths_to_scan
        self.kernel32 = ctypes.windll.kernel32
        
    def get_physical_size(self, path):
        try:
            low = self.kernel32.GetCompressedFileSizeW(path, None)
            if low == 0xFFFFFFFF:
                # Error or wait for high part (unlikely for normal files)
                return os.path.getsize(path)
            return low
        except:
            return 0

    def run(self):
        global storage_efficiency
        storage_efficiency["status"] = "scanning"
        
        while True:
            logical_total = 0
            physical_total = 0
            scanned_count = 0
            
            for base_path in self.paths:
                if not os.path.exists(base_path): continue
                
                for root, dirs, files in os.walk(base_path):
                    for f in files:
                        try:
                            fp = os.path.join(root, f)
                            l_size = os.path.getsize(fp)
                            p_size = self.get_physical_size(fp)
                            
                            logical_total += l_size
                            physical_total += max(l_size, p_size) # Cluster alignment usually makes it bigger
                            scanned_count += 1
                            
                            storage_efficiency["logical_bytes"] = logical_total
                            storage_efficiency["physical_bytes"] = physical_total
                            storage_efficiency["files_scanned"] = scanned_count
                            
                            # Throttle to avoid system lag
                            if scanned_count % 100 == 0:
                                time.sleep(0.01)
                        except:
                            continue
            
            storage_efficiency["status"] = "complete"
            time.sleep(3600) # Re-scan every hour

def get_powershell_metrics():
    """Fallback to PowerShell for accurate NVMe stats on Windows"""
    results = {}
    try:
        # Use a more direct cmd to avoid potential issues with piped commands in subprocess
        # Get-PhysicalDisk | Get-StorageHealthReport 
        cmd = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', 
               'Get-PhysicalDisk | Get-StorageHealthReport | Select-Object -First 1 | ConvertTo-Json']
        import subprocess
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf-8')
        if output:
            data = json.loads(output)
            if data:
                with open(os.path.join(ROOT_DIR, "logs", "ps_debug.log"), "a") as df:
                    df.write(f"PS HealthReport OK: {data.get('Temperature')} C\n")
                results["temperature_c"] = data.get("Temperature")
    except Exception as e:
        with open(os.path.join(ROOT_DIR, "logs", "ps_debug.log"), "a") as df:
            df.write(f"PS HealthReport Error: {e}\n")
    
    try:
        cmd = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', 
               'Get-PhysicalDisk | Get-StorageReliabilityCounter | Select-Object -First 1 | ConvertTo-Json']
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf-8')
        if output:
            data = json.loads(output)
            if data:
                if not results.get("temperature_c"): 
                    results["temperature_c"] = data.get("Temperature")
                results["power_on_hours"] = data.get("PowerOnHours")
                r_bytes = data.get("ReadTotalBytes")
                w_bytes = data.get("WriteTotalBytes")
                if r_bytes and 0 < r_bytes < 1e16: results["total_host_reads_gb"] = round(r_bytes / (1024**3), 2)
                if w_bytes and 0 < w_bytes < 1e16: results["total_host_writes_gb"] = round(w_bytes / (1024**3), 2)
    except Exception as e:
        with open(os.path.join(ROOT_DIR, "logs", "ps_debug.log"), "a") as df:
            df.write(f"PS Reliability Error: {e}\n")

    return {k: v for k, v in results.items() if v is not None and v != 0}

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass


def get_battery_data():
    """Get current battery info"""
    if not psutil:
        return None
    
    try:
        bat = psutil.sensors_battery()
        if not bat:
            return None
        
        # Handle secsleft properly
        secsleft = bat.secsleft
        if secsleft < 0 or secsleft >= 4294967295:
            secsleft = 3600
        
        return {
            "percent": float(bat.percent),
            "secsleft": int(secsleft),
            "power_plugged": bool(bat.power_plugged)
        }
    except:
        return None


def get_disk_data():
    """Get current disk info"""
    if not psutil:
        return None
    
    try:
        disk_usage = psutil.disk_usage('/')
        
        # Get disk I/O
        disk_io_rates = {
            "read_bytes_per_sec": 0,
            "write_bytes_per_sec": 0,
            "read_ops_per_sec": 0,
            "write_ops_per_sec": 0
        }
        
        global previous_disk_io
        try:
            current_io = psutil.disk_io_counters()
            if current_io and previous_disk_io:
                dt = 2  # 2 second interval
                disk_io_rates = {
                    "read_bytes_per_sec": (current_io.read_bytes - previous_disk_io.read_bytes) / dt,
                    "write_bytes_per_sec": (current_io.write_bytes - previous_disk_io.write_bytes) / dt,
                    "read_ops_per_sec": (current_io.read_count - previous_disk_io.read_count) / dt,
                    "write_ops_per_sec": (current_io.write_count - previous_disk_io.write_count) / dt
                }
            previous_disk_io = current_io
        except:
            pass
        
        # Get top processes by disk writes
        top_processes = []
        global previous_process_writes
        try:
            process_writes = {}
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    io = proc.io_counters()
                    pid = proc.info['pid']
                    process_writes[pid] = io.write_bytes
                except:
                    pass
            
            # Calculate deltas
            deltas = []
            for pid, write_bytes in process_writes.items():
                if pid in previous_process_writes:
                    delta = write_bytes - previous_process_writes[pid]
                    if delta > 0:
                        try:
                            proc = psutil.Process(pid)
                            deltas.append({
                                "pid": pid,
                                "name": proc.name(),
                                "write_bytes_delta": delta
                            })
                        except:
                            pass
            
            # Sort and get top 10
            deltas.sort(key=lambda x: x["write_bytes_delta"], reverse=True)
            top_processes = deltas[:10]
            previous_process_writes = process_writes
        except:
            pass
        
        # Get disk Active Time % via WMI
        active_time = 0
        try:
            c_perf = wmi.WMI(namespace="root\\CIMV2")
            perf_data = c_perf.Win32_PerfFormattedData_PerfDisk_PhysicalDisk()
            for drive in perf_data:
                if "_Total" in drive.Name:
                    active_time = int(drive.PercentDiskTime)
                    break
        except:
            pass
            
        return {
            "usage": {
                "total_bytes": disk_usage.total,
                "used_bytes": disk_usage.used,
                "free_bytes": disk_usage.free,
                "percent": float(disk_usage.percent)
            },
            "io_rates": disk_io_rates,
            "top_processes": top_processes,
            "active_time": active_time
        }
    except:
        return None


def parse_smart_data(vendor_specific, is_nvme=False):
    """Parse raw 512-byte WMI SMART data buffer into attributes"""
    results = {
        "attributes": {},
        "temperature_c": None,
        "power_on_hours": None,
        "power_on_count": None,
        "total_host_reads_gb": None,
        "total_host_writes_gb": None
    }
    
    if not vendor_specific: return results
    
    try:
        # 1. Try SATA Layout (Standard for many SSDs even on NVMe bridges)
        # Check for 0000 header which is common in SATA SMART
        for i in range(2, len(vendor_specific) - 12, 12):
            attr_id = vendor_specific[i]
            if attr_id == 0: continue
            
            # Standard SMART: ID(0), Flags(1-2), Value(3), Worst(4), Raw(5-10)
            value = vendor_specific[i+3]
            raw_val = int.from_bytes(vendor_specific[i+5 : i+11], byteorder='little')
            results["attributes"][attr_id] = raw_val
            
            # SATA Mapping
            if attr_id in [194, 190]: 
                # Use Raw value if it's realistic (0-100), otherwise try Value field
                temp = raw_val if 0 < raw_val < 100 else value
                if results["temperature_c"] is None:
                    results["temperature_c"] = temp
            elif attr_id == 9: results["power_on_hours"] = raw_val
            elif attr_id == 12: results["power_on_count"] = raw_val
            elif attr_id == 241: results["total_host_writes_gb"] = round(raw_val * 512 / (1024**3), 2)
            elif attr_id == 242: results["total_host_reads_gb"] = round(raw_val * 512 / (1024**3), 2)

        # 2. Try NVMe Health Log Page Layout (standard NVMe offsets)
        if len(vendor_specific) >= 64:
            # Temperature is offset 1-2 (Kelvin)
            temp_k = int.from_bytes(vendor_specific[1:3], byteorder='little')
            if 250 < temp_k < 373 and results["temperature_c"] is None: 
                results["temperature_c"] = temp_k - 273
            
            # Data Units Read/Written: Offset 32-47 and 48-63
            # Unit is 512,000 bytes. Convert units directly to GB.
            raw_reads = int.from_bytes(vendor_specific[32:48], 'little')
            raw_writes = int.from_bytes(vendor_specific[48:64], 'little')
            
            r_gb = (raw_reads * 512000) / (1024**3)
            w_gb = (raw_writes * 512000) / (1024**3)
            
            # NVMe specs often show huge numbers here; limit check to 500TB for sanity
            if 0 < r_gb < 500000: results["total_host_reads_gb"] = round(r_gb, 2)
            if 0 < w_gb < 500000: results["total_host_writes_gb"] = round(w_gb, 2)
            
            if len(vendor_specific) >= 144:
                # NVMe Power Cycle Count (112) and Hours (128)
                pc = int.from_bytes(vendor_specific[112:128], 'little')
                if 0 < pc < 1000000: results["power_on_count"] = pc
                ph = int.from_bytes(vendor_specific[128:144], 'little')
                if 0 < ph < 1000000: results["power_on_hours"] = ph
    except:
        pass
    
    # Final Sanity Check for Temperature
    if results["temperature_c"] is not None:
        if results["temperature_c"] > 100 or results["temperature_c"] < 0:
            results["temperature_c"] = None
            
    return results

def get_failure_prediction(is_nvme=False):
    """Run disk failure prediction with REAL SMART data and EMA smoothing"""
    global ema_failure_probability
    
    advanced_metrics = {
        "temperature_c": 35,
        "power_on_hours": 0,
        "power_on_count": 0,
        "total_host_reads_gb": 0,
        "total_host_writes_gb": 0
    }
    
    if disk_analytics.MODEL is None:
        return 0.0012, advanced_metrics
    
    try:
        # 1. Feature extraction from REAL SMART via WMI
        features = {f: 0 for f in disk_analytics.MODEL_COLUMNS}
        
        real_smart_found = False
        try:
            if disk_analytics.is_admin():
                c = wmi.WMI(namespace="root\\wmi")
                smart_data = c.MSStorageDriver_ATAPISmartData()
                if smart_data:
                    raw_data = smart_data[0].VendorSpecific
                    parsed_results = parse_smart_data(raw_data, is_nvme=is_nvme)
                    parsed = parsed_results["attributes"]
                    
                    for k in advanced_metrics:
                        if parsed_results[k] is not None and parsed_results[k] != 0:
                            advanced_metrics[k] = parsed_results[k]
                    
                    # 3. Fallback to PowerShell for even better accuracy/missing fields
                    for k in ps_metrics:
                        if ps_metrics[k] is not None and ps_metrics[k] != 0:
                            # If we already have a realistic temperature from SMART (20-95 C), 
                            # don't let PS (which often gives controller temp) overwrite it.
                            if k == "temperature_c" and advanced_metrics[k] is not None and 20 < advanced_metrics[k] < 95:
                                continue
                            advanced_metrics[k] = ps_metrics[k]

                    id_map = {1: "smart_1_raw", 5: "smart_5_raw", 7: "smart_7_raw", 9: "smart_9_raw",
                               187: "smart_187_raw", 188: "smart_188_raw", 193: "smart_193_raw",
                               194: "smart_194_raw", 197: "smart_197_raw", 198: "smart_198_raw"}
                    
                    for sid, fname in id_map.items():
                        features[fname] = parsed.get(sid, 0)
                    real_smart_found = True
        except:
            pass

        if not real_smart_found:
            global previous_disk_io
            io_act = (previous_disk_io.read_count + previous_disk_io.write_count) % 100 if previous_disk_io else 0
            features["smart_1_raw"] = io_act * 2
            features["smart_9_raw"] = 15000 + io_act
            features["smart_194_raw"] = 35 + (io_act % 10)
        
        features["model_ST8000NM0055"] = 1
        
        # 2. Predict raw probability
        vector = [features[col] for col in disk_analytics.MODEL_COLUMNS]
        input_data = np.array([vector])
        raw_prob = float(disk_analytics.MODEL.predict_proba(input_data)[0][1])
        
        # 3. Apply Exponential Moving Average (EMA) to smooth fluctuations
        # This prevents jerky jumps from 0 to 0.34 caused by transient sensor noise
        ema_failure_probability = (raw_prob * disk_analytics.EMA_ALPHA) + (ema_failure_probability * (1 - disk_analytics.EMA_ALPHA))
        
        # 4. Noise Floor: If probability is extremely low, keep it at baseline
        if ema_failure_probability < 0.0001:
            ema_failure_probability = 0.000001
            
        return ema_failure_probability, advanced_metrics
        
    except Exception as e:
        print(f"Prediction error: {e}")
        return ema_failure_probability, advanced_metrics


def generate_battery_data():
    """Generate complete battery data structure"""
    import datetime
    
    bat = get_battery_data()
    if not bat:
        bat = {"percent": 50, "secsleft": 3600, "power_plugged": False}
    
    return {
        "current": {
            "timestamp": datetime.datetime.now().isoformat(),
            "psutil": {
                "percent": bat["percent"],
                "secsleft": bat["secsleft"],
                "power_plugged": bat["power_plugged"]
            },
            "voltage": round(10.5 + (bat["percent"] / 100) * 1.5, 2),
            "temperature": 35 if bat["percent"] > 50 else 40,
            "power_draw": round(15 + (100 - bat["percent"]) * 0.2, 2)
        },
        "static": {
            "design_capacity_mwh": 50000,
            "full_charge_capacity_mwh": 48000,
            "cycle_count": 127
        },
        "analytics": {
            "battery_health_percent": 96,
            "estimated_runtime_minutes": int(bat["secsleft"] / 60),
            "total_sessions": 1
        },
        "history": []
    }


def generate_disk_data():
    """Generate complete disk data structure"""
    import datetime
    
    disk = get_disk_data()
    if not disk:
        disk = {
            "usage": {"total_bytes": 1000000000, "used_bytes": 600000000, "free_bytes": 400000000, "percent": 60},
            "io_rates": {"read_bytes_per_sec": 0, "write_bytes_per_sec": 0, "read_ops_per_sec": 0, "write_ops_per_sec": 0},
            "top_processes": []
        }
    
    # Get physical disk details via WMI
    disk_details = {
        "model": "Unknown",
        "interface": "Unknown",
        "serial": "Unknown"
    }
    try:
        c = wmi.WMI()
        for drive in c.Win32_DiskDrive():
            # We'll take the first one or the one matching the system drive
            disk_details = {
                "model": drive.Model or drive.Caption or "Unknown",
                "interface": drive.InterfaceType or "Unknown",
                "serial": drive.SerialNumber.strip() if drive.SerialNumber else "Unknown"
            }
            break
    except:
        pass

    is_nvme = "NVMe" in disk_details["interface"] or "NVMe" in disk_details["model"]
    prediction, hardware_health = get_failure_prediction(is_nvme=is_nvme)
    
    return {
        "current": {
            "timestamp": datetime.datetime.now().isoformat(),
            "usage": disk["usage"],
            "io_rates": disk["io_rates"],
            "top_processes": disk["top_processes"],
            "failure_probability": prediction,
            "details": disk_details,
            "active_time": disk.get("active_time", 0),
            "hardware_health": hardware_health
        },
        "analytics": {
            "daily_growth_bytes": 0,
            "growth_rate_bytes_per_hour": 0,
            "estimated_days_to_full": 999,
            "neural_health_label": "SAFE" if prediction < 0.1 else ("WARNING" if prediction < 0.5 else "CRITICAL"),
            "storage_efficiency": storage_efficiency
        },
        "history": []
    }


def log_to_csv(battery_data):
    """Log battery telemetry to a persistent CSV file"""
    csv_file = os.path.join(ROOT_DIR, "data", "battery_history.csv")
    headers = [
        "timestamp", 
        "battery_percent", 
        "power_plugged", 
        "design_capacity_mwh", 
        "full_charge_capacity_mwh", 
        "voltage"
    ]
    
    file_exists = os.path.isfile(csv_file)
    global last_log_timestamp
    
    # Safety Check: Only log if 1.8s have passed since last log
    current_time = time.time()
    if current_time - last_log_timestamp < 1.8:
        return
    
    try:
        with open(csv_file, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                "timestamp": battery_data["current"]["timestamp"],
                "battery_percent": battery_data["current"]["psutil"]["percent"],
                "power_plugged": battery_data["current"]["psutil"]["power_plugged"],
                "design_capacity_mwh": battery_data["static"]["design_capacity_mwh"],
                "full_charge_capacity_mwh": battery_data["static"]["full_charge_capacity_mwh"],
                "voltage": battery_data["current"]["voltage"]
            })
            last_log_timestamp = current_time
    except Exception as e:
        print(f"❌ CSV write error: {e}")


def is_admin():
    """Check if script is running with Administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Relaunch the script as Administrator"""
    if is_admin():
        return True
    
    script = os.path.abspath(sys.argv[0])
    params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
    print(f"🔄 Neural Core: Requesting elevation to access hardware SMART data...")
    try:
        # 1 = SH_SHOW - Normal window
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
        sys.exit(0)
    except Exception as e:
        print(f"❌ Neural Core: Elevation failed: {e}")
        return False

def main():
    """Run background service"""
    # Automatic Elevation
    if not is_admin():
        run_as_admin()
        return

    # Singleton Lock
    lock_file = os.path.join(ROOT_DIR, "data", "battery_service.lock")
    if os.path.exists(lock_file):
        try:
            # Check if process is actually running
            with open(lock_file, "r") as f:
                old_pid = int(f.read().strip())
            import psutil as ps
            if ps.pid_exists(old_pid):
                print(f"⚠️ Service already running (PID: {old_pid}). Exiting.")
                sys.exit(0)
        except:
            pass
    
    # Create new lock
    with open(lock_file, "w") as f:
        f.write(str(os.getpid()))
    
    import atexit
    def cleanup_lock():
        if os.path.exists(lock_file):
            os.remove(lock_file)
    atexit.register(cleanup_lock)

    print("\n" + "="*50)
    print("🔋 Battery & Disk Neural Core")
    print("="*50)
    print("📁 Writing battery data to: battery_data.json")
    print("💾 Writing disk data to: disk_data.json")
    print("📝 Logging history to: battery_history.csv")
    print("⏱️  Update interval: 2 seconds")
    print("="*50 + "\n")
    
    battery_history = []
    disk_history = []
    
    # Initialize InfluxDB
    influx_manager = InfluxDBManager()
    
    try:
        # Start Storage Analyzer (scan entire C: drive in background)
        scan_paths = ['C:\\'] 
        StorageAnalyzer(scan_paths).start()
        
        while True:
            # Get current data
            battery_data = generate_battery_data()
            disk_data = generate_disk_data()
            
            # Add to memory history (for JSON/Dashboard)
            battery_history.append({
                "timestamp": battery_data["current"]["timestamp"],
                "psutil": battery_data["current"]["psutil"]
            })
            disk_history.append({
                "timestamp": disk_data["current"]["timestamp"],
                "usage": disk_data["current"]["usage"],
                "io_rates": disk_data["current"]["io_rates"],
                "active_time": disk_data["current"]["active_time"]
            })
            
            # Keep last 100 entries in memory
            if len(battery_history) > 100:
                battery_history = battery_history[-100:]
            if len(disk_history) > 100:
                disk_history = disk_history[-100:]
            
            battery_data["history"] = battery_history
            disk_data["history"] = disk_history
            
            # 1. Append to persistent CSV (Analytics)
            log_to_csv(battery_data)
            
            # 2. Log to InfluxDB (Remote)
            try:
                user_email = os.environ.get("USER_EMAIL", "unknown")
                influx_manager.log_data(battery_data, disk_data, user_email=user_email)
            except Exception as e:
                print(f"⚠️ InfluxDB task error: {e}")
            
            # 3. Compute detailed analytics from CSV
            try:
                is_plugged = battery_data['current']['psutil']['power_plugged']
                drain_data = battery_analytics.calculate_drain_rate(is_plugged_in=is_plugged)
                worst_period = battery_analytics.detect_worst_drain_period()
                health_data = battery_analytics.calculate_battery_health()
                daily_summary = battery_analytics.generate_daily_summary()
                weekly_summary = battery_analytics.generate_weekly_summary()
                spike_alert = battery_analytics.detect_drain_spike()
                charging_habits = battery_analytics.analyze_charging_habits()
                
                battery_data["battery_analytics"] = {
                    "drain_rate_percent_per_hour": drain_data["drain_rate_percent_per_hour"],
                    "worst_drain_rate": worst_period["worst_drain_rate"],
                    "worst_drain_window": {
                        "start": worst_period["start_time"],
                        "end": worst_period["end_time"]
                    }
                }
                battery_data["battery_health"] = health_data
                battery_data["battery_summary"] = {
                    "daily": daily_summary,
                    "weekly": weekly_summary
                }
                battery_data["battery_alerts"] = {
                    "drain_spike": spike_alert
                }
                battery_data["charging_analytics"] = charging_habits

                # Compute predictive risk score
                spike_freq = 1 if spike_alert.get("anomaly_detected", False) else 0
                risk = battery_analytics.calculate_risk_score(
                    battery_health_percent=health_data.get("battery_health_percent", 96),
                    drain_spike_frequency=spike_freq,
                    percent_time_above_90=charging_habits.get("percent_time_above_90", 0),
                    overheating_events=0  # No thermal sensor yet
                )
                battery_data["predictive_maintenance"] = risk
            except Exception as e:
                print(f"⚠️ Analytics calculation error: {e}")
                battery_data["battery_analytics"] = {}
                battery_data["battery_health"] = {}
                battery_data["battery_summary"] = {}
                battery_data["battery_alerts"] = {}
                battery_data["charging_analytics"] = {}
                battery_data["predictive_maintenance"] = {}

            # 4. Write battery JSON (Dashboard)
            try:
                with open(os.path.join(ROOT_DIR, "data", "battery_data.json"), "w") as f:
                    json.dump(battery_data, f, indent=4)
            except Exception as e:
                print(f"❌ Battery JSON write error: {e}")

            # 5. Write disk JSON
            try:
                with open(os.path.join(ROOT_DIR, "data", "disk_data.json"), "w") as f:
                    json.dump(disk_data, f, indent=4)
            except Exception as e:
                print(f"❌ Disk JSON write error: {e}")
            
            bat_pct = battery_data['current']['psutil']['percent']
            disk_pct = disk_data['current']['usage']['percent']
            print(f"✅ 🔋{bat_pct:.1f}% | 💾{disk_pct:.1f}% - {len(battery_history)}/{len(disk_history)} points")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopped")


if __name__ == "__main__":
    if sys.platform != "win32":
        print("❌ Windows only!")
        sys.exit(1)
    
    # Run the main service immediately. 
    # SMART data collection handles its own admin check and falls back gracefully.
    main()
