# API Patterns

FastAPI is the HTTP boundary of the service. It should translate HTTP into application calls and translate application results back into HTTP.

## App Factory

Expose a `create_app()` function. This lets tests create the app with dependency overrides and avoids import-time side effects.

```python
def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    return app
```

When running with Uvicorn, use the app factory form, for example `uvicorn app.main:create_app --factory`.

Do not create database engines, Redis clients, HTTP clients, or worker tasks when the module is imported.

## Lifespan

Use `lifespan` for resources that live for the whole process:

- logging configuration
- metrics server
- database engine/session factory
- Redis client
- external HTTP clients
- worker tasks and shutdown events

Create resources before `yield`; close them after `yield`.

## Routers

Use `api/router.py` to include feature routers. Endpoint modules expose a router but do not include themselves in the app.

```text
api/
├── router.py
├── deps.py
├── endpoints/
│   └── users.py
└── schemas/
    └── users.py
```

Endpoint functions should:

- receive request schemas, query params, path params, and dependencies
- call a use case for application behavior, or a repository method for a simple read query
- map expected application errors to `HTTPException`
- return response schemas

Endpoint functions should not:

- open database sessions directly
- run SQLAlchemy queries
- call third-party HTTP APIs directly
- contain multi-step business workflows

Do not create pass-through use cases for endpoints that only read data. If an endpoint validates HTTP input, calls one repository/view method, and maps the result to a response, keep it as a read path through the API dependency and repository boundary. Add a use case only when the read path has real application behavior, such as authorization decisions beyond dependencies, combining multiple data sources, business-rule enforcement, or non-trivial error decisions.

## Dependencies

FastAPI dependencies adapt app-level resources into endpoint parameters. Keep `Depends` at the API edge; application use cases should receive normal Python arguments or dependency dataclasses.

```python
def _get_create_user_deps(request: Request) -> CreateUserDeps:
    return CreateUserDeps(
        session_factory=request.app.state.db.session_factory,
        email_client=request.app.state.email_client,
    )


dep_create_user_deps = Depends(_get_create_user_deps)
```

Use the original dependency function as the test override key.

```python
app.dependency_overrides[_get_create_user_deps] = lambda: fake_deps
```

## Schemas

Keep Pydantic request/response models in `api/schemas/`. These are HTTP contracts, not domain entities.

Map explicitly between API schemas and domain/application objects. This keeps API compatibility decisions separate from business modeling.

## Errors

Use domain/application errors for expected business failures. Convert them to HTTP status codes at the API boundary.

Do not raise `HTTPException` from domain or application code.
