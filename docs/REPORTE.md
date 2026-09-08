# Reporte — Proyecto 1: Uso de un Protocolo Existente (MCP)

**Universidad del Valle de Guatemala**  
**CC3067 Redes**  
**Autor:** Luis Palacios — Carnet 23933  
**Fecha:** _[completar]_

---

## 1. Introducción

### 1.1 Contexto

El **Model Context Protocol (MCP)** es un estándar abierto (Anthropic, 2024) que permite a los LLMs interactuar con herramientas externas mediante **JSON-RPC 2.0**. Resuelve el problema de interoperabilidad: una herramienta se implementa una vez y cualquier host compatible puede usarla.

### 1.2 Actores MCP

| Actor | Rol en este proyecto |
|-------|---------------------|
| **Servidor** | Ejecuta acciones (FitTrack local/remoto, Filesystem, Git) |
| **Cliente** | Mantiene conexión y traduce llamadas (capa en el chatbot) |
| **Anfitrión (Host)** | Aplicación que coordina clientes + LLM (chatbot web) |

### 1.3 Caso de uso industrial

**FitTrack** simula una app de fitness/nutrición (tipo MyFitnessPal): perfiles, macros, rutinas, registro de comidas/entrenos y sincronización de actividad de wearables.

---

## 2. Especificación del servidor MCP local

### 2.1 Transporte

- **Protocolo:** JSON-RPC 2.0, newline-delimited
- **Canal:** stdin/stdout (stdio)
- **Archivo:** `fittrack-mcp/server/fittrack_server.py`

### 2.2 Métodos JSON-RPC soportados

| Método | Tipo | Descripción |
|--------|------|-------------|
| `initialize` | Request/Response | Handshake, negociación de versión |
| `notifications/initialized` | Notification | Cliente listo (sin respuesta) |
| `tools/list` | Request/Response | Lista herramientas + JSON Schema |
| `tools/call` | Request/Response | Ejecuta una herramienta |
| `ping` | Request/Response | Liveness check |

### 2.3 Herramientas (tools)

| Tool | Parámetros requeridos | Descripción |
|------|----------------------|-------------|
| `crear_perfil` | usuario, peso_kg, altura_cm, edad, sexo, nivel_actividad, objetivo | Crea/actualiza perfil |
| `calcular_meta_nutricional` | usuario | Calorías y macros (Mifflin-St Jeor) |
| `generar_rutina` | usuario, dias_por_semana | Rutina semanal por nivel |
| `registrar_comida` | usuario, alimento, cantidad_g, calorias | Log de comida |
| `registrar_entrenamiento` | usuario | Marca entrenamiento completado |
| `sincronizar_actividad` | usuario, pasos, calorias_activas | Simula sync de wearable |
| `consultar_progreso` | usuario | Resumen del día/rango |

### 2.4 Almacenamiento

- Archivo JSON: `fittrack-mcp/data/fittrack_data.json`
- Sin base de datos externa

---

## 3. Especificación del servidor MCP remoto

### 3.1 Transporte

- **Protocolo:** JSON-RPC 2.0 sobre HTTP POST
- **Endpoint:** `POST /mcp`
- **Health check:** `GET /health`
- **Archivo:** `fittrack-remote/http_server.py`
- **Despliegue:** Google Cloud Run

### 3.2 URL del servicio

```
_[Pegar URL de Cloud Run después del deploy, ej: https://fittrack-mcp-xxxxx-uc.a.run.app]_
```

### 3.3 Herramientas

Idénticas al servidor local (misma lógica en `tools.py` compartido).

### 3.4 Ejemplo de request

```http
POST /mcp HTTP/1.1
Content-Type: application/json

{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"crear_perfil","arguments":{"usuario":"ana","peso_kg":65,"altura_cm":165,"edad":30,"sexo":"F","nivel_actividad":"ligero","objetivo":"mantener"}}}
```

---

## 4. Chatbot host (anfitrión web)

### 4.1 Componentes

| Componente | Archivo | Función |
|------------|---------|---------|
| API web | `chatbot/app.py` | FastAPI, sesiones, orquestación |
| Cliente MCP | `chatbot/mcp_client.py` | JSON-RPC manual (stdio + HTTP) |
| Manager | `chatbot/mcp_manager.py` | Gestiona FitTrack, Filesystem, Git |
| LLM | `chatbot/deepseek_client.py` | DeepSeek API (OpenAI-compatible) |
| UI | `chatbot/static/` | Chat + panel de log MCP |

### 4.2 Funcionalidades de rúbrica

| Requisito | Implementación |
|-----------|----------------|
| Conexión LLM vía API | DeepSeek `deepseek-chat` |
| Contexto en sesión | Historial `messages[]` por sesión |
| Log interacciones MCP | Panel lateral con timestamp, servidor, dirección, JSON |
| Filesystem MCP oficial | `@modelcontextprotocol/server-filesystem` |
| Git MCP oficial | `mcp-server-git` (Python, Anthropic official) |
| Servidor propio local | FitTrack stdio |
| Servidor propio remoto | FitTrack HTTP en Cloud Run |

### 4.3 Demo Git (Filesystem + Git)

Prompt: crear repo, README.md, add y commit "Initial commit" — botón **Run Git Demo** en la UI.

---

## 5. Análisis Wireshark

> **Completar esta sección** siguiendo [`WIRESHARK_GUIA.md`](WIRESHARK_GUIA.md).

### 5.1 Configuración de captura

- Interfaz usada: _[Wi-Fi / Ethernet]_
- Filtro aplicado: _[ej: tcp.port == 443]_
- URL remota capturada: _[URL Cloud Run]_

### 5.2 Clasificación de mensajes JSON-RPC

| # | Tipo | Método | Dirección | Observación |
|---|------|--------|-----------|-------------|
| 1 | | | | |
| 2 | | | | |
| ... | | | | |

### 5.3 Screenshots

_[Insertar capturas de Wireshark y del log MCP del chatbot]_

---

## 6. Análisis por capas OSI/TCP-IP

### 6.1 Capa de Enlace

_[Qué protocolo, qué direcciones MAC, qué observaste en Wireshark]_

### 6.2 Capa de Red (IP)

_[IPs origen/destino, IPv4/IPv6, TTL]_

### 6.3 Capa de Transporte (TCP)

_[Puertos, handshake SYN/SYN-ACK/ACK, flags, TLS]_

### 6.4 Capa de Aplicación (HTTP + JSON-RPC)

_[POST /mcp, Content-Type, estructura JSON-RPC — referencia cruzada con log MCP]_

---

## 7. Dificultades encontradas

_[Completar, ejemplos sugeridos:]_
- Implementar JSON-RPC manual sin SDK
- Diferencia entre transporte stdio (local) y HTTP (remoto)
- Tráfico TLS cifrado en Wireshark vs contenido en log MCP
- Integración de múltiples servidores MCP con prefijos de tools

---

## 8. Conclusiones

_[Completar: qué aprendiste sobre MCP, JSON-RPC, capas de red, ventajas del protocolo abierto]_

---

## 9. Referencias

- JSON-RPC: https://www.jsonrpc.org/
- MCP Architecture: https://modelcontextprotocol.io/docs/learn/architecture
- MCP Specification: https://modelcontextprotocol.io/specification/2025-11-25
- MCP Servers: https://github.com/modelcontextprotocol/servers
- Repositorio: https://github.com/Luisfer2211/MCP_Redes
