"""FitTrack business logic and tool definitions (shared by local and remote servers)."""

import json
import os
from datetime import date

DATA_DIR = os.environ.get(
    "FITTRACK_DATA_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"),
)
DATA_FILE = os.path.join(DATA_DIR, "fittrack_data.json")


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
            "comidas": [],
            "entrenamientos": [],
            "actividad": [],
        }
    return data["users"][usuario]


def today() -> str:
    return date.today().isoformat()


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
        ("Full Body B", ["Peso muerto rumano 3x10", "Press militar 3x10", "Jalon al pecho 3x10", "Elevaciones de piernas 3x12"]),
    ],
    "intermedio": [
        ("Empuje (Push)", ["Press banca 4x8", "Press militar 3x10", "Fondos 3x10", "Extension triceps 3x12"]),
        ("Tiron (Pull)", ["Dominadas 4x8", "Remo con barra 3x10", "Curl biceps 3x12", "Face pull 3x15"]),
        ("Pierna (Legs)", ["Sentadilla 4x8", "Peso muerto rumano 3x10", "Zancadas 3x12", "Elevacion de talones 3x15"]),
    ],
    "avanzado": [
        ("Pecho / Triceps", ["Press banca 5x5", "Press inclinado mancuerna 4x8", "Fondos lastrados 4x8", "Extension triceps polea 4x12"]),
        ("Espalda / Biceps", ["Peso muerto 5x5", "Dominadas lastradas 4x6", "Remo T 4x8", "Curl barra Z 4x10"]),
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
