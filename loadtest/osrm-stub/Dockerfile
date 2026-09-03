FROM python:3.12-slim

WORKDIR /app
COPY server.py ./server.py

ENV PORT=5001 \
    STUB_LATENCY_MS=40 \
    STUB_LATENCY_JITTER_MS=30 \
    STUB_ERROR_RATE=0

EXPOSE 5001

CMD ["python", "server.py"]
