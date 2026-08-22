#!/usr/bin/env python3
"""
FitTrack MCP Server
====================

A local MCP (Model Context Protocol) server implemented MANUALLY using
JSON-RPC 2.0 over stdio, with NO MCP SDKs (no FastMCP, no official
python-sdk). This is intentional per the assignment requirements: all
protocol framing, message parsing, and dispatch logic below is hand-written.

Transport
---------
Newline-delimited JSON over stdin/stdout, per the MCP stdio transport:
    - Every JSON-RPC message is a single line of JSON terminated by "\n".
    - stdout is reserved EXCLUSIVELY for protocol messages.
    - Any logging/debug output goes to stderr, never stdout.

Supported JSON-RPC methods
---------------------------
    initialize                 -> capability negotiation / handshake
    notifications/initialized  -> client notification, no response
    tools/list                 -> returns the list of available tools
    tools/call                 -> invokes a tool by name with arguments
    ping                       -> simple liveness check

Business domain
----------------
FitTrack is a general-purpose fitness & nutrition assistant (like
MyFitnessPal / Fitbit Coach). It is not tied to a specific gym. It exposes
7 tools covering: user profile, nutrition targets, workout routines,
meal logging, workout logging, wearable/phone activity sync, and
progress reporting.

Storage
-------
A single JSON file (data/fittrack_data.json) acts as a very small
"database", keyed by username. This keeps the server dependency-free
(Python standard library only) and easy to inspect/debug.
"""

import sys
import json
import os
from datetime import datetime, date

# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DATA_FILE = os.path.join(DATA_DIR, "fittrack_data.json")


def log(msg: str) -> None:
    """Debug/info logging. MUST go to stderr, stdout is protocol-only."""
    print(f"[fittrack-mcp] {msg}", file=sys.stderr, flush=True)


def load_data() -> dict:
    if not os.path.exists(DATA_FILE):
        return {"users": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"users": {}}


