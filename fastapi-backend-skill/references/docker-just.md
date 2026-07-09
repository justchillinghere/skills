# Docker And Just

## Default Services

Default development stack:

- backend
- PostgreSQL
- Redis only when the app needs caching, locks, queues, rate limits, or shared ephemeral state

Do not copy project-specific sidecars, CI, or Kubernetes deployment files into generic projects.

## Dockerfile

Use one backend Dockerfile with `base`, `dev`, and `prod` stages. Use `uv sync --frozen`; mount source files in dev through Compose.

Keep production images non-root and avoid installing dev dependencies in the prod stage.

Use the `prod` target locally when verifying that the production image starts without bind mounts or dev dependencies.

## Compose

Use Compose for local development. Include healthchecks and `depends_on.condition: service_healthy` for Postgres and Redis when the backend depends on them.

Make Redis optional: do not add a backend dependency on Redis unless the app actually uses Redis.

In dev, bind-mount `src/` and run Uvicorn with reload, either directly in Compose or through a thin start script. Compose should load `.env` through `--env-file`; `just` may also use `set dotenv-load := true` so recipes and Compose read the same local configuration.

## Just Commands

Baseline commands:

```just
docker-up
docker-down
docker-clean
docker-build
docker-logs
logs-service service
revision message
upgrade
downgrade
history
current
test
ruff-format
ruff-check
```

Prefer `just` recipes as the stable interface. Internal commands may evolve, but agents should run the recipe names.
