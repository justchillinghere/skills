# Composition And Dependencies

Dependency injection is explicit and lightweight. Build concrete resources at process startup, store shared process resources on `app.state`, and pass dependencies into use cases or read repositories through typed dependency objects.

Do not add a DI container by default. FastAPI `Depends` belongs at the API edge, not inside domain or application code.

## Settings

Use nested Pydantic settings for clear environment ownership:

- `DatabaseSettings`
- optional `RedisSettings`
- `MetricsSettings`
- `WorkerSettings`
- external API settings as needed

Expose cached `get_settings()` so app creation, dependencies, tests, and scripts can share the same parsing behavior. Tests can clear the cache when they mutate environment variables.

See `assets/snippets/settings.py.snippet`.

## Lifespan Composition

Use FastAPI lifespan to create process-level resources:

- settings
- logging
- metrics server
- database engine/session factory
- Redis client when needed
- external HTTP clients
- worker stop event and worker tasks

Close resources after `yield` in reverse dependency order when practical.

## Use-Case Dependencies

Use cases should receive application-facing dependencies, not FastAPI `Depends` or concrete web request objects.

Typical shape:

```python
@dataclass(frozen=True)
class CreateUserDeps:
    session_factory: async_sessionmaker[AsyncSession]
    email_client: EmailClient


async def create_user(deps: CreateUserDeps, input: CreateUserInput) -> User:
    ...
```

Use a dependency dataclass when there is more than one dependency or when call sites become easier to read. For tiny use cases, explicit parameters are fine.

## API Dependencies

FastAPI dependencies adapt process resources into endpoint parameters. They usually read shared resources from `request.app.state`:

```python
def _get_create_user_deps(request: Request) -> CreateUserDeps:
    return CreateUserDeps(
        session_factory=request.app.state.db.session_factory,
        email_client=request.app.state.email_client,
    )


dep_create_user_deps = Depends(_get_create_user_deps)
```

Use the original dependency function as the test override key.

For simple read endpoints, API dependencies may provide a read repository or read-scoped UoW/session directly. Prefer that over a pass-through use case with no business behavior.

## Workers

Workers use the same dependency objects as API-backed use cases when possible. Build worker dependency objects in lifespan and pass them directly into `asyncio.create_task(...)`, worker loops, or batch processors.

## Scripts

Some projects start the server through a shell script to run preflight steps, migrations, or environment setup before `uvicorn`. This is fine. Keep the script thin and still point it at the app factory.
