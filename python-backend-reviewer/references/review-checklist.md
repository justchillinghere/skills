# Review Checklist

Use this checklist as the review process owned by this skill. Do not duplicate the full content of the FastAPI Backend or Dignified Python skills; read those skills directly and use this file to decide how to turn observations into review findings.

## Required Finding Shape

A finding exists only when all five parts are present:

1. Observation: what the code currently does.
2. Violated expectation: what the task, plan, local pattern, or required skill expects instead.
3. Concrete risk: why this can cause a bug, unsafe behavior, bad architecture, weak tests, or unnecessary maintenance cost.
4. Affected location: file and line when possible.
5. Actionable correction: the smallest reasonable fix or design adjustment.

If any part is missing, use a Question or Note instead of a Finding.

## Severity Ranking

Rank by impact first, then likelihood.

- Critical: data loss, authorization bypass, money or billing corruption, migration breakage, production outage, irreversible destructive behavior.
- High: likely runtime bug, wrong business behavior, broken transaction boundary, security exposure, missing required validation, data leakage.
- Medium: architecture or layer boundary issue likely to cause near-term bugs, meaningful test gap, infrastructure leakage, unclear ownership across modules, fragile integration behavior.
- Low: localized readability or style issue, unnecessary helper, minor duplication, weak naming, small guideline drift with real navigation or maintenance cost.

Do not inflate severity because a rule was named in a skill. Severity follows risk.

## Topics

Assign each finding to exactly one primary topic:

- Bugs & Behavior: incorrect behavior, edge cases, data state, concurrency, time handling, idempotency, error handling.
- Architecture & Boundaries: module ownership, domain/application/infrastructure/API separation, transaction ownership, use-case shape, dependency direction.
- FastAPI Backend Skill Alignment: specific backend-skill guidance such as router/dependency shape, repository ownership, database access, migrations, worker composition, testcontainers, or metrics.
- Dignified Python Alignment: specific Python style guidance such as function/interface design, typing, imports, exception boundaries, defaults, LBYL flow, pathlib, module-level behavior.
- Security & Data Exposure: authn/authz, tenant isolation, secrets, PII masking, input validation, unsafe SQL, logging sensitive data.
- Tests: missing coverage, weak assertions, wrong test level, brittle fixtures, lack of regression tests for changed behavior.
- Maintainability & Local Fit: unnecessary indirection, mismatch with local code style, duplicated mapping, confusing naming, unclear reuse, overly clever code.

Omit empty topic sections.

## Common Sense Review Rules

- Do not reward indirection unless it improves reuse, naming, isolation, or testability.
- Small helpers must earn their existence. A one-line wrapper that is not reused and only forces navigation is usually a Low finding when it makes code harder to read.
- Always perform a final Low-severity maintainability sweep. Do not stop after finding High or Medium bugs.
- Pay special attention to newly added private helpers, one-line wrappers, schema mappers, local conversion functions, and pass-through functions. Keep them only when they improve reuse, semantic naming, isolation, or testability.
- Treat existing local style as evidence, not as a waiver for bugs, security issues, or bad boundaries.
- Do not require a use case for a simple read query only to satisfy layering.
- Do flag SQLAlchemy, Redis, HTTP clients, or FastAPI details leaking into domain/application code when it creates ownership or testability risk.
- Prefer specific, fixable findings over broad architectural complaints.
- Do not report the same root cause twice. Mention related locations under one finding.
- If a guideline conflicts with explicit local design or plan decisions, explain the conflict under Questions.

## Required Output Shape

Use this shape:

```markdown
# Python Backend Review

## Blockers

Only include when review could not run.

## Bugs & Behavior

### [High] Short title
File: path:line
Evidence:
Risk:
Suggested fix:

## Architecture & Boundaries

## FastAPI Backend Skill Alignment

## Dignified Python Alignment

## Security & Data Exposure

## Tests

## Maintainability & Local Fit

## Questions

## Notes
```

Do not include a verdict section.
