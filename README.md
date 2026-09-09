# MCP_Redes — CC3067 Project 1 (Complete)

Repository for **CC3067 Redes** (Universidad del Valle de Guatemala), Project 1: *Use of an existing protocol* (MCP / JSON-RPC 2.0).

**Author:** Luis Palacios — Carnet 23933  
**Repository:** https://github.com/Luisfer2211/MCP_Redes

## Project components

| Path | Description |
|------|-------------|
| [`fittrack-mcp/`](fittrack-mcp/) | Custom local FitTrack MCP server (stdio, hand-written JSON-RPC) |
| [`fittrack-remote/`](fittrack-remote/) | Same server over HTTP for Google Cloud Run |
| [`chatbot/`](chatbot/) | Web chatbot host (DeepSeek + MCP clients + interaction log) |
| [`capturas/`](capturas/) | Wireshark screenshots and `.pcapng` capture |
| [`docs/`](docs/) | Spanish project report |

## Architecture

```
Web UI  →  FastAPI host  →  DeepSeek API
                ↓
    MCP clients (manual JSON-RPC)
    ├── FitTrack (local stdio or remote HTTP)
    ├── Filesystem MCP (official, npx)
    └── Git MCP (official, mcp-server-git via pip)
```

## Live deployments (Google Cloud Run)

| Service | URL |
|---------|-----|
| **Chatbot host** | https://fittrack-chatbot-907980440492.us-central1.run.app |
| **FitTrack MCP (remote)** | https://fittrack-mcp-907980440492.us-central1.run.app |

The public chatbot uses **remote** FitTrack by default. For Wireshark analysis, run the chatbot locally in **Remote** mode so TLS traffic to Cloud Run is visible on your machine.

## Quick start — local FitTrack server

```bash
git clone https://github.com/Luisfer2211/MCP_Redes.git
cd MCP_Redes/fittrack-mcp
python test_client.py
```

## Quick start — web chatbot host

```bash
cd MCP_Redes/chatbot
pip install -r requirements.txt
cp .env.example .env
# Edit .env: set DEEPSEEK_API_KEY
python -m uvicorn app:app --reload --port 8000
```

Open http://localhost:8000

### Environment variables (`chatbot/.env`)

| Variable | Description |
|----------|-------------|
| `DEEPSEEK_API_KEY` | DeepSeek API key (required) |
| `FITTRACK_MODE` | `local` (default) or `remote` |
| `FITTRACK_REMOTE_URL` | Cloud Run URL when using remote mode |

### Web UI features

- Spanish interface with accessibility improvements (skip link, ARIA labels, keyboard focus)
- Local vs Cloud Run FitTrack toggle
- Session context across turns
- Collapsible **MCP log** panel (JSON-RPC request/response trace)
- Suggestion chips and one-click Git/filesystem demo

## Deploy to Google Cloud Run

### FitTrack MCP (remote server)

```bash
cd fittrack-remote
deploy.bat YOUR_GCP_PROJECT_ID
```

### Chatbot host (optional public URL)

```bash
cd chatbot
deploy.bat
```

`deploy.bat` reads `DEEPSEEK_API_KEY` from `chatbot/.env` (not committed) and sets `FITTRACK_MODE=remote`.

## Course requirements checklist

- [x] Custom local MCP server (manual JSON-RPC, no MCP SDK)
- [x] Web chatbot host with LLM API (DeepSeek)
- [x] Session context across turns
- [x] MCP interaction log (visible in UI)
- [x] Official Filesystem + Git MCP servers
- [x] Remote MCP server on Cloud Run
- [x] Chatbot uses remote server the same way as local
- [x] Wireshark analysis with capture artifacts
- [x] Spanish report (`docs/REPORTE.md`)
- [x] Web UI with HCI improvements (+15% extra)

## Documentation

- FitTrack server: [`fittrack-mcp/README.md`](fittrack-mcp/README.md)
- Remote server: [`fittrack-remote/README.md`](fittrack-remote/README.md)
- Report (Spanish): [`docs/REPORTE.md`](docs/REPORTE.md)
- Capture files: [`capturas/`](capturas/)

## Presentation topics

- MCP architecture (host, client, server) and manual JSON-RPC implementation
- Four integrated MCP servers (FitTrack local/remote, Filesystem, Git)
- Wireshark layer analysis (link → network → transport → TLS) vs MCP log (application)
- Difficulties (stdio subprocess, Git repo bootstrap, TLS encryption in captures)
- Lessons learned and live demo flow
