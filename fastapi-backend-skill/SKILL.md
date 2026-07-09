---
name: fastapi-backend-skill
description: Build, scaffold, evolve, and maintain async FastAPI backend services using uv, src-layout Python, Docker, PostgreSQL, optional Redis, Alembic migrations, SQLAlchemy async sessions, pytest/testcontainers, structured logging, Prometheus metrics, background workers, and clean architecture layering. Use when creating a new FastAPI backend, adding API endpoints, use cases, repositories, migrations, workers, Docker/just commands, tests, fixtures, factories, or backend project structure guidance.
---

# FastAPI Backend

Use this skill to build backend-only FastAPI services. It describes the default project style from first principles without assuming knowledge of any existing repository. Local project docs and explicit user instructions override these defaults.

## Backend Model

A backend service is a long-running process that accepts external inputs, runs application behavior, and talks to infrastructure.

Inputs usually come from:

- HTTP requests handled by FastAPI routers.
- Background workers that run periodically or consume queues.
- Local/dev commands such as migrations or populate scripts.

The service should keep business behavior independent from transport and infrastructure. HTTP, SQLAlchemy, Redis, and external HTTP clients are details at the edge of the system; use cases and domain rules should be testable without starting FastAPI or Docker.

## Request Flow

Default HTTP flow:

```text
HTTP request
  -> FastAPI router and Pydantic request schema
  -> API dependency functions provide settings, transaction/session access, auth/user, clients
  -> application use case coordinates behavior, or API calls a read repository for a simple query
  -> domain objects enforce business rules when behavior exists
  -> infrastructure adapters perform database/cache/external API calls
  -> API layer maps result to Pydantic response schema or HTTP error
```

Default worker flow:

```text
worker tick / queue message
  -> worker dependency bundle built at process startup
  -> application use case coordinates work
  -> infrastructure adapters perform database/cache/external API calls
  -> worker logs result and continues, retries, or stops gracefully
```

## Layer Responsibilities

- `api/`: FastAPI routers, request/response schemas, dependency functions, HTTP error mapping.
- `domain/`: business entities, value objects, invariants, domain errors. No FastAPI, SQLAlchemy, Redis, or HTTP client imports.
- `application/`: use cases, application services, ports/interfaces, transaction boundaries for real application behavior. No FastAPI route objects and no concrete infrastructure clients.
- `infrastructure/`: SQLAlchemy models, repositories, transaction helpers, Redis implementations, external API clients, concrete adapter code.
- `metrics/`: Prometheus metric definitions and middleware helpers.
- `main.py`: process composition: create settings, logging, FastAPI app, lifespan resources, clients, DB pools, metrics server, and worker tasks.
- `settings.py`: Pydantic settings and environment parsing.

Do not create a generic `core/` package by default. If a module does not have a clear owner, decide whether it is composition (`main.py`), configuration (`settings.py`), infrastructure (`infrastructure/`), API boundary (`api/`), or a small utility (`utils/`).

## Default Layout

Use one bounded context until the domain clearly needs multiple contexts.

```text
<repo>/
├── Dockerfile
├── docker-compose.yml
├── justfile
├── pyproject.toml
├── alembic.ini
├── alembic/
├── src/<package>/
│   ├── __init__.py
│   ├── main.py
│   ├── settings.py
│   ├── api/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   ├── metrics/
│   ├── populate/            # optional
│   └── utils/               # small cross-cutting helpers only
└── tests/
```

## Defaults

- Use `uv`, `pyproject.toml`, and `src/` layout.
- Use async FastAPI, async SQLAlchemy runtime, PostgreSQL, Alembic migrations, and optional Redis.
- Use sync Alembic migration connections by default while keeping app runtime database access async.
- Use `lifespan` for startup/shutdown resources and graceful cleanup.
- Use explicit dependency objects and composition in `main.py`; do not add a DI container by default.
- Use `logging.config.dictConfig` and Prometheus HTTP metrics by default.
- Expose Prometheus metrics on port `9000` unless the project says otherwise.
- Include worker guidance in backend design. Scaffold workers when the app needs periodic jobs, queue consumers, polling, outbox processing, reconciliation, or cleanup tasks.
- Use pytest, pytest-asyncio, testcontainers, Alembic test setup, fixtures, and factories.
- Treat auth, CORS, rate limiting, custom OpenAPI, and provider-specific integrations as project-local concerns unless explicitly requested.

## Existing Projects

When modifying an existing backend, first read local docs such as `AGENTS.md`, `CLAUDE.md`, and project-local skills. Inspect `pyproject.toml`, `justfile`, Docker files, `src/`, and `tests/conftest.py`. Prefer existing recipes over raw commands and preserve the current layout unless the task explicitly asks for restructuring.

## Add A Feature

Use this path for a typical endpoint-backed feature. Tests may be written before implementation or alongside it, but plan test cases before changing the implementation.

1. Define the behavior: request/response shape, business rules, persistence changes, external calls, errors, and worker effects.
2. Plan tests at the right levels: domain, use case, repository, API, and worker tests as needed.
3. Add or update domain objects, value objects, and read/command DTOs.
4. Add or update application use-case input/dependency DTOs and the async use-case function when the feature has real application behavior.
5. Add or update ports for repositories or external clients.
6. Implement infrastructure adapters and SQLAlchemy mappings; add an Alembic migration for schema changes.
7. Add API schemas, endpoint, router wiring, and dependency functions at the API edge.
8. Add worker wiring when the feature needs periodic or queued work.
9. Run focused tests and project lint/format recipes; run migration commands when schema changes.

## Pitfalls

- Do not create a generic `core/` package as a dumping ground.
- Do not put SQLAlchemy models, Redis clients, FastAPI objects, or concrete HTTP clients in `domain/` or `application/`.
- Do not create DB engines, Redis clients, HTTP clients, worker tasks, or settings objects at module import time.
- Do not let repositories create hidden transactions when the use case owns the transaction boundary.
- Do not wrap a simple read query in a use case only to satisfy layering.
- Do not use raw request URLs or user/resource IDs as Prometheus labels.
- Do not add Redis to backend `depends_on` unless the backend uses Redis.
- Do not mock database/cache behavior; use testcontainers for repository/cache integration tests.
- Do not duplicate test setup; promote reusable setup to factories and fixtures.
- Do not add CI, Kubernetes, provider-specific sidecars, or domain-specific auth to the generic backend structure.

## Detailed References

Read only what the task needs:

- `references/architecture.md`: conceptual model, dependency direction, package ownership, domain/application shape, ports, DTOs, and transaction styles.
- `references/composition.md`: settings, lifespan composition, explicit dependency objects, API dependency functions, and no-container dependency injection.
- `references/api-patterns.md`: app factory, lifespan, routers, dependencies, schemas, errors.
- `references/database.md`: async SQLAlchemy runtime, transaction styles, repositories, Alembic migration defaults.
- `references/testing.md`: pytest-asyncio, testcontainers, test directory structure, conftest layering, fixtures, factories, transaction tests, API clients, fakes, and assertion rules.
- `references/docker-just.md`: Docker Compose, Dockerfile, uv, just commands.
- `references/observability-workers.md`: dictConfig logging, Prometheus middleware, worker lifecycle.

Reusable starter snippets live in `assets/snippets/`, including `settings.py.snippet`, `database.py.snippet`, `use_case.py.snippet`, `endpoint.py.snippet`, `worker.py.snippet`, `batch_worker.py.snippet`, and `alembic_env.py.snippet`.
