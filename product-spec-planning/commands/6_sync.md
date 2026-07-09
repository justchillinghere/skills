---
description: Fold the change into the canonical product spec, archive it, and update the index
model: opus
argument-hint: "product/changes/<id>/"
---

# Sync — Close the Loop

Fold the approved change into the canonical current-truth specs, archive the change, and update the index. This is what keeps `specs/` from drifting: the change is a delta, and Sync applies it to the durable truth.

## Input

- `spec.md` from the change directory. Read it fully.

## Process

1. **Read `spec.md` fully.**

2. **Locate the affected domain spec(s)** under `product/specs/<domain>.md`. If none exists yet, create one — but document **only the slice this change touches**, grounded in `research.md`; do not describe the whole domain. A new domain spec is partial by design and grows as later changes land.

3. **Apply the delta into the domain spec** so `specs/` reflects the *current* behavior:
   - `ADDED` → add the behavior.
   - `MODIFIED` → edit the existing behavior in place.
   - `REMOVED` → delete the behavior (do not leave a tombstone).
   This is a merge/edit, not an append. `specs/` describes how the system behaves now — not its history.

4. **Present the specs delta** (what will change in `specs/`) and confirm before writing.

5. **Archive the change**: move `product/changes/<id>/` to `product/changes/archive/<id>/`.

6. **Update `product/index.md`**: mark the change archived and leave placeholders for the downstream backend/frontend PR links.

## Output

- Updated `product/specs/<domain>.md` (canonical current behavior) — in this shape:

```markdown
# Spec: <domain>

> Covers behavior that has passed through the planning workflow. Partial by
> design — not a complete model of the domain.

## Overview
[What this domain is, 2-3 sentences]

## Behavior
### <Capability>
- The system SHALL <current behavior>
- States: <...>   Policies: <...>

## Scenarios
- GIVEN <...> WHEN <...> THEN <...>   (key and edge cases)

## Data-model concepts
[Entities and relationships as product concepts, not schema]

## Source
[Doc and `file:line` references this was reconciled from]
```

- `product/changes/<id>/` moved under `archive/`.
- Updated `product/index.md` row.

## Gate

Present the `specs/` delta and get confirmation before overwriting canonical truth. Do not sync a spec that still has genuinely blocking Open Questions.

## Rules

- `specs/` contains only **current behavior** — no change history, no rationale, no backlog. Those live in the archived change.
- Behavior, not implementation.
- `REMOVED` behavior is deleted from `specs/`, not annotated.

## Next

The change is planned. Hand `spec.md` (now archived) to the engineering flows as plain text — typically backend first (contracts), then frontend — keyed by the change-id. That is outside this skill.

## When to go back

If Open Questions in the spec are actually blocking, do not sync. Return to `5_spec.md`/`4_design.md`, resolve them, then come back.
