# Architecture

This backend style separates business behavior from the frameworks and tools used to run it.

## Conceptual Model

The service has three kinds of code:

- Entry points receive work: HTTP endpoints, workers, local commands.
- Application code decides what the service should do: use cases, services, transactions.
- Infrastructure code knows how to talk to outside systems: PostgreSQL, Redis, HTTP APIs, files, queues.

Entry points should be thin. Infrastructure should be replaceable. Application and domain code should remain understandable without knowing FastAPI or SQLAlchemy.

## Dependency Rule

Dependencies point inward:

```text
api/ or workers
  -> application/
      -> domain/
      -> application/ports/

infrastructure/
  -> application/ports/
  -> domain/

main.py
  -> all layers, because it wires the process together
```

The application layer defines what it needs through ports. Infrastructure implements those ports. The composition root creates concrete objects and passes them in.

## Package Ownership

Use one bounded context by default:

```text
src/<package>/
├── main.py
├── settings.py
├── api/
├── domain/
├── application/
├── infrastructure/
├── metrics/
├── populate/
└── utils/
```

### `main.py`

Owns process composition:

- create the FastAPI app
- configure logging
- start Prometheus metrics server
- create settings
- create database/session factories
- create Redis and HTTP clients
- create worker dependency bundles and worker tasks
- close resources during shutdown

This file is allowed to import concrete infrastructure because it is the place where dependency inversion is resolved.

### `settings.py`

Owns environment parsing through Pydantic settings. Keep settings grouped by concern when the app grows, for example database, Redis, metrics, workers, and external APIs.

### `api/`

Owns HTTP-specific code:

- routers and endpoint modules
- request and response schemas
- FastAPI dependency functions
- auth dependencies
- HTTP error mapping

Endpoint functions should not contain SQL queries or business workflows.

### `domain/`

Owns business concepts. Use this layer for entities, value objects, domain errors, and pure rules.

Domain code should not import FastAPI, SQLAlchemy, Redis, Pydantic API schemas, or external client libraries.

Domain objects should be focused. They can contain validation, normalization, derived properties, primitive conversion, and small state transitions. They should not orchestrate long workflows, open transactions, call repositories, or call external services.

Avoid both extremes:

- Do not make every domain object a passive bag of fields when a rule naturally belongs on the object.
- Do not make domain objects so large that they coordinate multiple repositories, clients, or process-level concerns.

### `application/`

Owns use cases and service orchestration. Use cases coordinate domain behavior and ports. They decide transaction boundaries and call repositories or external-service ports.

Use explicit dependency objects or parameters. Avoid hidden global clients.

Prefer use cases as async functions. A use case is an application action called by an API endpoint, worker, or command. Use an input dataclass for caller data and a dependency dataclass or explicit parameters for dependencies when that improves readability.

Do not wrap a simple read query in a use case only to satisfy layering. A use case represents application behavior: business decisions, orchestration, state changes, transaction decisions, calls across multiple ports, or expected domain/application errors.

Use a class for a use case only when it has real state, multiple related methods, lifecycle behavior, or reusable internal helpers that are clearer as an object. Avoid classes whose only purpose is `__init__(deps)` plus one `execute()` method.

Use application services for reusable behavior shared by multiple use cases or cohesive logic that would make a use case too large. Do not extract a service only to make a small use case look artificially thin.

Expected application errors should be application/domain exceptions. Convert them to HTTP errors in `api/`, not inside the use case.

### `infrastructure/`

Owns concrete adapters:

- SQLAlchemy models, repositories, and transaction/session helpers
- Redis caches, locks, and queues
- HTTP clients for third-party services
- file/object storage clients
- queue consumers/producers

Infrastructure code can know about SQLAlchemy, Redis, HTTPX, and wire protocols.

Repositories may be classes or modules of functions. Use classes when they carry a session/connection or group a cohesive interface. Use functions when passing the active session/connection explicitly is clearer and avoids boilerplate.

Repositories return domain objects, read DTOs, or explicit command/query DTOs. They should not leak SQLAlchemy ORM models into `application/` or `api/`.

Simple read endpoints may call a repository or dedicated read repository directly through API dependencies or a read-scoped UoW/session. Keep query shape, joins, filtering, and row-to-read-model mapping in infrastructure. Large SQL-backed views are still read repositories by default, not use cases.

### `metrics/`

Owns Prometheus metric definitions and helpers. Keep high-cardinality values out of labels.

### `populate/`

Optional local/dev seeding commands. Do not mix populate scripts with runtime application behavior.

### `utils/`

Small helpers only. Do not let `utils/` become a second `core/`.

## Background Workers

Workers are entry points just like HTTP endpoints. A worker loop should be thin: receive a tick/message, call an application use case, log the outcome, and respect graceful shutdown.

Do not put worker business behavior directly in the loop.

## Ports

Ports describe dependencies that application code needs from the outside world.

Prefer ABCs for owned interfaces where missing methods should fail loudly during implementation, such as repositories or transaction/session abstractions.

Prefer Protocols for structural interfaces, third-party API clients, test fakes, or adapters where explicit inheritance is unnecessary.

The exact mechanism is less important than the boundary: application code should depend on an interface shape, not on concrete SQLAlchemy repositories, Redis clients, or HTTP clients.

## DTO Boundaries

Keep DTO categories explicit:

- API schemas: request and response contracts under `api/schemas/`.
- Use-case input/dependency DTOs: application boundary objects, often dataclasses.
- Domain objects and value objects: business concepts and invariants.
- Repository command DTOs: create, patch, filter, and persistence command shapes.
- Read DTOs/read models: query-specific shapes for large joined views or API-friendly reads.
- ORM models: infrastructure only.

Do not use ORM models as application DTOs. If a query does not naturally return a domain object, return a named read DTO.

## Transaction Styles

Application behavior code should own transaction boundaries. Simple read-only paths may use an API dependency or read-scoped UoW/session boundary when there is no use case. Two styles are acceptable for behavior that belongs in application code.

Style A: Unit of Work

- pass a UoW or UoW factory into the use case
- enter it in the use case
- access repositories through it
- commit or rollback through the UoW

Style B: Explicit session or connection

- acquire a database session/connection near the use-case boundary
- open the transaction explicitly in the use case
- pass the active session/connection to repository functions or lightweight repository objects
- commit or rollback at the use-case boundary

Choose the simpler style for the project. UoW is useful when many repositories are grouped behind one transaction abstraction. Explicit session/connection is fine when it makes transaction ownership clearer.

In both styles:

- repositories do not secretly create unrelated transactions
- SQLAlchemy remains an infrastructure detail
- repositories map ORM rows to domain objects or read DTOs
- API handlers do not use ORM models as business objects
