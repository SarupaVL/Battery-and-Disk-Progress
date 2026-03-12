#!/usr/bin/env python3
"""Flask server for Battery Neural Core Dashboard with Google OAuth integration"""

import os
import sys
import json
import csv
import io
import requests
from datetime import datetime
from flask import Flask, redirect, url_for, session, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

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
    # In a multi-tenant production environment, we would query InfluxDB here 
    # filtered by session.get('user').get('email').
    
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

    return jsonify(results)

@app.route('/battery/export')
@require_auth
def battery_export():
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

    if not os.path.exists(CSV_FILE):
        return jsonify({"error": "No history file found."}), 404

    output = io.StringIO()
    try:
        with open(CSV_FILE, "r") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                try:
                    ts = datetime.fromisoformat(row['timestamp'])
                except (ValueError, KeyError):
                    continue
                if start_dt and ts < start_dt:
                    continue
                if end_dt and ts > end_dt:
                    continue
                writer.writerow(row)
    except Exception as e:
        return jsonify({"error": f"Error reading CSV: {e}"}), 500

    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    
    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name='battery_export.csv'
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
    PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    print(f"\n  Battery Dashboard Server Running (Flask)")
    print(f"  http://localhost:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=True)
