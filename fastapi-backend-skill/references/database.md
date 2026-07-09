# Database

This skill assumes PostgreSQL with async SQLAlchemy at runtime and Alembic for migrations.

## Runtime Access

Create the async engine and session factory during process startup, usually in `lifespan`.

```python
engine = create_async_engine(settings.database.database_url, pool_pre_ping=True)
session_factory = async_sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)
```

Dispose the engine during shutdown.

Do not share one `AsyncSession` across concurrent tasks. Sessions are operation-scoped: one request, one use case call, one read query path, or one worker operation.

## Transaction Styles

Application behavior code should own transaction boundaries. Simple read-only paths may use an API dependency or read-scoped UoW/session boundary when there is no use case. Use either a Unit of Work or an explicit session/connection style for behavior that belongs in application code.

### Unit Of Work

A UoW groups repositories under one session and transaction.

Responsibilities:

- create or receive an `AsyncSession`
- begin a transaction
- expose repositories
- commit on success
- rollback on failure
- close the session

Use cases should call it like:

```python
async with uow:
    entity = await uow.users.get(user_id)
    await uow.users.save(entity)
```

Repositories do not commit when a UoW owns the transaction.

### Explicit Session Or Connection

For simpler projects, a use case may receive or acquire an active session/connection and open the transaction directly:

```python
async with session_factory() as session:
    async with session.begin():
        entity = await user_repository.get(session, user_id)
        await user_repository.save(session, entity)
```

Repository modules may expose functions that accept the active session/connection. This is acceptable when it makes transaction ownership clearer and avoids a thin repository class that only stores one session.

Do not mix independent hidden transactions inside repositories with use-case-level transaction management.

For read-only endpoints with no application behavior, it is acceptable for the API dependency or read-scoped UoW/session boundary to provide the active session and repository directly. Do not invent a use case that only forwards to one repository method.

## Repositories

Repositories translate between persistence and application/domain objects. They receive an active `AsyncSession` directly or through a UoW.

Repository methods should return domain objects, read models, or explicit DTOs. Avoid leaking ORM objects into API handlers or use cases unless the module is intentionally infrastructure-only.

Keep ORM mapping explicit and local to infrastructure. Use named mapper functions or methods such as `_to_domain(orm)`, `_to_orm(domain)`, or `_row_to_read_model(row)` when conversion has any logic. This is especially important for JSON columns, enums, value objects, nested dataclasses, money/time units, and query-specific read DTOs.

Avoid scattering mapping logic across use cases or API handlers. If several repositories need the same conversion, move it to a small infrastructure mapper module.

See `assets/snippets/database.py.snippet` for a small async database wrapper.

## Alembic

Use Alembic for all schema changes.

Default setup:

- runtime app URL may use an async driver
- Alembic may convert/use a sync PostgreSQL driver for migrations, for example `postgresql+psycopg_async://` to `postgresql+psycopg://`
- `alembic/env.py` imports all model modules so `target_metadata` is complete

Expected commands:

```bash
just revision "message"
just upgrade
just downgrade
just current
just history
```

Review generated migrations before accepting them. Check indexes, constraints, nullability, data migration steps, and downgrade behavior.

See `assets/snippets/alembic_env.py.snippet` for a minimal sync Alembic setup that reads the sync URL from settings and imports models for autogenerate.
