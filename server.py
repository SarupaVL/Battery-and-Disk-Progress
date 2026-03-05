#!/usr/bin/env python3
"""HTTP server for Battery Neural Core Dashboard with API endpoints"""

import http.server
import socketserver
import sys
import json
import csv
import os
from urllib.parse import urlparse, parse_qs
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
CSV_FILE = "battery_history.csv"


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == '/battery/history':
            self.handle_battery_history(parsed)
        elif parsed.path == '/battery/export':
            self.handle_battery_export(parsed)
        else:
            super().do_GET()

    def handle_battery_history(self, parsed):
        """GET /battery/history?start=ISO&end=ISO"""
        params = parse_qs(parsed.query)

        # Parse optional start/end filters
        start_dt = None
        end_dt = None
        try:
            if 'start' in params:
                start_dt = datetime.fromisoformat(params['start'][0]).replace(tzinfo=None)
            if 'end' in params:
                end_dt = datetime.fromisoformat(params['end'][0]).replace(tzinfo=None)
        except ValueError:
            self.send_json_error(400, "Invalid timestamp format. Use ISO 8601.")
            return

        if not os.path.exists(CSV_FILE):
            self.send_json_response([])
            return

        # Stream through CSV, filter, and collect matching rows
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
            self.send_json_error(500, f"Error reading CSV: {e}")
            return

        self.send_json_response(results)

    def send_json_response(self, data):
        """Send a JSON response with proper headers"""
        body = json.dumps(data).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json_error(self, code, message):
        """Send a JSON error response"""
        body = json.dumps({"error": message}).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_battery_export(self, parsed):
        """GET /battery/export?start=ISO&end=ISO — downloadable CSV"""
        params = parse_qs(parsed.query)

        start_dt = None
        end_dt = None
        try:
            if 'start' in params:
                start_dt = datetime.fromisoformat(params['start'][0]).replace(tzinfo=None)
            if 'end' in params:
                end_dt = datetime.fromisoformat(params['end'][0]).replace(tzinfo=None)
        except ValueError:
            self.send_json_error(400, "Invalid timestamp format. Use ISO 8601.")
            return

        if not os.path.exists(CSV_FILE):
            self.send_json_error(404, "No history file found.")
            return

        import io
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
            self.send_json_error(500, f"Error reading CSV: {e}")
            return

        body = output.getvalue().encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/csv')
        self.send_header('Content-Disposition', 'attachment; filename="battery_export.csv"')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        status = str(args[1]) if len(args) > 1 else ''
        if '200' in status or '304' in status:
            print(f"  {args[0]}")


try:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"\n  Battery Dashboard Server Running")
        print(f"  http://localhost:{PORT}")
        print(f"  API: http://localhost:{PORT}/battery/history?start=...&end=...")
        print(f"  Export: http://localhost:{PORT}/battery/export?start=...&end=...\n")
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\n  Stopped")
except OSError as e:
    print(f"  Error: {e}")
    sys.exit(1)
