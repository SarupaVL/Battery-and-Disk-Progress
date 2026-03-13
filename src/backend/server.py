#!/usr/bin/env python3
"""Flask server for Battery Neural Core Dashboard with Google OAuth integration"""

import os
import sys
import json
import csv
import io
import requests
from datetime import datetime, timedelta
from flask import Flask, redirect, url_for, session, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import math
from influx_storage import InfluxDBManager

# Reconfigure stdout for UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Paths
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

STATIC_DIR = os.path.join(ROOT_DIR, "src", "web")
DATA_DIR = os.path.join(ROOT_DIR, "data")
CSV_FILE = os.path.join(DATA_DIR, "battery_history.csv")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='')
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))
CORS(app)

# Initialize InfluxDB Manager
influx_manager = InfluxDBManager()

# OAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

from functools import wraps

def sanitize_data(data):
    """Recursively convert NaN and Inf to None (null in JSON)"""
    if isinstance(data, dict):
        return {k: sanitize_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_data(v) for v in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
    return data

# --- Authentication Decorator ---
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({"error": "Unauthorized. Please login."}), 401
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---

@app.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')

@app.route('/login')
def login():
    redirect_uri = url_for('auth_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/callback')
def auth_callback():
    token = google.authorize_access_token()
    user = token.get('userinfo')
    if user:
        session['user'] = user
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/api/me')
def get_me():
    user = session.get('user')
    if user:
        return jsonify({
            "logged_in": True,
            "email": user.get('email'),
            "name": user.get('name'),
            "picture": user.get('picture')
        })
    return jsonify({"logged_in": False})

@app.route('/battery/history')
@require_auth
def battery_history():
    """Fetch battery history from InfluxDB with local CSV fallback"""
    user_email = session.get('user').get('email')
    
    start_param = request.args.get('start')
    end_param = request.args.get('end')
    
    start_dt = None
    end_dt = None
    try:
        if start_param:
            start_dt = datetime.fromisoformat(start_param).replace(tzinfo=None)
        if end_param:
            end_dt = datetime.fromisoformat(end_param).replace(tzinfo=None)
    except ValueError:
        return jsonify({"error": "Invalid timestamp format. Use ISO 8601."}), 400

    # 1. Try InfluxDB first
    if influx_manager.client:
        results = influx_manager.query_battery_history(user_email, start_dt, end_dt)
        if results:
            return jsonify(sanitize_data(results))

    # 2. Fallback to local CSV
    if not os.path.exists(CSV_FILE):
        return jsonify([])

    results = []
    try:
        with open(CSV_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ts = datetime.fromisoformat(row['timestamp'])
                except (ValueError, KeyError):
                    continue

                if start_dt and ts < start_dt:
                    continue
                if end_dt and ts > end_dt:
                    continue

                results.append({
                    "timestamp": row['timestamp'],
                    "battery_percent": float(row.get('battery_percent', 0)),
                    "power_plugged": row.get('power_plugged', 'False').lower() == 'true',
                    "voltage": float(row.get('voltage', 0)),
                    "design_capacity_mwh": float(row.get('design_capacity_mwh', 0)),
                    "full_charge_capacity_mwh": float(row.get('full_charge_capacity_mwh', 0))
                })
    except Exception as e:
        return jsonify({"error": f"Error reading CSV: {e}"}), 500

    return jsonify(sanitize_data(results))

@app.route('/api/live')
@require_auth
def get_live_data():
    """Fetch real-time data from InfluxDB or local JSON files"""
    user_email = session.get('user').get('email')
    
    data = {"battery": None, "disk": None}

    # 1. Try InfluxDB for latest point (Production Mode)
    if influx_manager.client:
        try:
            bat_latest, disk_latest = influx_manager.get_latest_stats(user_email)
            
            # Freshness Check: If data is older than 5 minutes, fall back to local JSON
            is_fresh = False
            if bat_latest and 'time' in bat_latest:
                import pandas as pd
                last_ts = pd.to_datetime(bat_latest['time'])
                now_ts = pd.Timestamp.now(tz=last_ts.tz)
                if (now_ts - last_ts).total_seconds() < 300:
                    is_fresh = True
                else:
                    print(f"⚠️ InfluxDB data is stale. Falling back to local files.")

            if bat_latest and is_fresh:
                data["battery"] = {
                    "current": {
                        "timestamp": bat_latest.get("timestamp"),
                        "psutil": {
                            "percent": bat_latest.get("percent"),
                            "secsleft": bat_latest.get("secsleft"),
                            "power_plugged": bat_latest.get("power_plugged")
                        },
                        "voltage": bat_latest.get("voltage"),
                        "temperature": bat_latest.get("temperature"),
                        "power_draw": bat_latest.get("power_draw")
                    },
                    "static": {
                        "design_capacity_mwh": bat_latest.get("design_capacity"),
                        "full_charge_capacity_mwh": bat_latest.get("full_charge_capacity"),
                        "cycle_count": bat_latest.get("cycle_count")
                    },
                    "analytics": {
                        "battery_health_percent": bat_latest.get("health_percent", 100),
                        "estimated_runtime_minutes": (bat_latest.get("secsleft", 0) or 0) // 60,
                        "total_sessions": bat_latest.get("total_sessions", 0)
                    },
                    "battery_analytics": {
                        "drain_rate_percent_per_hour": bat_latest.get("drain_rate", 0),
                        "worst_drain_rate": bat_latest.get("worst_drain_rate", 0),
                        "worst_drain_window": {
                            "start": bat_latest.get("worst_drain_start", ""),
                            "end": bat_latest.get("worst_drain_end", "")
                        }
                    },
                    "battery_summary": {
                        "daily": {
                            "average_drain_rate": bat_latest.get("daily_avg_drain", 0),
                            "max_drain_spike": bat_latest.get("max_drain_spike", 0)
                        }
                    },
                    "predictive_maintenance": {
                        "battery_risk_score": bat_latest.get("risk_score", 0),
                        "risk_level": "High" if bat_latest.get("risk_score", 0) >= 60 else ("Medium" if bat_latest.get("risk_score", 0) >= 30 else "Low")
                    },
                    "charging_analytics": {
                        "percent_time_above_90": bat_latest.get("percent_above_90", 0),
                        "time_charging_minutes": bat_latest.get("time_charging", 0),
                        "time_above_90_minutes": bat_latest.get("time_above_90", 0)
                    }
                }
                
                # Fetch last 1 hour for the live chart
                try:
                    one_hour_ago = datetime.now() - timedelta(hours=1)
                    history_raw = influx_manager.query_battery_history(user_email, start_time=one_hour_ago)
                    # Re-map history to match what app.js expects: {timestamp, psutil: {percent, ...}}
                    data["battery"]["history"] = [
                        {
                            "timestamp": h["timestamp"],
                            "psutil": {
                                "percent": h["percent"],
                                "power_plugged": h["power_plugged"]
                            }
                        } for h in history_raw
                    ]
                except Exception as e:
                    print(f"⚠️ Failed to fetch recent history from InfluxDB: {e}")
                    data["battery"]["history"] = []
            
            if disk_latest and is_fresh:
                # Parse top processes if present
                top_procs = []
                try:
                    procs_json = disk_latest.get("top_processes_json")
                    if procs_json:
                        top_procs = json.loads(procs_json)
                except:
                    pass

                data["disk"] = {
                    "current": {
                        "timestamp": disk_latest.get("timestamp"),
                        "usage": {
                            "total_bytes": disk_latest.get("total_bytes"),
                            "used_bytes": disk_latest.get("used_bytes"),
                            "free_bytes": disk_latest.get("free_bytes"),
                            "percent": disk_latest.get("used_percent")
                        },
                        "io_rates": {
                            "read_bytes_per_sec": disk_latest.get("read_bytes_sec"),
                            "write_bytes_per_sec": disk_latest.get("write_bytes_sec"),
                            "read_ops_per_sec": disk_latest.get("read_ops_sec"),
                            "write_ops_per_sec": disk_latest.get("write_ops_sec")
                        },
                        "hardware_health": {
                            "temperature_c": disk_latest.get("temp_c"),
                            "power_on_hours": disk_latest.get("power_on_hours"),
                            "power_on_count": disk_latest.get("power_on_count"),
                            "total_host_reads_gb": disk_latest.get("total_host_reads_gb"),
                            "total_host_writes_gb": disk_latest.get("total_host_writes_gb")
                        },
                        "top_processes": top_procs,
                        "failure_probability": disk_latest.get("failure_probability"),
                        "details": {
                            "model": disk_latest.get("model", "Unknown"),
                            "interface": disk_latest.get("interface", "Unknown"),
                            "serial": disk_latest.get("serial", "Unknown")
                        }
                    },
                    "analytics": {
                        "neural_health_label": "SAFE" if (disk_latest.get("failure_probability") or 0) < 0.1 else "WARNING",
                        "storage_efficiency": {
                            "logical_bytes": disk_latest.get("logical_bytes", 0),
                            "physical_bytes": disk_latest.get("physical_bytes", 0),
                            "files_scanned": disk_latest.get("files_scanned", 0),
                            "status": disk_latest.get("storage_status", "unknown"),
                            "efficiency_ratio": disk_latest.get("efficiency_ratio", 1.0)
                        }
                    }
                }

                # Fetch last 1 hour for disk chart
                try:
                    one_hour_ago = datetime.now() - timedelta(hours=1)
                    disk_history_raw = influx_manager.query_disk_history(user_email, start_time=one_hour_ago)
                    data["disk"]["history"] = [
                        {
                            "timestamp": h["timestamp"],
                            "active_time": h["active_time"]
                        } for h in disk_history_raw
                    ]
                except Exception as e:
                    print(f"⚠️ Failed to fetch recent disk history from InfluxDB: {e}")
                    data["disk"]["history"] = []
            
            # Note: history and top_processes are omitted here as they are large 
            # and usually accessed via specialized endpoints or local fallback.
            
            if data["battery"] and data["disk"]:
                return jsonify(sanitize_data(data))
        except Exception as e:
            print(f"⚠️ Live InfluxDB query failed, falling back to local files: {e}")

    # 2. Fallback to local JSON files (Development/Local Mode)
    try:
        bat_json = os.path.join(DATA_DIR, "battery_data.json")
        disk_json = os.path.join(DATA_DIR, "disk_data.json")
        
        if os.path.exists(bat_json):
            with open(bat_json, "r") as f:
                data["battery"] = json.load(f)
        
        if os.path.exists(disk_json):
            with open(disk_json, "r") as f:
                data["disk"] = json.load(f)
                
        return jsonify(sanitize_data(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/battery/export')
@require_auth
def battery_export():
    """Export battery history to CSV from InfluxDB or local file"""
    user_email = session.get('user').get('email')
    start_param = request.args.get('start')
    end_param = request.args.get('end')
    
    start_dt = None
    end_dt = None
    try:
        if start_param:
            start_dt = datetime.fromisoformat(start_param).replace(tzinfo=None)
        if end_param:
            end_dt = datetime.fromisoformat(end_param).replace(tzinfo=None)
    except ValueError:
        return jsonify({"error": "Invalid timestamp format. Use ISO 8601."}), 400

    # 1. Fetch data
    rows = []
    if influx_manager.client:
        rows = influx_manager.query_battery_history(user_email, start_dt, end_dt)
    
    if not rows and os.path.exists(CSV_FILE):
        # Fallback to CSV
        try:
            with open(CSV_FILE, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        ts = datetime.fromisoformat(row['timestamp'])
                    except (ValueError, KeyError):
                        continue
                    if start_dt and ts < start_dt:
                        continue
                    if end_dt and ts > end_dt:
                        continue
                    rows.append(row)
        except Exception as e:
            return jsonify({"error": f"Error reading CSV: {e}"}), 500

    if not rows:
        return jsonify({"error": "No data found to export."}), 404

    # 2. Generate CSV
    output = io.StringIO()
    # Use headers from first row or common headers
    fieldnames = rows[0].keys() if isinstance(rows[0], dict) else ["timestamp", "battery_percent", "power_plugged", "voltage", "design_capacity_mwh", "full_charge_capacity_mwh"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    
    filename = f"battery_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@app.route('/data/<path:filename>')
@require_auth
def serve_data(filename):
    return send_from_directory(DATA_DIR, filename)

# Serve other static files manually if they are not in the root
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(STATIC_DIR, path)

if __name__ == '__main__':
    # Environmental Check
    required_vars = ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"]
    missing = [v for v in required_vars if not os.environ.get(v)]
    if missing:
        print(f"❌ CRITICAL ERROR: Missing environment variables: {', '.join(missing)}")
        print("Please check your .env file.")
        sys.exit(1)
        
    if not os.environ.get("INFLUXDB_TOKEN"):
        print("⚠️ WARNING: INFLUXDB_TOKEN missing. Dashboard will operate in local mode (JSON/CSV).")

    PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    print(f"\n  Battery Dashboard Server Running (Flask)")
    print(f"  http://localhost:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=True)
