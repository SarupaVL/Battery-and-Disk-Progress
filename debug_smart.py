import wmi
import ctypes
import os
import json

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

print(f"Is Elevated: {is_admin()}")

try:
    c = wmi.WMI(namespace="root\\wmi")
    smart_data = c.MSStorageDriver_ATAPISmartData()
    if smart_data:
        raw = bytes(smart_data[0].VendorSpecific)
        print(f"VendorSpecific Length: {len(raw)}")
        
        # Scan for 43 C (or 316 K)
        # 43 C is 0x2B
        # 316 K is 0x013C
        
        found_target = []
        for i in range(len(raw)):
            if raw[i] == 43:
                found_target.append(f"Byte {i}: 43 (0x2B)")
            if i + 1 < len(raw):
                val = int.from_bytes(raw[i:i+2], 'little')
                if val == 316:
                    found_target.append(f"Bytes {i}-{i+1}: 316 K (43 C)")
        
        if found_target:
            print("Possible offsets for 43 C:")
            for m in found_target: print(m)
        else:
            print("Did not find 43 or 316 in raw buffer.")
            
        print(f"Bytes 0-127 (Hex): {raw[:128].hex()}")
    else:
        print("No SMART data found.")
except Exception as e:
    print(f"Error: {e}")

try:
    # Try a more basic Get-PhysicalDisk to see what's available
    import subprocess
    cmd = 'powershell -Command "Get-PhysicalDisk | Select-Object FriendlyName, HealthStatus, OperationalStatus | ConvertTo-Json"'
    out = subprocess.check_output(cmd, shell=True).decode('utf-8')
    print("PhysicalDisk info:")
    print(out)
except Exception as e:
    print(f"PS Error: {e}")
