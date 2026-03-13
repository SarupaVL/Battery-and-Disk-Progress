#!/usr/bin/env python3
"""Flask server for Battery Neural Core Dashboard with Google OAuth integration"""

import os
import sys
import json
import csv
import io
import zipfile
import requests
from datetime import datetime, timedelta
from flask import Flask, redirect, url_for, session, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import math

# Add backend directory to sys.path so it can find local modules when run from WSGI
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(ROOT_DIR, "src", "backend"))

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
PRODUCTION = os.environ.get("PRODUCTION", "false").lower() == "true"

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
    influx_results = []
    if influx_manager.client:
        res = influx_manager.query_battery_history(user_email, start_dt, end_dt)
        if res:
            influx_results = res

    # In production, we strictly use InfluxDB
    if PRODUCTION:
        return jsonify(sanitize_data(influx_results))

    # 2. Add local CSV data (Development/Fallback)
    csv_results = []
    if os.path.exists(CSV_FILE):
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

                    csv_results.append({
                        "timestamp": row['timestamp'],
                        "battery_percent": float(row.get('battery_percent', 0)),
                        "power_plugged": row.get('power_plugged', 'False').lower() == 'true',
                        "voltage": float(row.get('voltage', 0)),
                        "design_capacity_mwh": float(row.get('design_capacity_mwh', 0)),
                        "full_charge_capacity_mwh": float(row.get('full_charge_capacity_mwh', 0))
                    })
        except Exception as e:
            print(f"Error reading CSV: {e}")

    # 3. Merge both sources (InfluxDB takes precedence)
    merged = {r['timestamp']: r for r in csv_results}
    for r in influx_results:
        merged[r['timestamp']] = r

    # Sort chronologically
    final_results = sorted(merged.values(), key=lambda x: x['timestamp'])

    return jsonify(sanitize_data(final_results))

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
            
            # If no data found at all in InfluxDB, return a placeholder structure 
            # so the frontend doesn't crash before the first agent push.
            if not data["battery"] and PRODUCTION:
                data["battery"] = {
                    "current": {
                        "timestamp": datetime.now().isoformat(),
                        "psutil": {"percent": 0, "secsleft": 0, "power_plugged": False},
                        "voltage": 0, "temperature": 0, "power_draw": 0
                    },
                    "static": {"design_capacity_mwh": 0, "full_charge_capacity_mwh": 0, "cycle_count": 0},
                    "analytics": {"battery_health_percent": 0, "estimated_runtime_minutes": 0, "total_sessions": 0},
                    "battery_analytics": {
                        "drain_rate_percent_per_hour": 0, "worst_drain_rate": 0, 
                        "worst_drain_window": {"start": "", "end": ""}
                    },
                    "battery_summary": {"daily": {"average_drain_rate": 0, "max_drain_spike": 0}},
                    "predictive_maintenance": {"battery_risk_score": 0, "risk_level": "PENDING ML DATA"},
                    "charging_analytics": {"percent_time_above_90": 0, "time_charging_minutes": 0, "time_above_90_minutes": 0},
                    "history": []
                }
            if not data["disk"] and PRODUCTION:
                data["disk"] = {
                    "current": {
                        "timestamp": datetime.now().isoformat(),
                        "usage": {"total_bytes": 0, "used_bytes": 0, "free_bytes": 0, "percent": 0},
                        "io_rates": {"read_bytes_per_sec": 0, "write_bytes_per_sec": 0, "read_ops_per_sec": 0, "write_ops_per_sec": 0},
                        "hardware_health": {"temperature_c": 0, "power_on_hours": 0, "power_on_count": 0, "total_host_reads_gb": 0, "total_host_writes_gb": 0},
                        "top_processes": [], "failure_probability": 0,
                        "details": {"model": "Awaiting Telemetry", "interface": "--", "serial": "--"}
                    },
                    "analytics": {
                        "neural_health_label": "AWAITING DATA",
                        "storage_efficiency": {"logical_bytes": 0, "physical_bytes": 0, "files_scanned": 0, "status": "pending", "efficiency_ratio": 1.0}
                    },
                    "history": []
                }

            if data["battery"] and data["disk"]:
                return jsonify(sanitize_data(data))
        except Exception as e:
            print(f"⚠️ Live InfluxDB query failed, falling back to local files: {e}")

    # 2. Fallback to local JSON files (Development/Local Mode only)
    if PRODUCTION:
        return jsonify(sanitize_data(data))

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

