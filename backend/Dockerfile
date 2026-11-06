# MyFarm AI Backend — production-style image
# Installs dependencies from pyproject.toml + uv.lock (frozen), runs as non-root.

FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv

WORKDIR /app

# Dependencies first for layer caching; --frozen enforces uv.lock.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Application code + migrations
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN uv sync --frozen --no-dev

# Non-root runtime user — chown only the writable data dir; the venv and
# code stay root-owned (read-only for the app). A `chown -R /app` here would
# duplicate the whole venv into a new image layer (~120 MB).
RUN useradd --system --uid 10001 --no-create-home appuser \
    && mkdir -p /app/data \
    && chown appuser:appuser /app/data
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=3)"]

CMD ["/app/.venv/bin/uvicorn", "app.main:get_default_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