def save_data(data: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_user(data: dict, usuario: str) -> dict:
    if usuario not in data["users"]:
        data["users"][usuario] = {
            "perfil": None,
            "meta_nutricional": None,
            "rutina": None,
            "comidas": [],       # list of {fecha, alimento, cantidad_g, calorias}
            "entrenamientos": [],  # list of {fecha, rutina_dia, completado, notas}
            "actividad": [],     # list of {fecha, pasos, calorias_activas, dispositivo}
        }
    return data["users"][usuario]


def today() -> str:
    return date.today().isoformat()


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

ACTIVITY_MULTIPLIERS = {
    "sedentario": 1.2,
    "ligero": 1.375,
    "moderado": 1.55,
    "activo": 1.725,
    "muy_activo": 1.9,
}

OBJECTIVE_KCAL_ADJUSTMENT = {
    "bajar_grasa": -500,
    "mantener": 0,
    "ganar_musculo": 300,
}

WORKOUT_TEMPLATES = {
    "principiante": [
        ("Full Body A", ["Sentadilla goblet 3x10", "Press banca mancuerna 3x10", "Remo con mancuerna 3x10", "Plancha 3x30s"]),
        ("Full Body B", ["Peso muerto rumano 3x10", "Press militar 3x10", "Jalón al pecho 3x10", "Elevaciones de piernas 3x12"]),
    ],
    "intermedio": [
        ("Empuje (Push)", ["Press banca 4x8", "Press militar 3x10", "Fondos 3x10", "Extensión tríceps 3x12"]),
        ("Tirón (Pull)", ["Dominadas 4x8", "Remo con barra 3x10", "Curl bíceps 3x12", "Face pull 3x15"]),
        ("Pierna (Legs)", ["Sentadilla 4x8", "Peso muerto rumano 3x10", "Zancadas 3x12", "Elevación de talones 3x15"]),
    ],
    "avanzado": [
        ("Pecho / Tríceps", ["Press banca 5x5", "Press inclinado mancuerna 4x8", "Fondos lastrados 4x8", "Extensión tríceps polea 4x12"]),
        ("Espalda / Bíceps", ["Peso muerto 5x5", "Dominadas lastradas 4x6", "Remo T 4x8", "Curl barra Z 4x10"]),
        ("Pierna", ["Sentadilla trasera 5x5", "Prensa 4x10", "Peso muerto rumano 4x8", "Curl femoral 4x12"]),
        ("Hombro / Core", ["Press militar 4x8", "Elevaciones laterales 4x12", "Face pull 4x15", "Plancha con peso 3x45s"]),
    ],
}


def tool_crear_perfil(args: dict, data: dict) -> dict:
    usuario = args["usuario"]
    user = get_user(data, usuario)
    user["perfil"] = {
        "peso_kg": args["peso_kg"],
        "altura_cm": args["altura_cm"],
        "edad": args["edad"],
        "sexo": args["sexo"],
        "nivel_actividad": args["nivel_actividad"],
        "objetivo": args["objetivo"],
        "actualizado": today(),
    }
    save_data(data)
    return {"ok": True, "perfil": user["perfil"]}


def tool_calcular_meta_nutricional(args: dict, data: dict) -> dict:
    usuario = args["usuario"]
    user = get_user(data, usuario)
    perfil = user.get("perfil")
    if not perfil:
        raise ValueError(f"El usuario '{usuario}' no tiene un perfil creado. Llama primero a crear_perfil.")

    peso = perfil["peso_kg"]
    altura = perfil["altura_cm"]
    edad = perfil["edad"]
    sexo = perfil["sexo"].upper()

    # Mifflin-St Jeor
    if sexo == "M":
        bmr = 10 * peso + 6.25 * altura - 5 * edad + 5
    else:
        bmr = 10 * peso + 6.25 * altura - 5 * edad - 161

    multiplier = ACTIVITY_MULTIPLIERS.get(perfil["nivel_actividad"], 1.375)
    tdee = bmr * multiplier

    adjustment = OBJECTIVE_KCAL_ADJUSTMENT.get(perfil["objetivo"], 0)
    calorias_objetivo = round(tdee + adjustment)

    proteina_g = round(peso * 2.0)
    grasas_g = round((calorias_objetivo * 0.25) / 9)
    kcal_restantes = calorias_objetivo - (proteina_g * 4) - (grasas_g * 9)
    carbohidratos_g = max(round(kcal_restantes / 4), 0)

    meta = {
        "calorias_objetivo": calorias_objetivo,
        "proteina_g": proteina_g,
        "grasas_g": grasas_g,
        "carbohidratos_g": carbohidratos_g,
        "bmr": round(bmr),
        "tdee": round(tdee),
    }
    user["meta_nutricional"] = meta
    save_data(data)
    return meta


def tool_generar_rutina(args: dict, data: dict) -> dict:
    usuario = args["usuario"]
    user = get_user(data, usuario)
    dias = int(args["dias_por_semana"])
    nivel = args.get("nivel", "principiante")
    equipo = args.get("equipo_disponible", "gimnasio_completo")

    template = WORKOUT_TEMPLATES.get(nivel, WORKOUT_TEMPLATES["principiante"])
    plan = []
    for i in range(dias):
        nombre, ejercicios = template[i % len(template)]
        plan.append({"dia": i + 1, "enfoque": nombre, "ejercicios": ejercicios})

    rutina = {
        "nivel": nivel,
        "dias_por_semana": dias,
        "equipo_disponible": equipo,
        "plan": plan,
        "generada": today(),
    }
    user["rutina"] = rutina
    save_data(data)
    return rutina


def tool_registrar_comida(args: dict, data: dict) -> dict:
    usuario = args["usuario"]
    user = get_user(data, usuario)
    entrada = {
        "fecha": args.get("fecha", today()),
        "alimento": args["alimento"],
        "cantidad_g": args["cantidad_g"],
        "calorias": args["calorias"],
    }
    user["comidas"].append(entrada)
    save_data(data)

    total_dia = sum(c["calorias"] for c in user["comidas"] if c["fecha"] == entrada["fecha"])
    return {"ok": True, "registro": entrada, "calorias_totales_del_dia": total_dia}


def tool_registrar_entrenamiento(args: dict, data: dict) -> dict:
    usuario = args["usuario"]
    user = get_user(data, usuario)
    entrada = {
        "fecha": args.get("fecha", today()),
        "rutina_dia": args.get("rutina_dia", ""),
        "completado": args.get("completado", True),
        "notas": args.get("notas", ""),
    }
    user["entrenamientos"].append(entrada)
    save_data(data)
    return {"ok": True, "registro": entrada}


def tool_sincronizar_actividad(args: dict, data: dict) -> dict:
    """
    NOTE (scope of this course project): this tool simulates receiving
    activity data that would normally come from a phone/smartwatch
    health API (Apple HealthKit, Google Fit, Fitbit Web API, etc.).
    A production integration would authenticate with the provider via
    OAuth and pull steps/active-calories from their API; here the tool
    simply accepts that data as arguments, so the MCP layer and the
    chatbot flow can be demonstrated end-to-end without needing a real
    device or third-party OAuth credentials.
    """
    usuario = args["usuario"]
    user = get_user(data, usuario)
    entrada = {
        "fecha": args.get("fecha", today()),
        "pasos": args["pasos"],
        "calorias_activas": args["calorias_activas"],
        "dispositivo": args.get("dispositivo", "desconocido"),
    }
    user["actividad"].append(entrada)
    save_data(data)
    return {"ok": True, "registro": entrada}


def tool_consultar_progreso(args: dict, data: dict) -> dict:
    usuario = args["usuario"]
    user = get_user(data, usuario)
    fecha_inicio = args.get("fecha_inicio", today())
    fecha_fin = args.get("fecha_fin", today())

    comidas = [c for c in user["comidas"] if fecha_inicio <= c["fecha"] <= fecha_fin]
    entrenamientos = [e for e in user["entrenamientos"] if fecha_inicio <= e["fecha"] <= fecha_fin]
    actividad = [a for a in user["actividad"] if fecha_inicio <= a["fecha"] <= fecha_fin]

    calorias_consumidas = sum(c["calorias"] for c in comidas)
    pasos_totales = sum(a["pasos"] for a in actividad)
    calorias_activas_totales = sum(a["calorias_activas"] for a in actividad)
    entrenamientos_completados = sum(1 for e in entrenamientos if e.get("completado"))

    meta = user.get("meta_nutricional")

    return {
        "rango": {"inicio": fecha_inicio, "fin": fecha_fin},
        "calorias_consumidas": calorias_consumidas,
        "calorias_objetivo": meta["calorias_objetivo"] if meta else None,
        "pasos_totales": pasos_totales,
        "calorias_activas_totales": calorias_activas_totales,
        "entrenamientos_completados": entrenamientos_completados,
        "detalle_comidas": comidas,
        "detalle_entrenamientos": entrenamientos,
        "detalle_actividad": actividad,
    }


TOOL_FUNCTIONS = {
    "crear_perfil": tool_crear_perfil,
    "calcular_meta_nutricional": tool_calcular_meta_nutricional,
    "generar_rutina": tool_generar_rutina,
    "registrar_comida": tool_registrar_comida,
    "registrar_entrenamiento": tool_registrar_entrenamiento,
    "sincronizar_actividad": tool_sincronizar_actividad,
    "consultar_progreso": tool_consultar_progreso,
}

# ---------------------------------------------------------------------------
# Tool schemas (exposed via tools/list)
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "name": "crear_perfil",
        "description": "Crea o actualiza el perfil fisico y objetivo de un usuario.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "usuario": {"type": "string", "description": "Identificador o nombre del usuario"},
                "peso_kg": {"type": "number"},
                "altura_cm": {"type": "number"},
                "edad": {"type": "integer"},
                "sexo": {"type": "string", "enum": ["M", "F"]},
                "nivel_actividad": {
                    "type": "string",
                    "enum": ["sedentario", "ligero", "moderado", "activo", "muy_activo"],
                },
                "objetivo": {
                    "type": "string",
                    "enum": ["bajar_grasa", "mantener", "ganar_musculo"],
                },
            },
            "required": ["usuario", "peso_kg", "altura_cm", "edad", "sexo", "nivel_actividad", "objetivo"],
        },
    },
    {
        "name": "calcular_meta_nutricional",
        "description": "Calcula calorias y macronutrientes diarios objetivo a partir del perfil guardado (formula Mifflin-St Jeor).",
        "inputSchema": {
            "type": "object",
            "properties": {"usuario": {"type": "string"}},
            "required": ["usuario"],
        },
    },
    {
        "name": "generar_rutina",
        "description": "Genera una rutina de ejercicio semanal segun nivel y dias disponibles.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "usuario": {"type": "string"},
                "dias_por_semana": {"type": "integer", "minimum": 1, "maximum": 7},
                "nivel": {"type": "string", "enum": ["principiante", "intermedio", "avanzado"]},
                "equipo_disponible": {"type": "string"},
            },
            "required": ["usuario", "dias_por_semana"],
        },
    },
    {
        "name": "registrar_comida",
        "description": "Registra una comida consumida por el usuario en su log diario.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "usuario": {"type": "string"},
                "alimento": {"type": "string"},
                "cantidad_g": {"type": "number"},
                "calorias": {"type": "number"},
                "fecha": {"type": "string", "description": "YYYY-MM-DD, opcional (default: hoy)"},
            },
            "required": ["usuario", "alimento", "cantidad_g", "calorias"],
        },
    },
    {
        "name": "registrar_entrenamiento",
        "description": "Marca un entrenamiento como realizado.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "usuario": {"type": "string"},
                "fecha": {"type": "string"},
                "rutina_dia": {"type": "string"},
                "completado": {"type": "boolean"},
                "notas": {"type": "string"},
            },
            "required": ["usuario"],
        },
    },
    {
        "name": "sincronizar_actividad",
        "description": "Sincroniza pasos y calorias activas capturadas por el telefono o smartwatch del usuario (simulado para fines del curso).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "usuario": {"type": "string"},
                "fecha": {"type": "string"},
                "pasos": {"type": "integer"},
                "calorias_activas": {"type": "number"},
                "dispositivo": {"type": "string", "description": "Ej: Apple Watch, Fitbit, Google Fit"},
            },
            "required": ["usuario", "pasos", "calorias_activas"],
        },
    },
    {
        "name": "consultar_progreso",
        "description": "Devuelve un resumen de calorias, macros, pasos y entrenamientos en un rango de fechas.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "usuario": {"type": "string"},
                "fecha_inicio": {"type": "string"},
                "fecha_fin": {"type": "string"},
            },
            "required": ["usuario"],
        },
    },
]

