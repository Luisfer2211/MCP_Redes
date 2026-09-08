# FitTrack MCP — Remote HTTP Server

Hand-written JSON-RPC 2.0 over HTTP for Google Cloud Run deployment.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/mcp` | JSON-RPC 2.0 (same methods as local stdio server) |

## Local test

```bash
# Copy shared modules (or run deploy.bat which does this)
copy ..\fittrack-mcp\server\tools.py server\
copy ..\fittrack-mcp\server\protocol.py server\

set FITTRACK_DATA_DIR=.\data
set PORT=8090
python http_server.py
```

Test:

```bash
curl http://localhost:8090/health
```

## Deploy to Google Cloud Run

**Prerequisites:** GCP project with billing enabled, `gcloud` CLI authenticated.

```bash
deploy.bat YOUR_GCP_PROJECT_ID
```

Or:

```bash
gcloud config set project YOUR_GCP_PROJECT_ID
gcloud run deploy fittrack-mcp --source . --region us-central1 --allow-unauthenticated
```

After deploy, copy the service URL to `chatbot/.env`:

```
FITTRACK_REMOTE_URL=https://fittrack-mcp-xxxxx-uc.a.run.app
FITTRACK_MODE=remote
```

## Note on billing

If deploy fails with `BILLING_DISABLED`, enable billing at:
https://console.developers.google.com/billing/enable?project=YOUR_PROJECT_ID

Cloud Run free tier covers light usage for course demos.
