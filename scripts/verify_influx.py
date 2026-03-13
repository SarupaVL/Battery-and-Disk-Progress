import os
import sys
import datetime
from dotenv import load_dotenv

# Add src to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT_DIR, "src", "backend"))

from influx_storage import InfluxDBManager

def test_influx_integration():
    print("[TEST] Testing InfluxDB Integration...")
    
    manager = InfluxDBManager()
    if not manager.client:
        print("❌ InfluxDB client not initialized. Check .env and influxdb3-python installation.")
        return

    user_email = os.environ.get("USER_EMAIL", "test@example.com")
    print(f"[FETCH] Querying data for: {user_email}")
    
    # 1. Test Latest Stats
    bat, disk = manager.get_latest_stats(user_email)
    print("\n--- Latest Stats ---")
    print(f"Battery: {bat if bat else 'No data'}")
    print(f"Disk: {disk if disk else 'No data'}")
    
    # 2. Test History Query (last 1 hour)
    start = datetime.datetime.now() - datetime.timedelta(hours=1)
    history = manager.query_battery_history(user_email, start_time=start)
    print(f"\n--- History (Last 1h) ---")
    print(f"Count: {len(history)} points")
    if history:
        print(f"First point: {history[0]}")

if __name__ == "__main__":
    load_dotenv(os.path.join(ROOT_DIR, ".env"))
    test_influx_integration()
