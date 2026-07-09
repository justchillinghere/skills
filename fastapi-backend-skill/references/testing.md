# Testing

Backend tests should verify behavior at the boundary where defects are likely. Pure business rules can be tested without Docker. Database, migration, cache, API, and worker integration behavior should use realistic local infrastructure.

## Default Test Structure

Mirror the source layout enough that each test has an obvious home.

```text
tests/
├── __init__.py
├── conftest.py                    # shared containers, settings, DB, app client
├── fixtures/                      # reusable factories and fakes
│   ├── __init__.py
│   ├── users.py
│   ├── <entity_factories>.py
│   └── <external_client_fakes>.py
├── api/
│   ├── conftest.py                # API auth/client helpers when needed
│   └── endpoints/
│       └── <feature>/
├── domain/
├── application/
│   ├── services/
│   └── use_cases/
├── infrastructure/
│   ├── repositories/
│   ├── redis/
│   └── http/
└── workers/
```

For a small service, keep fewer directories. Add structure when tests need it, not before.

## Test Levels

- Domain tests: pure Python objects and functions, no database.
- Application/use-case tests: verify orchestration, transaction behavior, domain rules, and port interactions.
- Service tests: focused business logic that would be hard to isolate through use cases.
- Repository tests: real PostgreSQL through testcontainers.
- API tests: FastAPI app created by `create_app()`, dependency overrides, and real database when persistence matters.
- Cache/lock tests: real Redis through testcontainers.
- Worker tests: call the worker operation/use case directly; test the infinite loop only for lifecycle behavior.

Prefer use-case tests for composition. Add separate service tests for focused edge cases, not to duplicate the same path.

## Test Intent

Each test should protect behavior owned by the application, not prove framework behavior. Do not add API tests whose only purpose is to show that Pydantic rejects an invalid enum value, forbids extra fields, parses required fields, or returns FastAPI's standard validation shape. One focused boundary test is enough when the project has custom error mapping or schema configuration worth protecting.

Avoid expanding one rule into many setup-heavy tests. If several inputs exercise the same branch, pick the smallest representative set unless the differences are domain behavior the code owns. Use `pytest.mark.parametrize` when it removes duplication across genuinely equivalent cases; do not use it to turn a small assertion into a table of obvious framework or helper behavior.

## Default Test Stack

Use:

- `pytest`
- `pytest-asyncio` with `asyncio_mode = "auto"`; no `@pytest.mark.asyncio` needed for normal async tests.
- `testcontainers` for PostgreSQL and Redis when integration behavior matters.
- Alembic `upgrade head` once per test session.
- FastAPI dependency overrides for API tests.

## Fixture Lifecycle

Root `tests/conftest.py` should provide the shared runtime test environment:

```text
session scope:
  start Postgres container
  optionally start Redis container
  set environment variables
  materialize Settings
  build Alembic config
  run Alembic upgrade head
  create async engine
  create async_session_factory

function scope:
  create AsyncSession when a test asks for it
  run the test
  clean database state after the test

api tests:
  create app with test lifespan
  override dependencies
  yield client
  clear overrides
```

Common root fixtures:

- `postgres_container`
- optional `redis_container`
- `settings`
- `alembic_config`
- `alembic_upgrade`
- `async_engine`
- `async_session_factory`
- `async_db`
- automatic cleanup fixture
- `api_client`

If tests mutate environment variables before materializing settings, call `get_settings.cache_clear()` before reading settings again.

Feature-specific `conftest.py` files and `tests/fixtures/` modules should provide domain factories, auth helpers, UoW/session factories, and fake external clients.

## Database Isolation

Prefer truncating all tables after each integration test:

```sql
TRUNCATE TABLE <all tables> RESTART IDENTITY CASCADE
```

Rollback-only isolation is often insufficient when the app or use case opens a separate session. Truncation gives each test a clean database even when factories commit data for cross-session visibility.

## Factories

Use async factory fixtures for persisted entities. Factories should:

- accept explicit overrides for fields relevant to the test
- set realistic defaults for everything else
- commit when other sessions need to read created data
- return domain objects or ORM objects consistently for that project
- avoid hiding important setup that the assertion depends on

Always `await` async factories.

When using factory-created ORM objects, save generated IDs and values before later DB operations:

```python
user = await user_factory(email="a@example.com")
user_id = user.id
```

SQLAlchemy objects can become stale after commits, truncation, or use of other sessions.

Before creating a new reusable fixture, search existing `conftest.py` files and `tests/fixtures/`.

## Raw ORM Seeding

Prefer factories for normal setup. Raw ORM writes are acceptable in repository tests or when testing persistence internals.

Use `flush()` for generated IDs and `commit()` before reading through another session:

```python
async_db.add(row)
await async_db.flush()
row_id = row.id
await async_db.commit()
```

If Arrange and Act share the same session, commit may not be needed.

## Transaction Tests

When the project uses a UoW, use the async context manager:

```python
async with uow:
    result = await uow.users.get(user_id)
```

Do not call UoW repositories before entering the UoW. The UoW manages session and transaction lifecycle.

When code under test needs to create its own UoW, pass a `uow_factory` fixture rather than a single already-entered UoW.

When the project uses explicit sessions/connections, test with the same transaction style as production code. Pass the active session/connection into repository functions or lightweight repository objects, and commit setup data before another session needs to read it.

## API Tests

Build the app through `create_app()` with a test lifespan. Override dependencies by function object:

```python
app.dependency_overrides[_get_create_user_deps] = lambda: fake_create_user_deps
app.dependency_overrides[get_settings] = lambda: settings
```

Override auth/user dependencies with helper fixtures when auth exists. Clear overrides after the test.

Assert both status code and response body. Use exact values.

## External Systems

- Use real PostgreSQL for repository and migration behavior.
- Use real Redis for cache, lock, queue, and rate-limit behavior.
- Use fakes/stubs for third-party APIs.
- Let fakes track calls so tests can assert expected external interactions.
- Avoid `unittest.mock.patch` for internal modules when constructor/factory injection is possible.

## Time And Determinism

Do not assert against `datetime.now()` unless time is explicitly controlled. Use deterministic timestamps as fixture inputs.

Database-generated timestamps come from PostgreSQL, not Python. Python time-freezing libraries do not affect `server_default` values.

## Naming And Assertions

Name tests by action, scenario, and expected outcome:

```python
async def test_create_user_existing_email_returns_conflict(...):
    """
    Arrange: existing user with the requested email.
    Act: create a user with the same email.
    Assert: conflict is returned and no duplicate user is stored.
    """
```

Assert exact expected values. Avoid weak checks like `is not None`, `len(result) > 0`, or only checking status code when the response body matters.

## Pitfalls

- Forgetting to await async factories.
- Calling UoW repositories outside `async with` when the project uses UoW.
- Expecting uncommitted setup data to be visible to another session.
- Accessing stale ORM attributes after session changes.
- Mocking internal modules instead of injecting fakes.
- Duplicating fixture setup instead of promoting reusable factories.
- Testing the same behavior at service, use-case, and API levels without a distinct reason.
- Testing Pydantic, FastAPI, enum, or pytest behavior instead of application behavior.
