#!/usr/bin/env python3
"""Simple HTTP server for Battery Neural Core Dashboard"""

import http.server
import socketserver
import sys
import os
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 3000

# Directory configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PROJECT_ROOT, **kwargs)

    def do_GET(self):
        # Redirect root to index.html in src/web
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/src/web/index.html')
            self.end_headers()
            return
        return super().do_GET()

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()
    
    def log_message(self, format, *args):
        if '200' in format or '304' in format:
            print(f"✅ {args[0]}")

try:
    # Set the working directory to PROJECT_ROOT for the handler context
    os.chdir(PROJECT_ROOT)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"\n🚀 Battery Dashboard Server Running")
        print(f"📍 http://localhost:{PORT}")
        print(f"📁 Project Root: {PROJECT_ROOT}\n")
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\n🛑 Stopped")
except OSError as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
