FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY app/ ./app/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY app/ ./app/
COPY database/ ./database/
COPY docs/ ./docs/

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=app \
    DB_HOST=db \
    DB_PORT=5432 \
    DB_USER=buska_user \
    DB_PASSWORD=buska_pass \
    DB_NAME=buska_db

# Gunicorn concurrency. Load testing showed this workload is CPU-bound on the
# 2-vCPU allocation (heavy JSON serialization + bcrypt on login), so adding
# workers or threads beyond a small number only thrashes the two cores and
# collapses latency — threaded (gthread) workers were the worst, and 2-4 plain
# sync workers were the sweet spot (see loadtest/REPORT.md). The real lever for
# more capacity is more vCPUs, not more workers. Kept as sync/4 (the validated
# optimum for 2 vCPU) but overridable so capacity can be re-tuned per host size
# without rebuilding — e.g. bump GUNICORN_WORKERS to ~2x vCPU on a larger box.
ENV GUNICORN_WORKERS=4 \
    GUNICORN_THREADS=1 \
    GUNICORN_WORKER_CLASS=sync \
    GUNICORN_TIMEOUT=120

EXPOSE 5000

# JSON-array + `sh -c` so ${GUNICORN_*} expand at runtime; `exec` so gunicorn
# replaces the shell as PID 1 and receives SIGTERM for graceful shutdown on
# deploy. A plain shell-form CMD leaves /bin/sh as PID 1, which does not
# forward SIGTERM — Docker then SIGKILLs gunicorn after the stop timeout.
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:5000 --workers ${GUNICORN_WORKERS} --threads ${GUNICORN_THREADS} --worker-class ${GUNICORN_WORKER_CLASS} --timeout ${GUNICORN_TIMEOUT} 'app:create_app()'"]
