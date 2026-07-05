# backend/Dockerfile
# Multi-stage build for the Abhyas FastAPI backend

# ---- Builder stage ----
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---- Final stage ----
FROM python:3.11-slim AS final

WORKDIR /app

# Runtime dependency needed by psycopg2 / libpq at runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 appuser

# Bring in the installed Python packages from the builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY ./app ./app
COPY alembic.ini ./alembic.ini
COPY ./alembic ./alembic

RUN chown -R appuser:appuser /app /home/appuser/.local

USER appuser

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
