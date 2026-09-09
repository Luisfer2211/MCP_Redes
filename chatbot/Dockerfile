FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py deepseek_client.py mcp_client.py mcp_manager.py ./
COPY static/ ./static/

RUN mkdir -p workspace/demo-repo

ENV PORT=8080
ENV FITTRACK_MODE=remote
ENV FITTRACK_REMOTE_URL=https://fittrack-mcp-907980440492.us-central1.run.app

EXPOSE 8080

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
