import csv
import os
import math
from datetime import datetime, timedelta
from collections import defaultdict

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_CSV = os.path.join(ROOT_DIR, "data", "battery_history.csv")

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import joblib
    import numpy as np
    import warnings
    # Filter out UserWarnings from joblib, often related to sklearn version mismatches
    # when loading RandomForest models.
    warnings.filterwarnings("ignore", category=UserWarning, module='joblib')
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

def get_discharging_history(csv_file, minutes):
    """Read CSV and return rows within the last X minutes where power_plugged is False"""
    if not os.path.exists(csv_file):
        return []

    now = datetime.now()
    cutoff = now - timedelta(minutes=minutes)
    history = []

    try:
        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ts = datetime.fromisoformat(row['timestamp'])
                    if ts > cutoff and row['power_plugged'].lower() == 'false':
                        history.append({
                            'timestamp': ts,
                            'battery_percent': float(row['battery_percent'])
                        })
                except (ValueError, KeyError):
                    continue
    except Exception as e:
        print(f"ΓÜá∩╕Å Analytics read error: {e}")
        return []

    return history

def calculate_drain_rate(csv_file=DEFAULT_CSV, is_plugged_in=False):
    """Compute battery drain rate as median of slopes to ignore reporting jitter and spikes"""
    if is_plugged_in:
        return {"drain_rate_percent_per_hour": 0.0}

    if not os.path.exists(csv_file):
        return {"drain_rate_percent_per_hour": 0.0}

    # CSV fallback check just in case
    try:
        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            last_row = None
            for last_row in reader:
                pass
            if last_row and last_row['power_plugged'].lower() == 'true':
                return {"drain_rate_percent_per_hour": 0.0}
    except:
        pass

    history = get_discharging_history(csv_file, 30)
    
    if len(history) < 10:
        return {"drain_rate_percent_per_hour": 0.0}

    slopes = []
    
    # Calculate slopes over various windows (at least 2 minutes apart to reduce noise)
    for i in range(0, len(history), 5):
        for j in range(i + 10, len(history), 10):
            start = history[i]
            end = history[j]
            
            time_diff_hours = (end['timestamp'] - start['timestamp']).total_seconds() / 3600.0
            
            # Windows between 2 and 15 minutes are best for "instant" rate
            if 0.033 < time_diff_hours < 0.25:
                percent_diff = start['battery_percent'] - end['battery_percent']
                slopes.append(percent_diff / time_diff_hours)
    
    if not slopes:
        total_span = (history[-1]['timestamp'] - history[0]['timestamp']).total_seconds() / 3600.0
        if total_span > 0.083:
            drain = (history[0]['battery_percent'] - history[-1]['battery_percent']) / total_span
            return {"drain_rate_percent_per_hour": round(min(60.0, max(0.0, drain)), 2)}
        return {"drain_rate_percent_per_hour": 0.0}

    # Use median to ignore outliers 
    slopes.sort()
    median_drain = slopes[len(slopes) // 2]
    
    # Sanity cap: anything > 60%/hr is almost certainly a reporting error or extreme spike
    final_rate = min(60.0, max(0.0, median_drain))
    
    return {
        "drain_rate_percent_per_hour": round(float(final_rate), 2)
    }

def detect_worst_drain_period(csv_file=DEFAULT_CSV):
    """Scan the last 2 hours of history and find the time window with the highest drain slope (O(N) sliding window)"""
    history = get_discharging_history(csv_file, 120)
    
    if len(history) < 10:  # Need a decent sample size
        return {
            "worst_drain_rate": 0.0,
            "start_time": "N/A",
            "end_time": "N/A"
        }

    worst_rate = 0.0
    worst_window = {"start": "N/A", "end": "N/A"}
    
    # Sliding window: find max drop over roughly 5-minute intervals
    # O(N) approach: for each end point, find a start point at least 5 mins prior
    left = 0
    for right in range(len(history)):
        # Maintain a window of at least 2 minutes but not more than 10 minutes for "period" analysis
        while left < right:
            duration_hours = (history[right]['timestamp'] - history[left]['timestamp']).total_seconds() / 3600.0
            
            # If window is too large (>10 mins), move left forward
            if duration_hours > (10.0 / 60.0):
                left += 1
                continue
            
            # If window is large enough to be meaningful (>2 mins)
            if duration_hours >= (2.0 / 60.0):
                pct_drop = history[left]['battery_percent'] - history[right]['battery_percent']
                rate = pct_drop / duration_hours
                
                if rate > worst_rate:
                    worst_rate = rate
                    worst_window = {
                        "start": history[left]['timestamp'].isoformat(),
                        "end": history[right]['timestamp'].isoformat()
                    }
                # We found a valid window for this 'right' point, but smaller windows might have higher rates
                # However, to keep it O(N), we don't nested loop. 
                # Actually, the 'while' loop makes it O(2N) total as left only moves forward.
                break
            else:
                # Window too small, stop moving left for this right point
                break

    return {
        "worst_drain_rate": round(worst_rate, 2),
        "start_time": worst_window["start"],
        "end_time": worst_window["end"]
    }


def calculate_battery_health(csv_file=DEFAULT_CSV):
    """Calculate battery health from the most recent CSV row's capacity values"""
    if not os.path.exists(csv_file):
        return {"battery_health_percent": 0.0, "design_capacity_mwh": 0, "full_charge_capacity_mwh": 0}

    design = 0
    full_charge = 0

    try:
        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                design = float(row.get("design_capacity_mwh", 0))
                full_charge = float(row.get("full_charge_capacity_mwh", 0))
    except Exception as e:
        print(f"ΓÜá∩╕Å Health read error: {e}")

    if design <= 0:
        return {"battery_health_percent": 0.0, "design_capacity_mwh": design, "full_charge_capacity_mwh": full_charge}

    health = round((full_charge / design) * 100, 2)
    health = max(0.0, min(100.0, health)) # Clamp to 100%

    return {
        "battery_health_percent": health,
        "design_capacity_mwh": design,
        "full_charge_capacity_mwh": full_charge
    }


def _read_all_discharging_rows(csv_file, since):
    """Read all discharging rows from CSV since a given datetime"""
    if not os.path.exists(csv_file):
        return []

    rows = []
    try:
        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ts = datetime.fromisoformat(row['timestamp'])
                    if ts >= since and row['power_plugged'].lower() == 'false':
                        rows.append({
                            'timestamp': ts,
                            'battery_percent': float(row['battery_percent'])
                        })
                except (ValueError, KeyError):
                    continue
    except Exception:
        pass
    return rows


def _drain_rate_for_segment(rows):
    """Calculate drain rate (%/hr) for a sorted list of rows"""
    if len(rows) < 2:
        return 0.0
    time_diff = (rows[-1]['timestamp'] - rows[0]['timestamp']).total_seconds() / 3600.0
    if time_diff <= 0:
        return 0.0
    return max(0.0, (rows[0]['battery_percent'] - rows[-1]['battery_percent']) / time_diff)


def generate_daily_summary(csv_file=DEFAULT_CSV):
    """Generate a summary of the last 24 hours of battery usage"""
    now = datetime.now()
    since = now - timedelta(hours=24)
    rows = _read_all_discharging_rows(csv_file, since)

    if len(rows) < 2:
        return {"average_drain_rate": 0.0, "max_drain_spike": 0.0, "total_samples": len(rows)}

    # --- Average drain rate over the full window ---
    avg_drain = _drain_rate_for_segment(rows)

    # --- Max drain spike: highest rate in any 5-minute window ---
    max_spike = 0.0
    window_seconds = 300  # 5 minutes
    i = 0
    for j in range(1, len(rows)):
        while (rows[j]['timestamp'] - rows[i]['timestamp']).total_seconds() > window_seconds:
            i += 1
        if j > i:
            segment = rows[i:j + 1]
            rate = _drain_rate_for_segment(segment)
            if rate > max_spike:
                max_spike = rate

    return {
        "average_drain_rate": round(avg_drain, 2),
        "max_drain_spike": round(max_spike, 2),
        "total_samples": len(rows)
    }


def generate_weekly_summary(csv_file=DEFAULT_CSV):
    """Generate a summary of the last 7 days of battery usage"""
    now = datetime.now()
    since = now - timedelta(days=7)
    rows = _read_all_discharging_rows(csv_file, since)

    if len(rows) < 2:
        return {"avg_daily_drain_rate": 0.0, "highest_drain_day": "N/A", "lowest_drain_day": "N/A"}

    if HAS_PANDAS:
        return _weekly_summary_pandas(rows)
    else:
        return _weekly_summary_pure(rows)


def _weekly_summary_pandas(rows):
    """Efficient weekly summary using pandas"""
    df = pd.DataFrame(rows)
    df['date'] = df['timestamp'].dt.date

    daily_rates = {}
    for date, group in df.groupby('date'):
        group = group.sort_values('timestamp')
        if len(group) >= 2:
            time_h = (group['timestamp'].iloc[-1] - group['timestamp'].iloc[0]).total_seconds() / 3600.0
            if time_h > 0:
                rate = max(0.0, (group['battery_percent'].iloc[0] - group['battery_percent'].iloc[-1]) / time_h)
                daily_rates[str(date)] = round(rate, 2)

    if not daily_rates:
        return {"avg_daily_drain_rate": 0.0, "highest_drain_day": "N/A", "lowest_drain_day": "N/A"}

    avg_rate = round(sum(daily_rates.values()) / len(daily_rates), 2)
    highest = max(daily_rates, key=daily_rates.get)
    lowest = min(daily_rates, key=daily_rates.get)

    return {"avg_daily_drain_rate": avg_rate, "highest_drain_day": highest, "lowest_drain_day": lowest}


def _weekly_summary_pure(rows):
    """Pure-Python weekly summary fallback"""
    by_date = defaultdict(list)
    for r in rows:
        by_date[r['timestamp'].date()].append(r)

    daily_rates = {}
    for date, day_rows in by_date.items():
        day_rows.sort(key=lambda x: x['timestamp'])
        if len(day_rows) >= 2:
            time_h = (day_rows[-1]['timestamp'] - day_rows[0]['timestamp']).total_seconds() / 3600.0
            if time_h > 0:
                rate = max(0.0, (day_rows[0]['battery_percent'] - day_rows[-1]['battery_percent']) / time_h)
                daily_rates[str(date)] = round(rate, 2)

    if not daily_rates:
        return {"avg_daily_drain_rate": 0.0, "highest_drain_day": "N/A", "lowest_drain_day": "N/A"}

    avg_rate = round(sum(daily_rates.values()) / len(daily_rates), 2)
    highest = max(daily_rates, key=daily_rates.get)
    lowest = min(daily_rates, key=daily_rates.get)

    return {"avg_daily_drain_rate": avg_rate, "highest_drain_day": highest, "lowest_drain_day": lowest}


def detect_drain_spike(csv_file=DEFAULT_CSV):
    """Detect anomalous drain spikes using mean + 3*std deviation threshold over last 3 hours"""
    rows = _read_all_discharging_rows(csv_file, datetime.now() - timedelta(hours=3))

    if len(rows) < 10:
        return {"anomaly_detected": False, "drain_rate": 0.0, "threshold": 0.0}

    # Compute drain rates over sliding 5-minute windows
    drain_rates = []
    window_seconds = 300
    i = 0
    for j in range(1, len(rows)):
        while (rows[j]['timestamp'] - rows[i]['timestamp']).total_seconds() > window_seconds:
            i += 1
        if j > i:
            rate = _drain_rate_for_segment(rows[i:j + 1])
            if rate > 0:
                drain_rates.append(rate)

    if len(drain_rates) < 3:
        return {"anomaly_detected": False, "drain_rate": 0.0, "threshold": 0.0}

    # Mean and standard deviation
    mean = sum(drain_rates) / len(drain_rates)
    variance = sum((r - mean) ** 2 for r in drain_rates) / len(drain_rates)
    std_dev = math.sqrt(variance)

    threshold = round(mean + 3 * std_dev, 2)
    current_rate = round(drain_rates[-1], 2)

    return {
        "anomaly_detected": current_rate > threshold,
        "drain_rate": current_rate,
        "threshold": threshold
    }


def analyze_charging_habits(csv_file=DEFAULT_CSV):
    """Analyze charging habits: total charging time, time above 90%, percent time above 90"""
    if not os.path.exists(csv_file):
        return {"time_charging_minutes": 0.0, "time_above_90_minutes": 0.0, "percent_time_above_90": 0.0}

    rows = []
    try:
        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    rows.append({
                        "timestamp": datetime.fromisoformat(row["timestamp"]),
                        "battery_percent": float(row["battery_percent"]),
                        "power_plugged": row["power_plugged"].lower() == "true"
                    })
                except (ValueError, KeyError):
                    continue
    except Exception:
        return {"time_charging_minutes": 0.0, "time_above_90_minutes": 0.0, "percent_time_above_90": 0.0}

    if len(rows) < 2:
        return {"time_charging_minutes": 0.0, "time_above_90_minutes": 0.0, "percent_time_above_90": 0.0}

    total_charging_seconds = 0.0
    total_above_90_seconds = 0.0
    total_tracked_seconds = 0.0

    for i in range(1, len(rows)):
        dt = (rows[i]["timestamp"] - rows[i - 1]["timestamp"]).total_seconds()

        # Skip gaps larger than 30 seconds (service was likely stopped)
        if dt <= 0 or dt > 30:
            continue

        total_tracked_seconds += dt

        if rows[i - 1]["power_plugged"]:
            total_charging_seconds += dt

        if rows[i - 1]["battery_percent"] >= 90:
            total_above_90_seconds += dt

    charging_min = round(total_charging_seconds / 60, 2)
    above_90_min = round(total_above_90_seconds / 60, 2)
    pct_above_90 = round((total_above_90_seconds / total_tracked_seconds) * 100, 2) if total_tracked_seconds > 0 else 0.0

    return {
        "time_charging_minutes": charging_min,
        "time_above_90_minutes": above_90_min,
        "percent_time_above_90": pct_above_90
    }


def calculate_risk_score(battery_health_percent=96.0,
                         drain_spike_frequency=0,
                         percent_time_above_90=0.0,
                         overheating_events=0,
                         current_voltage=11.5,
                         current_temp=35.0,
                         current=2.0,
                         cycle_count=100,
                         time_sec=3600):
    """
    Compute a predictive battery risk score from 0-100.
    
    If the trained Random Forest model is available, it predicts the
    remaining capacity (health score) and overrides the default heuristic.
    """
    ml_health_score = None
    
    if ML_AVAILABLE:
        try:
            model_path = os.path.join(ROOT_DIR, 'models', 'battery_rf_model.joblib')
            if os.path.exists(model_path):
                # Load the model
                model = joblib.load(model_path)
                
                # Model expects: cycle, avg_voltage, avg_current, avg_temperature, discharge_time_sec
                features = np.array([[cycle_count, current_voltage, current, current_temp, time_sec]])
                
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    ml_health_score = float(model.predict(features)[0])
                
                # Cap the prediction
                ml_health_score = max(0.0, min(100.0, ml_health_score))
        except Exception as e:
            print(f"ΓÜá∩╕Å ML Prediction Error: {e}")

    # Use ML predicted health if available, otherwise fallback to basic heuristic
    active_health_score = ml_health_score if ml_health_score is not None else battery_health_percent

    # Weights:
    # 0.4 * (100 - active_health_score)  <- Drives the main risk
    # 0.3 * drain_spike_frequency  (capped at 100)
    # 0.2 * percent_time_above_90
    # 0.1 * overheating_events     (capped at 100)
    health_component = 0.4 * (100 - max(0, min(100, active_health_score)))
    spike_component = 0.3 * min(drain_spike_frequency, 100)
    above90_component = 0.2 * max(0, min(100, percent_time_above_90))
    heat_component = 0.1 * min(overheating_events, 100)

    raw_score = health_component + spike_component + above90_component + heat_component
    score = round(max(0, min(100, raw_score)), 2)

    if score >= 60:
        level = "High"
    elif score >= 30:
        level = "Medium"
    else:
        level = "Low"

    return {
        "battery_risk_score": score,
        "risk_level": level,
        "ml_health_predicted": ml_health_score is not None
    }
