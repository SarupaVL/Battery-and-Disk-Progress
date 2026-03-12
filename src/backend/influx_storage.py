import os
import platform
import datetime
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
                print("⚠️ InfluxDB token not found in .env. Skipping remote storage.")
            if InfluxDBClient3 is None:
                print("⚠️ influxdb-client-3 not installed. Skipping remote storage.")
        else:
            try:
                self.client = InfluxDBClient3(host=self.host, token=self.token, org=self.org)
                print(f"✅ InfluxDB initialized for device: {self.device_id}")
            except Exception as e:
                print(f"❌ InfluxDB initialization failed: {e}")
                self.client = None

    def log_data(self, battery_data, disk_data):
        if not self.client:
            return

        try:
            points = []
            
            # Battery point
            bat_curr = battery_data.get("current", {})
            bat_ps = bat_curr.get("psutil", {})
            if bat_ps:
                p_bat = Point("battery_telemetry") \
                    .tag("device_id", self.device_id) \
                    .field("percent", float(bat_ps.get("percent", 0))) \
                    .field("secsleft", int(bat_ps.get("secsleft", 0))) \
                    .field("power_plugged", bool(bat_ps.get("power_plugged", False))) \
                    .field("voltage", float(bat_curr.get("voltage", 0))) \
                    .field("temperature", float(bat_curr.get("temperature", 0))) \
                    .field("power_draw", float(bat_curr.get("power_draw", 0)))
                points.append(p_bat)

            # Disk point
            disk_curr = disk_data.get("current", {})
            disk_usage = disk_curr.get("usage", {})
            if disk_usage:
                p_disk = Point("disk_telemetry") \
                    .tag("device_id", self.device_id) \
                    .tag("model", disk_curr.get("details", {}).get("model", "unknown")) \
                    .field("used_percent", float(disk_usage.get("percent", 0))) \
                    .field("used_bytes", int(disk_usage.get("used_bytes", 0))) \
                    .field("free_bytes", int(disk_usage.get("free_bytes", 0))) \
                    .field("active_time", int(disk_curr.get("active_time", 0))) \
                    .field("failure_probability", float(disk_curr.get("failure_probability", 0)))
                points.append(p_disk)

            if points:
                # influxdb-client-3 write accepts a list of Point objects
                self.client.write(database=self.database, record=points)
        except Exception as e:
            print(f"❌ InfluxDB write error: {e}")

if __name__ == "__main__":
    # Test script
    manager = InfluxDBManager()
    if manager.client:
        test_bat = {"current": {"psutil": {"percent": 99, "secsleft": 3600, "power_plugged": True}, "voltage": 12.0, "temperature": 30, "power_draw": 10.0}}
        test_disk = {"current": {"usage": {"percent": 10, "used_bytes": 100, "free_bytes": 900}, "active_time": 5, "failure_probability": 0.01, "details": {"model": "Test Model"}}}
        manager.log_data(test_bat, test_disk)
        print("Test data sent (if client is active). Check InfluxDB.")
