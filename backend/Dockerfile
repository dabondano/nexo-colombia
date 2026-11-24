FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .

RUN useradd --create-home nexo
USER nexo

EXPOSE 8000
# Migrations run before the server starts (the stack has a single API instance).
# With NEXO_MIGRATION_DATABASE_URL set, they run as the owner, then the restricted
# application account gets its privileges (app.core.grants).
CMD ["sh", "-c", "alembic upgrade head && if [ -n \"$NEXO_MIGRATION_DATABASE_URL\" ]; then python -m app.core.grants; fi && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
