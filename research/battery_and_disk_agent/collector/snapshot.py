# Snapshot collection module
from datetime import datetime, timezone
from collector.disk_usage import collect_disk_usage
from collector.disk_io import collect_disk_io
from collector.process_io import collect_process_write_deltas
from config import DISK_MOUNT, DEVICE_ID

def collect_snapshot():
    snapshot = {
        "device_id": DEVICE_ID,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "disk_usage": collect_disk_usage(DISK_MOUNT),
        "disk_io": collect_disk_io(),
        "process_writes": collect_process_write_deltas()
    }
    return snapshot
