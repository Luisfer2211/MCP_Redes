# MCP_Redes — CC3067 Project 1 (Complete)

Repository for **CC3067 Redes** (Universidad del Valle de Guatemala), Project 1: *Use of an existing protocol* (MCP / JSON-RPC 2.0).

**Author:** Luis Palacios — Carnet 23933

## Project components

| Path | Description |
|------|-------------|
| [`fittrack-mcp/`](fittrack-mcp/) | Custom local FitTrack MCP server (stdio, hand-written JSON-RPC) |
| [`fittrack-remote/`](fittrack-remote/) | Same server over HTTP for Google Cloud Run |
| [`chatbot/`](chatbot/) | Web chatbot host (DeepSeek + MCP clients + interaction log) |
| [`docs/`](docs/) | Report template (Spanish) + Wireshark guide |

## Architecture

```
Web UI  →  FastAPI host  →  DeepSeek API
                ↓
    MCP clients (manual JSON-RPC)
    ├── FitTrack (local stdio or remote HTTP)
    ├── Filesystem MCP (official, npx)
    └── Git MCP (official, mcp-server-git via pip)
```

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

## Deploy remote server (Google Cloud Run)

```bash
cd fittrack-remote
deploy.bat YOUR_GCP_PROJECT_ID
```

Or manually:

```bash
gcloud run deploy fittrack-mcp --source . --region us-central1 --allow-unauthenticated
```

Set `FITTRACK_REMOTE_URL` in `chatbot/.env` to the deployed URL.

## Course requirements checklist

- [x] Custom local MCP server (manual JSON-RPC)
- [x] Web chatbot host with LLM API (DeepSeek)
- [x] Session context across turns
- [x] MCP interaction log (visible in UI)
- [x] Official Filesystem + Git MCP servers
- [x] Remote MCP server on Cloud Run
- [x] Wireshark guide + report template (Spanish)

## Documentation

- FitTrack server: [`fittrack-mcp/README.md`](fittrack-mcp/README.md)
- Report (Spanish): [`docs/REPORTE.md`](docs/REPORTE.md)
- Wireshark guide: [`docs/WIRESHARK_GUIA.md`](docs/WIRESHARK_GUIA.md)

## Presentation topics

- Features implemented (chatbot, 4 MCP servers, local + remote)
- Difficulties (manual JSON-RPC, stdio vs HTTP, TLS in Wireshark)
- Lessons learned