@app.route('/api/download-agent')
@require_auth
def download_agent():
    """Bundle the background agent with a user-specific .env and return as ZIP"""
    user_email = session.get('user', {}).get('email', 'unknown')
    
    # Files to include in the agent package
    agent_files = {
        # Core scripts
        "agent/battery_service.py": os.path.join(ROOT_DIR, "src", "backend", "battery_service.py"),
        "agent/influx_storage.py": os.path.join(ROOT_DIR, "src", "backend", "influx_storage.py"),
        "agent/battery_analytics.py": os.path.join(ROOT_DIR, "src", "analytics", "battery_analytics.py"),
        "agent/disk_analytics.py": os.path.join(ROOT_DIR, "src", "analytics", "disk_analytics.py"),
        # ML models
        "agent/models/drain_ml_model.joblib": os.path.join(ROOT_DIR, "models", "drain_ml_model.joblib"),
        "agent/models/Disk_ML/disk_failure_model_gpu.pkl": os.path.join(ROOT_DIR, "models", "Disk_ML", "disk_failure_model_gpu.pkl"),
    }
    
    # Generate user-specific .env (InfluxDB creds only, NO OAuth secrets)
    agent_env = (
        f"# Battery & Disk Neural Core - Agent Configuration\n"
        f"# Auto-generated for: {user_email}\n"
        f"# Generated: {datetime.now().isoformat()}\n\n"
        f"USER_EMAIL={user_email}\n\n"
        f"# InfluxDB Cloud (shared telemetry database)\n"
        f"INFLUXDB_TOKEN={os.environ.get('INFLUXDB_TOKEN', '')}\n"
        f"INFLUXDB_ORG={os.environ.get('INFLUXDB_ORG', 'battery-disk-analytics')}\n"
        f"INFLUXDB_HOST={os.environ.get('INFLUXDB_HOST', '')}\n"
        f"INFLUXDB_DATABASE={os.environ.get('INFLUXDB_DATABASE', 'time_db')}\n"
    )
    
    # Agent-specific requirements.txt
    agent_requirements = (
        "psutil\n"
        "python-dotenv\n"
        "influxdb3-python\n"
        "pandas\n"
        "pyarrow\n"
        "numpy\n"
        "scikit-learn\n"
        "joblib\n"
        "xgboost\n"
        "wmi\n"
        "pywin32\n"
    )
    
    # Agent README
    agent_readme = (
        "# Battery & Disk Neural Core - Agent\n\n"
        f"Configured for: **{user_email}**\n\n"
        "## Setup\n\n"
        "1. Install Python 3.10+\n"
        "2. Extract this ZIP to a folder\n"
        "3. Open a terminal in the `agent/` folder\n"
        "4. Install dependencies:\n"
        "   ```\n"
        "   pip install -r requirements.txt\n"
        "   ```\n"
        "5. Run the agent:\n"
        "   ```\n"
        "   python battery_service.py\n"
        "   ```\n\n"
        "The agent will collect battery and disk metrics every 2 seconds\n"
        "and send them to the shared InfluxDB database.\n\n"
        "## Notes\n\n"
        "- Run as Administrator for full SMART disk data access\n"
        "- Or use `--no-elevate` flag for basic metrics without admin\n"
        "- The `.env` file is pre-configured with your identity and database credentials\n"
        "- **Do not share your `.env` file** — it contains database access tokens\n"
    )
    
    # Build ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add Python files and models
        for zip_path, fs_path in agent_files.items():
            if os.path.exists(fs_path):
                zf.write(fs_path, zip_path)
        
        # Add generated files
        zf.writestr("agent/.env", agent_env)
        zf.writestr("agent/requirements.txt", agent_requirements)
        zf.writestr("agent/README.md", agent_readme)
        
        # Create empty directories the agent needs
        zf.writestr("agent/data/.gitkeep", "")
        zf.writestr("agent/logs/.gitkeep", "")
    
    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"battery_disk_agent_{user_email.split('@')[0]}.zip"
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

    mode = "PRODUCTION" if PRODUCTION else "DEVELOPMENT"
    PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    print(f"\n  Battery Dashboard Server Running (Flask) [{mode}]")
    print(f"  http://localhost:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=not PRODUCTION)
