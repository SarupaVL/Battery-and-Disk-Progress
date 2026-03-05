# Main entry point for disk agent
import time
from collector.snapshot import collect_snapshot
from collector.battery import collect_battery_snapshot
from sender.local_dump import dump
from config import POLL_INTERVAL, DISK_LOG_PATH, BATTERY_LOG_PATH

def main():
    while True:
        # Collect and dump disk telemetry
        disk_snap = collect_snapshot()
        dump(disk_snap, DISK_LOG_PATH)
        
        # Collect and dump battery telemetry
        battery_snap = collect_battery_snapshot()
        dump(battery_snap, BATTERY_LOG_PATH)
        
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
