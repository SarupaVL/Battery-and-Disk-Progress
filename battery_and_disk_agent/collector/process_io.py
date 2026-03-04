# Process I/O collection module
import psutil

_prev_proc_writes = {}

def collect_process_write_deltas():
    deltas = []

    for proc in psutil.process_iter(['pid', 'name', 'io_counters']):
        try:
            io = proc.info['io_counters']
            if io is None:
                continue

            pid = proc.info['pid']
            name = proc.info['name']
            current = io.write_bytes

            prev = _prev_proc_writes.get(pid, current)
            delta = current - prev

            _prev_proc_writes[pid] = current

            if delta > 0:
                deltas.append({
                    "pid": pid,
                    "process_name": name,
                    "write_bytes_delta": delta
                })

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return deltas