SERVER_INFO = {"name": "fittrack-mcp-server", "version": "1.0.0"}
PROTOCOL_VERSION = "2025-06-18"

# ---------------------------------------------------------------------------
# JSON-RPC 2.0 plumbing (hand-written, no MCP SDK)
# ---------------------------------------------------------------------------


def make_result(msg_id, result):
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def make_error(msg_id, code, message):
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def handle_initialize(msg_id, params):
    return make_result(msg_id, {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {"tools": {}},
        "serverInfo": SERVER_INFO,
    })


def handle_tools_list(msg_id, params):
    return make_result(msg_id, {"tools": TOOL_DEFINITIONS})


def handle_tools_call(msg_id, params):
    name = params.get("name")
    arguments = params.get("arguments", {})

    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        return make_error(msg_id, -32602, f"Herramienta desconocida: {name}")

    data = load_data()
    try:
        result = func(arguments, data)
        content_text = json.dumps(result, ensure_ascii=False, indent=2)
        return make_result(msg_id, {
            "content": [{"type": "text", "text": content_text}],
            "isError": False,
        })
    except KeyError as e:
        return make_result(msg_id, {
            "content": [{"type": "text", "text": f"Falta el parametro requerido: {e}"}],
            "isError": True,
        })
    except ValueError as e:
        return make_result(msg_id, {
            "content": [{"type": "text", "text": str(e)}],
            "isError": True,
        })
    except Exception as e:
        return make_result(msg_id, {
            "content": [{"type": "text", "text": f"Error interno: {e}"}],
            "isError": True,
        })


def handle_ping(msg_id, params):
    return make_result(msg_id, {})


METHOD_HANDLERS = {
    "initialize": handle_initialize,
    "tools/list": handle_tools_list,
    "tools/call": handle_tools_call,
    "ping": handle_ping,
}


def dispatch(message: dict):
    method = message.get("method")
    msg_id = message.get("id")

    # Notifications (no "id") never get a response, per JSON-RPC 2.0.
    is_notification = "id" not in message

    if method == "notifications/initialized":
        log("Cliente confirmo inicializacion (notifications/initialized)")
        return None

    handler = METHOD_HANDLERS.get(method)
    if handler is None:
        if is_notification:
            return None
        return make_error(msg_id, -32601, f"Metodo no encontrado: {method}")

    try:
        response = handler(msg_id, message.get("params", {}) or {})
    except Exception as e:
        if is_notification:
            return None
        return make_error(msg_id, -32603, f"Error interno del servidor: {e}")

    return None if is_notification else response


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
        response = dispatch(message)
        if response is not None:
            log(f"OUT <- {json.dumps(response, ensure_ascii=False)}")
            print(json.dumps(response, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
