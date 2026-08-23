#!/usr/bin/env python3
"""
Simple manual MCP client used to test/demo the FitTrack MCP server.

It spawns server/fittrack_server.py as a subprocess and talks to it over
stdin/stdout using newline-delimited JSON-RPC 2.0, exactly like a real
MCP host (Claude Desktop, a custom chatbot, etc.) would.

Run:
    python3 test_client.py
"""

import json
import subprocess
import sys
import os

SERVER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server", "fittrack_server.py")


class MCPClient:
    def __init__(self, server_cmd):
        self.proc = subprocess.Popen(
            server_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            text=True,
            bufsize=1,
        )
        self._id = 0

    def _next_id(self):
        self._id += 1
        return self._id

    def send(self, method, params=None, notification=False):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        if not notification:
            msg["id"] = self._next_id()

        self.proc.stdin.write(json.dumps(msg, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()

        if notification:
            return None

        line = self.proc.stdout.readline()
        return json.loads(line)

    def close(self):
        self.proc.stdin.close()
        self.proc.terminate()


def pretty(label, obj):
    print(f"\n=== {label} ===")
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def main():
    client = MCPClient([sys.executable, SERVER_PATH])

    # 1. Handshake
    init_resp = client.send("initialize", {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "fittrack-test-client", "version": "1.0"},
    })
    pretty("initialize", init_resp)

    client.send("notifications/initialized", notification=True)

    # 2. Discover tools
    tools_resp = client.send("tools/list")
    pretty("tools/list", tools_resp)

    usuario = "carlos"

    # 3. Create profile
    resp = client.send("tools/call", {
        "name": "crear_perfil",
        "arguments": {
            "usuario": usuario,
            "peso_kg": 78,
            "altura_cm": 172,
            "edad": 25,
            "sexo": "M",
            "nivel_actividad": "moderado",
            "objetivo": "bajar_grasa",
        },
    })
    pretty("tools/call -> crear_perfil", resp)

    # 4. Calculate nutrition target
    resp = client.send("tools/call", {
        "name": "calcular_meta_nutricional",
        "arguments": {"usuario": usuario},
    })
    pretty("tools/call -> calcular_meta_nutricional", resp)

    # 5. Generate routine
    resp = client.send("tools/call", {
        "name": "generar_rutina",
        "arguments": {"usuario": usuario, "dias_por_semana": 4, "nivel": "intermedio"},
    })
    pretty("tools/call -> generar_rutina", resp)

    # 6. Log a meal
    resp = client.send("tools/call", {
        "name": "registrar_comida",
        "arguments": {"usuario": usuario, "alimento": "Pechuga de pollo + arroz", "cantidad_g": 350, "calorias": 520},
    })
    pretty("tools/call -> registrar_comida", resp)

    # 7. Log a workout
    resp = client.send("tools/call", {
        "name": "registrar_entrenamiento",
        "arguments": {"usuario": usuario, "rutina_dia": "Empuje (Push)", "completado": True},
    })
    pretty("tools/call -> registrar_entrenamiento", resp)

    # 8. Sync phone/smartwatch activity
    resp = client.send("tools/call", {
        "name": "sincronizar_actividad",
        "arguments": {"usuario": usuario, "pasos": 8400, "calorias_activas": 310, "dispositivo": "Apple Watch"},
    })
    pretty("tools/call -> sincronizar_actividad", resp)

    # 9. Check progress
    resp = client.send("tools/call", {
        "name": "consultar_progreso",
        "arguments": {"usuario": usuario},
    })
    pretty("tools/call -> consultar_progreso", resp)

    client.close()


if __name__ == "__main__":
    main()
