# Backend architecture lens

Review rules for Python backend changes. This file is the lens: what to look for. The finding
discipline, severity scale, and delivery are the harness's job (see the `review-swarm`
SKILL.md) — do not restate them here.

This lens is stack-specific. Before forming findings, read the two sibling skills it depends
on and apply their guidance; do not reconstruct it from memory:

- `fastapi-backend-skill` — backend structure and layering.
- `dignified-python` — Python style and interface rules.

Also reconstruct intent first: read the plan the caller passed (if any), the diff, nearby
tests, and the local code style. Existing local style is evidence of intent, not a waiver for
bugs, security holes, or bad boundaries.

## What to look for

Assign each finding to one primary topic.

- **Bugs & behavior** — incorrect behavior, edge cases, data state, concurrency, time
  handling, idempotency, error handling.
- **Architecture & boundaries** — module ownership; domain / application / infrastructure /
  API separation; transaction ownership; use-case shape; dependency direction.
- **FastAPI alignment** — router and dependency shape, repository ownership, database access,
  migrations, worker composition, testcontainers, metrics.
- **Dignified Python alignment** — function and interface design, typing, imports, exception
  boundaries, defaults, LBYL flow, pathlib, module-level behavior.
- **Security & data exposure** — authn/authz, tenant isolation, secrets, PII masking, input
  validation, unsafe SQL, logging sensitive data.
- **Tests** — missing coverage, weak assertions, wrong test level, brittle fixtures, no
  regression test for changed behavior.
- **Maintainability & local fit** — unnecessary indirection, mismatch with local style,
  duplicated mapping, confusing naming, unclear reuse, overly clever code.

## Backend-specific rules

- Flag SQLAlchemy, Redis, HTTP clients, or FastAPI details leaking into domain or application
  code when it creates ownership or testability risk.
- Do not require a use case for a simple read query only to satisfy layering.
- Watch newly added private helpers, one-line wrappers, schema mappers, and pass-through
  functions. Keep them only when they improve reuse, semantic naming, isolation, or
  testability.
- If a guideline conflicts with an explicit plan or local design decision, raise it as a
  Question, not a finding.
