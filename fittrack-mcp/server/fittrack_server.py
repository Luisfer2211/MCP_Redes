#!/usr/bin/env python3
"""
FitTrack MCP Server — stdio transport (JSON-RPC 2.0, hand-written, no MCP SDK).
"""

import json
import sys

from protocol import dispatch, make_error
from tools import PROTOCOL_VERSION


def log(msg: str) -> None:
    print(f"[fittrack-mcp] {msg}", file=sys.stderr, flush=True)


def main():
    log(f"FitTrack MCP Server iniciado (protocolo {PROTOCOL_VERSION}). Esperando mensajes en stdin...")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            error = make_error(None, -32700, "Parse error: JSON invalido")
            print(json.dumps(error), flush=True)
            continue

        log(f"IN  -> {json.dumps(message, ensure_ascii=False)}")
        response = dispatch(message, on_notification=lambda m: log(f"Cliente confirmo inicializacion ({m})"))
        if response is not None:
            log(f"OUT <- {json.dumps(response, ensure_ascii=False)}")
            print(json.dumps(response, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
