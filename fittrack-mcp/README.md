# FitTrack MCP Server

A local MCP (Model Context Protocol) server for a general-purpose fitness &
nutrition assistant, built for **CC3067 Redes – Project 1 (Use of an
existing protocol)** at Universidad del Valle de Guatemala.

The business scenario mirrors consumer fitness apps like MyFitnessPal or
Fitbit Coach: it is not tied to a specific gym, and it lets a chatbot help a
user plan their nutrition and workouts, log meals and training sessions,
sync activity data from a phone/smartwatch, and check their progress over
time.

**Important:** this server implements the MCP JSON-RPC 2.0 protocol
**manually**, using only the Python standard library (`json`, `sys`, `os`,
`datetime`). No MCP SDK (FastMCP, official `mcp` python package, etc.) is
used, per the assignment requirements.

## Architecture

```
Host (chatbot) <--stdio/JSON-RPC 2.0--> FitTrack MCP Server (this repo)
```

- **Server**: `server/fittrack_server.py`. Reads newline-delimited JSON-RPC
  requests from stdin, writes responses to stdout. All logging goes to
  stderr, since stdout is reserved exclusively for protocol messages.
- **Storage**: a single JSON file at `data/fittrack_data.json`, created
  automatically on first use. No external database required.

## Tools exposed

| Tool | Description |
|---|---|
| `crear_perfil` | Creates/updates a user's physical profile and goal |
| `calcular_meta_nutricional` | Calculates daily calorie & macro targets (Mifflin-St Jeor formula) |
| `generar_rutina` | Generates a weekly workout routine by level and days/week |
| `registrar_comida` | Logs a meal for the day |
| `registrar_entrenamiento` | Marks a workout as completed |
| `sincronizar_actividad` | Syncs steps/active calories from a phone or smartwatch (see note below) |
| `consultar_progreso` | Returns a summary of calories, macros, steps and workouts for a date range |

Full JSON Schema for each tool's parameters is available by calling
`tools/list` on the running server (see [Usage](#usage) below), and is also
defined in `server/fittrack_server.py`.

### Note on `sincronizar_actividad`

For the scope of this course project, this tool **simulates** receiving
activity data that would normally come from a phone/smartwatch health API
(Apple HealthKit, Google Fit, Fitbit Web API, etc.). A production
integration would authenticate with the provider via OAuth and pull
steps/active-calories automatically; here the tool simply accepts that data
as arguments, so the MCP flow (and the chatbot host built on top of it) can
be demonstrated end-to-end without needing a real device or third-party
credentials.

## Requirements

- Python 3.8+
- No third-party dependencies (standard library only)

## Installation

```bash
git clone https://github.com/Luisfer2211/MCP_Redes.git
cd MCP_Redes/fittrack-mcp
```

That's it — there is nothing to `pip install`.

## Usage

### Option A: run the included test client (recommended for a quick demo)

The test client spawns the server as a subprocess and exchanges the full
MCP handshake plus a chain of tool calls (create profile -> calculate
nutrition target -> generate routine -> log a meal -> log a workout -> sync
activity -> check progress):

```bash
python test_client.py
```

On Linux/macOS you can also use `python3 test_client.py`.

You should see the JSON-RPC request/response pair for each step printed to
your terminal. See `examples/example_session.md` for the exact messages
this exchange produces.

### Option B: run the server standalone and talk to it manually

```bash
python server/fittrack_server.py
```

The server will block, waiting for JSON-RPC messages on stdin, one per
line. Example manual session (type each line and press Enter):

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"manual-test","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/list"}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"crear_perfil","arguments":{"usuario":"ana","peso_kg":65,"altura_cm":165,"edad":30,"sexo":"F","nivel_actividad":"ligero","objetivo":"mantener"}}}
```

Press `Ctrl+D` (Linux/macOS) or `Ctrl+Z` then Enter (Windows) to close stdin
and stop the server.

### Option C: connect it to an MCP-compatible host (e.g. Claude Desktop or Cursor)

Add an entry to your host's MCP server configuration pointing to
`server/fittrack_server.py`. Example for Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "fittrack": {
      "command": "python",
      "args": ["C:/Users/you/MCP_Redes/fittrack-mcp/server/fittrack_server.py"]
    }
  }
}
```

Restart the host afterward so it picks up the new server.

## Project status

Phase 1 (local MCP server) and Phase 2 (chatbot host, official MCP servers, remote HTTP server) are implemented in this repository. See the root [`README.md`](../README.md) for the full project setup, chatbot, Cloud Run deploy, and documentation.

## Repository structure

```
fittrack-mcp/
├── README.md
├── .gitignore
├── test_client.py          # manual MCP client used to demo/test the server
├── server/
│   ├── fittrack_server.py  # stdio transport entrypoint
│   ├── protocol.py         # hand-written JSON-RPC dispatch
│   └── tools.py            # shared business logic
├── examples/
│   └── example_session.md  # sample raw JSON-RPC request/response pairs
└── data/                   # created at runtime, gitignored
```

## Author

Luis Palacios — Carnet 23933  
CC3067 Redes — Universidad del Valle de Guatemala — Project 1
