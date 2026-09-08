#!/usr/bin/env python3
"""FitTrack MCP Server — HTTP transport for Cloud Run (JSON-RPC 2.0, hand-written)."""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

# Add shared server modules to path
SERVER_DIR = os.path.join(os.path.dirname(__file__), "server")
sys.path.insert(0, SERVER_DIR)

from protocol import dispatch, make_error  # noqa: E402
from tools import PROTOCOL_VERSION  # noqa: E402


def log(msg: str) -> None:
    print(f"[fittrack-remote] {msg}", file=sys.stderr, flush=True)


class MCPHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        log(format % args)

    def do_GET(self):
        if self.path in ("/", "/health"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "service": "fittrack-mcp-remote",
                "protocol": PROTOCOL_VERSION,
            }).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path != "/mcp":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")

        try:
            message = json.loads(body)
        except json.JSONDecodeError:
            response = make_error(None, -32700, "Parse error: JSON invalido")
            self._send_json(400, response)
            return

        log(f"IN  -> {json.dumps(message, ensure_ascii=False)}")
        response = dispatch(message, on_notification=lambda m: log(f"Notification: {m}"))

        if response is None:
            self.send_response(204)
            self.end_headers()
            return

        log(f"OUT <- {json.dumps(response, ensure_ascii=False)}")
        self._send_json(200, response)

    def _send_json(self, status: int, data: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())


def main():
    port = int(os.environ.get("PORT", "8080"))
    os.environ.setdefault("FITTRACK_DATA_DIR", "/app/data")
    server = HTTPServer(("0.0.0.0", port), MCPHandler)
    log(f"FitTrack MCP HTTP server listening on port {port} (protocol {PROTOCOL_VERSION})")
    server.serve_forever()


if __name__ == "__main__":
    main()
