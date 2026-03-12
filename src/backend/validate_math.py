import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analytics")))

from src.backend.battery_service import generate_battery_data, generate_disk_data

def validate_ranges():
    print("🚩 Running Calculation Validation...")
    
    bat_data = generate_battery_data()
    disk_data = generate_disk_data()
    
    # 1. Voltage Check (9V - 14V)
    v = bat_data['current']['voltage']
    print(f"Voltage: {v}V - {'✅ OK' if 9 <= v <= 14 else '❌ FAIL'}")
    
    # 2. Power Draw Check (5W - 65W)
    p = bat_data['current']['power_draw']
    print(f"Power Draw: {p}W - {'✅ OK' if 5 <= p <= 65 else '❌ FAIL'}")
    
    # 3. Health Normalization (0-100)
    h = bat_data['analytics']['battery_health_percent']
    print(f"Battery Health: {h}% - {'✅ OK' if 0 <= h <= 100 else '❌ FAIL'}")
    
    # 4. Disk Failure Prob (0-1)
    f = disk_data['current']['failure_probability']
    print(f"Failure Prob: {f} - {'✅ OK' if 0 <= f <= 1 else '❌ FAIL'}")
    
    # 5. Prediction Label
    label = disk_data['analytics']['neural_health_label']
    print(f"Health Label: {label} - {'✅ OK' if label in ['SAFE', 'WARNING', 'CRITICAL'] else '❌ FAIL'}")

if __name__ == "__main__":
    validate_ranges()
