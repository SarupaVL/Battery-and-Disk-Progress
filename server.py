#!/usr/bin/env python3
"""Simple HTTP server for Battery Neural Core Dashboard"""

import http.server
import socketserver
import sys
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 3000

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()
    
    def log_message(self, format, *args):
        if '200' in format or '304' in format:
            print(f"✅ {args[0]}")

try:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"\n🚀 Battery Dashboard Server Running")
        print(f"📍 http://localhost:{PORT}\n")
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\n🛑 Stopped")
except OSError as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
