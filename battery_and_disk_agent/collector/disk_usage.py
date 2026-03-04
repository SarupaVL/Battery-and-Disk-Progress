# Disk usage collection module
import psutil

def collect_disk_usage(mount):
    usage = psutil.disk_usage(mount)
    return {
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free
    }
