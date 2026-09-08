FROM python:3.11-slim

WORKDIR /app

COPY server/ /app/server/
COPY http_server.py /app/http_server.py

RUN mkdir -p /app/data

ENV FITTRACK_DATA_DIR=/app/data
ENV PORT=8080

EXPOSE 8080

CMD ["python", "http_server.py"]
