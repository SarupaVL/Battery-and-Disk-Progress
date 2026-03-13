import os
import platform
import datetime
import json
try:
    from influxdb_client_3 import InfluxDBClient3, Point
except ImportError:
    # Fallback for local development if package is not yet fully picked up by IDE
    InfluxDBClient3 = None
    Point = None

from dotenv import load_dotenv

# Load .env relative to this file's root
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

class InfluxDBManager:
    def __init__(self):
        self.token = os.environ.get("INFLUXDB_TOKEN")
        self.org = os.environ.get("INFLUXDB_ORG", "battery-disk-analytics")
        self.host = os.environ.get("INFLUXDB_HOST", "https://us-east-1-1.aws.cloud2.influxdata.com")
        self.database = os.environ.get("INFLUXDB_DATABASE", "time_db")
        self.device_id = platform.node()
        
        self.client = None
        if not self.token or InfluxDBClient3 is None:
            if not self.token:
                print("[WARNING] InfluxDB token not found in .env. Skipping remote storage.")
            if InfluxDBClient3 is None:
                print("[WARNING] influxdb-client-3 not installed. Skipping remote storage.")
        else:
            try:
                self.client = InfluxDBClient3(host=self.host, token=self.token, org=self.org)
                print(f"[OK] InfluxDB initialized for device: {self.device_id}")
            except Exception as e:
                print(f"[ERROR] InfluxDB initialization failed: {e}")
                self.client = None

    def log_data(self, battery_data, disk_data, user_email="unknown"):
        if not self.client:
            return

        try:
            points = []
            
            # Battery point
            bat_curr = battery_data.get("current", {})
            bat_ps = bat_curr.get("psutil", {})
            bat_static = battery_data.get("static", {})
            bat_analytics = battery_data.get("analytics", {})
            bat_health = battery_data.get("battery_health", {})
            bat_risk = battery_data.get("predictive_maintenance", {})
            bat_charging = battery_data.get("charging_analytics", {})
            
            if bat_ps:
                p_bat = Point("battery_telemetry") \
                    .tag("device_id", self.device_id) \
                    .tag("user_email", user_email) \
                    .field("percent", float(bat_ps.get("percent", 0) or 0)) \
                    .field("secsleft", int(bat_ps.get("secsleft", 0) or 0)) \
                    .field("power_plugged", bool(bat_ps.get("power_plugged", False))) \
                    .field("voltage", float(bat_curr.get("voltage", 0) or 0)) \
                    .field("temperature", float(bat_curr.get("temperature", 0) or 0)) \
                    .field("power_draw", float(bat_curr.get("power_draw", 0) or 0)) \
                    .field("design_capacity", float(bat_static.get("design_capacity_mwh", 0) or 0)) \
                    .field("full_charge_capacity", float(bat_static.get("full_charge_capacity_mwh", 0) or 0)) \
                    .field("cycle_count", int(bat_static.get("cycle_count", 0) or 0)) \
                    .field("health_percent", float(bat_analytics.get("battery_health_percent", 100) or 100)) \
                    .field("total_sessions", int(bat_analytics.get("total_sessions", 0) or 0)) \
                    .field("risk_score", float(bat_risk.get("battery_risk_score", 0) or 0)) \
                    .field("drain_rate", float(battery_data.get("battery_analytics", {}).get("drain_rate_percent_per_hour", 0) or 0)) \
                    .field("percent_above_90", float(bat_charging.get("percent_time_above_90", 0) or 0)) \
                    .field("daily_avg_drain", float(battery_data.get("battery_summary", {}).get("daily", {}).get("average_drain_rate", 0) or 0)) \
                    .field("max_drain_spike", float(battery_data.get("battery_summary", {}).get("daily", {}).get("max_drain_spike", 0) or 0)) \
                    .field("worst_drain_rate", float(battery_data.get("battery_analytics", {}).get("worst_drain_rate", 0) or 0)) \
                    .field("worst_drain_start", str(battery_data.get("battery_analytics", {}).get("worst_drain_window", {}).get("start", ""))) \
                    .field("worst_drain_end", str(battery_data.get("battery_analytics", {}).get("worst_drain_window", {}).get("end", ""))) \
                    .field("time_charging", int(bat_charging.get("time_charging_minutes", 0) or 0)) \
                    .field("time_above_90", int(bat_charging.get("time_above_90_minutes", 0) or 0))
                points.append(p_bat)

            # Disk point
            disk_curr = disk_data.get("current", {}) or {}
            disk_usage = disk_curr.get("usage", {}) or {}
            disk_io = disk_curr.get("io_rates", {}) or {}
            disk_hw = disk_curr.get("hardware_health", {}) or {}
            disk_analytics = disk_data.get("analytics", {}) or {}
            disk_procs = disk_curr.get("top_processes", []) or []
            eff_stats = disk_analytics.get("storage_efficiency", {}) or {}
            
            if disk_usage:
                p_disk = Point("disk_telemetry") \
                    .tag("device_id", self.device_id) \
                    .tag("user_email", user_email) \
                    .tag("model", str(disk_curr.get("details", {}).get("model", "unknown") or "unknown")) \
                    .tag("interface", str(disk_curr.get("details", {}).get("interface", "unknown") or "unknown")) \
                    .field("total_bytes", int(disk_usage.get("total_bytes", 0) or 0)) \
                    .field("used_bytes", int(disk_usage.get("used_bytes", 0) or 0)) \
                    .field("free_bytes", int(disk_usage.get("free_bytes", 0) or 0)) \
                    .field("used_percent", float(disk_usage.get("percent", 0) or 0)) \
                    .field("read_bytes_sec", float(disk_io.get("read_bytes_per_sec", 0) or 0)) \
                    .field("write_bytes_sec", float(disk_io.get("write_bytes_per_sec", 0) or 0)) \
                    .field("read_ops_sec", float(disk_io.get("read_ops_per_sec", 0) or 0)) \
                    .field("write_ops_sec", float(disk_io.get("write_ops_per_sec", 0) or 0)) \
                    .field("temp_c", float(disk_hw.get("temperature_c", 0) or 0)) \
                    .field("power_on_hours", int(disk_hw.get("power_on_hours", 0) or 0)) \
                    .field("power_on_count", int(disk_hw.get("power_on_count", 0) or 0)) \
                    .field("total_host_reads_gb", float(disk_hw.get("total_host_reads_gb", 0) or 0)) \
                    .field("total_host_writes_gb", float(disk_hw.get("total_host_writes_gb", 0) or 0)) \
                    .field("active_time", int(disk_curr.get("active_time", 0) or 0)) \
                    .field("failure_probability", float(disk_curr.get("failure_probability", 0) or 0)) \
                    .field("logical_bytes", int(eff_stats.get("logical_bytes", 0) or 0)) \
                    .field("physical_bytes", int(eff_stats.get("physical_bytes", 0) or 0)) \
                    .field("files_scanned", int(eff_stats.get("files_scanned", 0) or 0)) \
                    .field("storage_status", str(eff_stats.get("status", "unknown") or "unknown")) \
                    .field("serial", str(disk_curr.get("details", {}).get("serial", "unknown") or "unknown")) \
                    .field("top_processes_json", json.dumps(disk_procs))
                points.append(p_disk)

            if points:
                # influxdb-client-3 write accepts a list of Point objects
                self.client.write(database=self.database, record=points)
        except Exception as e:
            print(f"[ERROR] InfluxDB write error: {e}")

    def query_battery_history(self, user_email, start_time=None, end_time=None):
        """Query historical battery data from InfluxDB"""
        if not self.client:
            return []

        try:
            # SQL query for InfluxDB v3
            query = f"SELECT * FROM battery_telemetry WHERE user_email = '{user_email}'"
            
            if start_time:
                # Convert to ISO format with Z for InfluxDB SQL
                ts_str = start_time.isoformat() if isinstance(start_time, datetime.datetime) else start_time
                if 'Z' not in str(ts_str): ts_str = f"{ts_str}Z"
                query += f" AND time >= '{ts_str}'"
            
            if end_time:
                ts_str = end_time.isoformat() if isinstance(end_time, datetime.datetime) else end_time
                if 'Z' not in str(ts_str): ts_str = f"{ts_str}Z"
                query += f" AND time <= '{ts_str}'"
            
            query += " ORDER BY time ASC"
            
            table = self.client.query(query=query, database=self.database, language='sql')
            df = table.to_pandas()
            if df.empty:
                return []
            
            # Replace NaNs with None for JSON compatibility
            df = df.where(df.notnull(), None)
                
            results = []
            for _, row in df.iterrows():
                entry = {
                    "timestamp": row['time'].isoformat() if hasattr(row['time'], 'isoformat') else str(row['time']),
                    "percent": float(row.get('percent', 0)) if row.get('percent') is not None else 0,
                    "power_plugged": bool(row.get('power_plugged', False)),
                    "voltage": float(row.get('voltage', 0)) if row.get('voltage') is not None else 0,
                    "temperature": float(row.get('temperature', 0)) if row.get('temperature') is not None else 0,
                    "power_draw": float(row.get('power_draw', 0)) if row.get('power_draw') is not None else 0,
                    "drain_rate": float(row.get('drain_rate', 0)) if row.get('drain_rate') is not None else 0,
                    "risk_score": float(row.get('risk_score', 0)) if row.get('risk_score') is not None else 0,
                    "design_capacity": float(row.get('design_capacity', 0)) if row.get('design_capacity') is not None else 0,
                    "full_charge_capacity": float(row.get('full_charge_capacity', 0)) if row.get('full_charge_capacity') is not None else 0,
                }
                results.append(entry)
            return results
        except Exception as e:
            print(f"[ERROR] InfluxDB query error: {e}")
            return []

    def query_disk_history(self, user_email, start_time=None, end_time=None):
        """Query historical disk data from InfluxDB"""
        if not self.client:
            return []

        try:
            query = f"SELECT * FROM disk_telemetry WHERE user_email = '{user_email}'"
            
            if start_time:
                ts_str = start_time.isoformat() if isinstance(start_time, datetime.datetime) else start_time
                if 'Z' not in str(ts_str): ts_str = f"{ts_str}Z"
                query += f" AND time >= '{ts_str}'"
            
            if end_time:
                ts_str = end_time.isoformat() if isinstance(end_time, datetime.datetime) else end_time
                if 'Z' not in str(ts_str): ts_str = f"{ts_str}Z"
                query += f" AND time <= '{ts_str}'"
            
            query += " ORDER BY time ASC"
            
            table = self.client.query(query=query, database=self.database, language='sql')
            df = table.to_pandas()
            if df.empty:
                return []
                
            # Replace NaNs with None for JSON compatibility
            df = df.where(df.notnull(), None)

            results = []
            for _, row in df.iterrows():
                results.append({
                    "timestamp": row['time'].isoformat() if hasattr(row['time'], 'isoformat') else str(row['time']),
                    "active_time": float(row.get('active_time', 0)) if row.get('active_time') is not None else 0
                })
            return results
        except Exception as e:
            print(f"[ERROR] InfluxDB disk query error: {e}")
            return []

    def get_latest_stats(self, user_email):
        """Fetch the most recent telemetry for both battery and disk"""
        if not self.client:
            return None, None

        try:
            # Query latest battery
            q_bat = f"SELECT * FROM battery_telemetry WHERE user_email = '{user_email}' ORDER BY time DESC LIMIT 1"
            t_bat = self.client.query(query=q_bat, database=self.database, language='sql').to_pandas()
            
            # Replace NaNs with None
            t_bat = t_bat.where(t_bat.notnull(), None)

            # Query latest disk
            q_disk = f"SELECT * FROM disk_telemetry WHERE user_email = '{user_email}' ORDER BY time DESC LIMIT 1"
            t_disk = self.client.query(query=q_disk, database=self.database, language='sql').to_pandas()
            
            # Replace NaNs with None
            t_disk = t_disk.where(t_disk.notnull(), None)

            bat_res = t_bat.to_dict('records')[0] if not t_bat.empty else None
            disk_res = t_disk.to_dict('records')[0] if not t_disk.empty else None
            
            # Format time if present
            if bat_res and 'time' in bat_res: bat_res['timestamp'] = bat_res['time'].isoformat()
            if disk_res and 'time' in disk_res: disk_res['timestamp'] = disk_res['time'].isoformat()
            
            return bat_res, disk_res
        except Exception as e:
            print(f"[ERROR] InfluxDB latest stats error: {e}")
            return None, None

if __name__ == "__main__":
    # Test script
    manager = InfluxDBManager()
    if manager.client:
        test_bat = {"current": {"psutil": {"percent": 99, "secsleft": 3600, "power_plugged": True}, "voltage": 12.0, "temperature": 30, "power_draw": 10.0}}
        test_disk = {"current": {"usage": {"percent": 10, "used_bytes": 100, "free_bytes": 900}, "active_time": 5, "failure_probability": 0.01, "details": {"model": "Test Model"}}}
        manager.log_data(test_bat, test_disk)
        print("Test data sent (if client is active). Check InfluxDB.")
