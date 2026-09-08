# Guía Wireshark — FitTrack MCP Remoto

**Autor:** Luis Palacios — Carnet 23933  
**Curso:** CC3067 Redes — Proyecto 1

Esta guía te ayuda a capturar y clasificar el tráfico entre el chatbot (host) y el servidor FitTrack remoto en Google Cloud Run.

---

## 1. Preparación

1. Despliega el servidor remoto (ver [`fittrack-remote/deploy.bat`](../fittrack-remote/deploy.bat)).
2. Configura `FITTRACK_REMOTE_URL` en `chatbot/.env` con la URL de Cloud Run.
3. En el chatbot web, cambia FitTrack a **Remote (Cloud Run)**.
4. Abre Wireshark en tu PC con permisos de administrador.

---

## 2. Iniciar la captura

### Opción A — Interfaz de red activa (recomendada)

1. Wireshark → selecciona tu interfaz Wi-Fi o Ethernet.
2. Click **Start**.
3. Filtro de captura (Display Filter después de capturar):

```
tls.host contains "run.app" || http.host contains "run.app"
```

> Cloud Run usa HTTPS (TLS). Verás tráfico TLS encriptado en capas bajas; el contenido JSON-RPC aparece **antes** de cifrarse en tu proceso (capa aplicación del cliente) o puedes usar el **log MCP del chatbot** como referencia cruzada.

### Opción B — Log MCP + captura TCP

Como el tráfico HTTPS está cifrado, para el reporte combina:

- **Captura Wireshark:** frames TCP/TLS (SYN, ACK, handshake TLS, Application Data)
- **Log del panel MCP del chatbot:** contenido JSON-RPC exacto (request/response)

Esto es válido académicamente: Wireshark muestra las capas de transporte/red; el log muestra la capa de aplicación (JSON-RPC).

---

## 3. Ejecutar la demo mientras capturas

Con la captura activa, en el chatbot:

1. Cambia FitTrack a **Remote**.
2. Envía: *"Crea mi perfil: usuario ana, 65kg, 165cm, 30 años, F, ligero, mantener"*
3. Envía: *"Calcula mi meta nutricional"*
4. Envía: *"Consulta mi progreso"*

Detén la captura después de las 3 interacciones.

---

## 4. Clasificar mensajes JSON-RPC

Usa el **log MCP del chatbot** y completa esta tabla en tu reporte:

| # | Tipo | Método JSON-RPC | Dirección | Descripción |
|---|------|-----------------|-----------|-------------|
| 1 | Sync | `initialize` | OUT → servidor | Handshake MCP, negociación de protocolo |
| 2 | Sync | `initialize` | IN ← servidor | Respuesta con `protocolVersion`, `serverInfo` |
| 3 | Sync | `notifications/initialized` | OUT → servidor | Cliente confirma inicialización (sin respuesta) |
| 4 | Request | `tools/list` | OUT → servidor | Descubrir herramientas disponibles |
| 5 | Response | `tools/list` | IN ← servidor | Lista de 7 tools con `inputSchema` |
| 6 | Request | `tools/call` | OUT → servidor | Invocar tool (ej. `crear_perfil`) |
| 7 | Response | `tools/call` | IN ← servidor | Resultado en `result.content[].text` |

**Regla rápida:**
- **Sync:** `initialize`, `notifications/initialized`
- **Request:** mensajes con `"method"` y `"id"` enviados por el cliente
- **Response:** mensajes con `"result"` o `"error"` y el mismo `"id"`

---

## 5. Qué documentar por capa (para el reporte)

### Capa de Enlace (Data Link)
- Protocolo: Ethernet / Wi-Fi (802.11)
- Qué ver: direcciones MAC origen/destino, tipo de frame
- En Wireshark: columna "Source", "Destination", protocolo "Ethernet II"

### Capa de Red (Network)
- Protocolo: IPv4 o IPv6
- Qué ver: IP origen (tu PC), IP destino (Google Cloud)
- En Wireshark: filtro `ip` — ver paquetes hacia la IP de Cloud Run

### Capa de Transporte (Transport)
- Protocolo: TCP sobre puerto 443 (HTTPS)
- Qué ver: SYN, SYN-ACK, ACK (three-way handshake), segmentos con PSH/ACK
- En Wireshark: filtro `tcp.port == 443`

### Capa de Aplicación (Application)
- Protocolo: HTTP/1.1 o HTTP/2 sobre TLS; payload JSON-RPC en POST `/mcp`
- Qué ver en log MCP: `{"jsonrpc":"2.0","method":"tools/call",...}`
- Nota: dentro de TLS el payload está cifrado en Wireshark; usa el log MCP para el contenido JSON

---

## 6. Screenshots sugeridos para el reporte

1. Wireshark con filtro `tcp.port == 443` mostrando handshake TCP
2. Frame TLS Client Hello / Server Hello
3. Panel MCP log del chatbot con un par request/response `tools/call`
4. Tabla de clasificación completada (sección 4)

---

## 7. Preguntas frecuentes

**¿Por qué no veo el JSON en Wireshark?**  
Cloud Run usa HTTPS. El cuerpo JSON-RPC viaja cifrado dentro de TLS. El curso pide analizar las capas — documenta TCP/IP/TLS en Wireshark y el JSON-RPC en el log de aplicación.

**¿Cuántos paquetes necesito?**  
Con 3 tool calls + list + initialize, ~20-50 frames TCP/TLS es suficiente.
