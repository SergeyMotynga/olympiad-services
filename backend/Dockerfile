FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.7 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./
COPY runtime ./runtime
COPY access ./access
COPY tasks-print ./tasks-print
COPY submissions ./submissions
COPY migrations ./migrations

ARG SERVICE
ARG APP_MODULE
RUN uv sync --locked --no-dev --package "olympiad-${SERVICE}"

WORKDIR /app/${SERVICE}
ENV APP_MODULE=${APP_MODULE}
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn \"$APP_MODULE\" --host 0.0.0.0 --port 8000"]
