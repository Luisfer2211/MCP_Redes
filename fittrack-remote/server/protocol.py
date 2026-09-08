"""Hand-written JSON-RPC 2.0 protocol handlers for FitTrack MCP."""

import json

from tools import (
    PROTOCOL_VERSION,
    SERVER_INFO,
    TOOL_DEFINITIONS,
    TOOL_FUNCTIONS,
    load_data,
)


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


def dispatch(message: dict, on_notification=None):
    method = message.get("method")
    msg_id = message.get("id")
    is_notification = "id" not in message

    if method == "notifications/initialized":
        if on_notification:
            on_notification("notifications/initialized")
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
