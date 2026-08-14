---
description: Fold the change into the canonical product spec, archive it, and update the index
model: opus
argument-hint: "product/changes/<id>/"
---

# Sync — Close the Loop

Fold the approved change into the canonical current-truth specs, archive the change, and update the index. This is what keeps `specs/` from drifting: the change is a delta, and Sync applies it to the durable truth.

## Input

- `spec.md` from the change directory. Read it fully. Its `## ADDED|MODIFIED|REMOVED Requirements` sections carry the deltas inline — there is no separate delta file to reconcile.

## Process

1. **Read `spec.md` fully.**

2. **Locate the affected capability spec(s)** under `product/specs/<capability>/spec.md`. If none exists yet, create one — but document **only the slice this change touches**, grounded in `research.md`; do not describe the whole capability. A new capability spec is partial by design and grows as later changes land.

3. **Apply the delta into the capability spec** so `specs/` reflects the *current* behavior:
   - `ADDED` → insert the `### Requirement:` block with its scenarios.
   - `MODIFIED` → edit the existing `### Requirement:` block in place, scenarios included.
   - `REMOVED` → delete the `### Requirement:` block entirely (do not leave a tombstone).

   This is a merge/edit, not an append. `specs/` describes how the system behaves now — not its history. Requirements move as whole blocks: a requirement and its scenarios are never separated.

4. **Update verification markers.** Every requirement carries a `Verified:` line. A requirement this change touched was checked against code during Research — set its marker to the current date and the `file:line` evidence. Do not touch markers on requirements this change did not examine.

5. **Run the validator** before presenting anything:

   ```bash
   python3 <skill-path>/scripts/validate_spec.py product/specs/
   ```

   Fix every reported error. Do not present a spec that fails validation.

6. **Present the specs delta** (what will change in `specs/`) and confirm before writing.

7. **Archive the change**: move `product/changes/<id>/` to `product/changes/archive/<id>/`.

8. **Update `product/index.md`**: mark the change archived and leave placeholders for the downstream backend/frontend PR links.

## Output

- Updated `product/specs/<capability>/spec.md` (canonical current behavior) — in this shape:

```markdown
# Spec: <capability>

> Covers behavior that has passed through the planning workflow. Partial by
> design — not a complete model of the capability.

## Purpose

[What this capability is, 2-3 sentences.]

## Requirements

### Requirement: <Short name>

Verified: <YYYY-MM-DD | NO> — <file:line evidence, or migration note>

The system SHALL <current behavior>.

<Further SHALL/SHOULD statements for this requirement, one per paragraph.>

#### Scenario: <Short name>

- **GIVEN** <precondition>
- **WHEN** <the behavior being specified>
- **THEN** <the observable outcome>
- **AND** <additional outcome, optional>

#### Scenario: <Another case — include negative and edge cases>

- **GIVEN** ...
- **WHEN** ...
- **THEN** ...

## Data-model concepts

[Entities and relationships as product concepts, not schema.]

## Source

[Doc and `file:line` references this capability was reconciled from.]
```

- `product/changes/<id>/` moved under `archive/`.
- Updated `product/index.md` row.

## Gate

Present the `specs/` delta and get confirmation before overwriting canonical truth. Do not sync a spec that still has genuinely blocking Open Questions, and do not sync a spec that fails the validator.

## Rules

- **Specs are written in English**, regardless of the language of the surrounding product docs. Downstream engineering flows and the validator both assume it.
- Every `### Requirement:` MUST own at least one `#### Scenario:`. A requirement with no scenario is not verifiable and the validator rejects it.
- Scenarios live under the requirement they prove, never in a separate section.
- `specs/` contains only **current behavior** — no change history, no rationale, no backlog. Those live in the archived change.
- Behavior, not implementation.
- `REMOVED` behavior is deleted from `specs/`, not annotated.

## Next

The change is planned. Hand `spec.md` (now archived) to the engineering flows as plain text — typically backend first (contracts), then frontend — keyed by the change-id. That is outside this skill.

## When to go back

If Open Questions in the spec are actually blocking, do not sync. Return to `5_spec.md`/`4_design.md`, resolve them, then come back.
