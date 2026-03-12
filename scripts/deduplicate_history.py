#!/usr/bin/env python3
"""Refined cleanup script to remove near-duplicate timestamps from battery_history.csv"""

import csv
import os
import sys
from datetime import datetime

# Ensure console can handle output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def deduplicate():
    input_file = "battery_history.csv"
    output_file = "battery_history_clean.csv"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    seen_seconds = set()
    rows_written = 0
    duplicates_removed = 0
    
    try:
        with open(input_file, "r", encoding='utf-8') as f_in, open(output_file, "w", newline="", encoding='utf-8') as f_out:
            reader = csv.DictReader(f_in)
            writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
            writer.writeheader()
            
            for row in reader:
                ts_str = row['timestamp']
                try:
                    # Parse timestamp and round to nearest second
                    dt = datetime.fromisoformat(ts_str)
                    sec_key = dt.strftime("%Y-%m-%dT%H:%M:%S")
                except:
                    sec_key = ts_str # Fallback to exact string if parsing fails
                
                # If we've already logged something in this same second, it's likely a duplicate from a parallel process
                if sec_key in seen_seconds:
                    duplicates_removed += 1
                    continue
                
                seen_seconds.add(sec_key)
                writer.writerow(row)
                rows_written += 1
        
        # Replace original with cleaned version
        if os.path.exists(input_file):
            os.remove(input_file)
        os.rename(output_file, input_file)
        
        print(f"Successfully cleaned {input_file}")
        print(f"   - Rows written: {rows_written}")
        print(f"   - Near-duplicates removed (same second): {duplicates_removed}")
        
    except Exception as e:
        print(f"Error during deduplication: {e}")
        if os.path.exists(output_file):
            os.remove(output_file)

if __name__ == "__main__":
    deduplicate()
