# Web application and API in one container, for one free Render web service
# (docs/07-deployment-render-neon.md). Build context: the repository root.

FROM node:22-slim AS web
WORKDIR /web
RUN corepack enable
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm build

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy \
    PATH="/app/api/.venv/bin:$PATH" \
    NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 \
    NEXO_API_URL=http://127.0.0.1:8000 \
    NODE_OPTIONS=--max-old-space-size=256
# Node.js runtime for the web server (a single binary plus the C++ runtime).
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=node:22-slim /usr/local/bin/node /usr/local/bin/node

WORKDIR /app/api
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /usr/local/bin/uv
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev
COPY backend/ ./

WORKDIR /app/web
COPY --from=web /web/.next/standalone ./
COPY --from=web /web/.next/static ./.next/static

COPY deploy/render/start.sh /app/start.sh
RUN useradd --create-home nexo && chown -R nexo /app/web
USER nexo
WORKDIR /app
EXPOSE 10000
CMD ["/app/start.sh"]
