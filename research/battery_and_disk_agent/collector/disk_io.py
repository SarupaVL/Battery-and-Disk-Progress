# Disk I/O collection module
import psutil
import time

_prev = None
_prev_time = None

def collect_disk_io():
    global _prev, _prev_time

    now = time.time()
    counters = psutil.disk_io_counters()

    if _prev is None:
        _prev = counters
        _prev_time = now
        return None

    dt = now - _prev_time

    data = {
        "read_bytes_per_sec": (counters.read_bytes - _prev.read_bytes) / dt,
        "write_bytes_per_sec": (counters.write_bytes - _prev.write_bytes) / dt,
        "read_ops_per_sec": (counters.read_count - _prev.read_count) / dt,
        "write_ops_per_sec": (counters.write_count - _prev.write_count) / dt,
    }

    _prev = counters
    _prev_time = now
    return data
