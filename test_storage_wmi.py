import wmi
try:
    c = wmi.WMI(namespace="root\\Microsoft\\Windows\\Storage")
    disks = c.MSFT_PhysicalDisk()
    for disk in disks:
        print(f"Disk: {disk.FriendlyName}")
        print(f"Health: {disk.HealthStatus}")
        print(f"OperationalStatus: {disk.OperationalStatus}")
except Exception as e:
    print(f"Error: {e}")
