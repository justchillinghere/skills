FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS base

ARG BACKEND_PORT=8000
EXPOSE ${BACKEND_PORT}

ENV PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PYTHONPATH=/app/src:/app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    ca-certificates \
    bash \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    UV_COMPILE_BYTECODE=1 uv sync --frozen --no-dev --no-install-project

FROM base AS dev
COPY . /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    UV_COMPILE_BYTECODE=1 uv sync --frozen --dev
CMD ["uv", "run", "uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS prod
COPY . /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    UV_COMPILE_BYTECODE=1 uv sync --frozen --no-dev
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser
CMD ["uv", "run", "uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

