FROM python:3.12-slim AS builder

# uv fijado a una version exacta para que el build sea reproducible
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /usr/local/bin/uv

WORKDIR /app

ENV UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

# Capa de dependencias: solo cambia si cambian pyproject.toml o uv.lock.
# --locked falla si uv.lock no coincide con pyproject.toml (no resuelve versiones nuevas).
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project

COPY App ./App
RUN uv sync --locked --no-dev

FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

RUN groupadd --system app \
	&& useradd --system --gid app --no-create-home appuser \
	&& chown -R appuser:app /app

COPY --from=builder --chown=appuser:app /opt/venv /opt/venv
COPY --from=builder --chown=appuser:app /app/App ./App

USER appuser
EXPOSE 8000
CMD ["uvicorn", "App.main:app", "--host", "0.0.0.0", "--port", "8000"]
