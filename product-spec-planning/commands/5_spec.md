---
description: Produce the final, self-contained Product Change Spec consumed by engineering flows
model: opus
argument-hint: "product/changes/<id>/"
---

# Spec — The Product Change Contract

Turn the approved design into a concise, self-contained **Product Change Spec**: the final document engineering flows (backend, frontend) consume, as plain text, to plan their work. It states the whole change in terms of observable behavior and nothing more.

The behavior sections use the **same requirement blocks as the canonical specs** under `product/specs/<capability>/spec.md`. That is deliberate: `6_sync.md` folds this change in by moving whole `### Requirement:` blocks, with no rewriting and no second copy of the behavior to keep in step.

## Input

- `design.md` from the change directory. Read it fully.

## Process

1. **Read `design.md` fully.**

2. **Write `spec.md`** using the skeleton below. Distill design into what matters for implementation planning — drop discussion, rationale depth, and alternatives. State behavior with `SHALL`/`MUST` (required) and `SHOULD` (exceptions acceptable).

3. **Route every requirement.** Each `### Requirement:` carries a `Capability:` line naming the capability spec it will land in (`product/specs/<capability>/spec.md`). Use an existing capability name where one fits; introduce a new one only when the behavior genuinely has no home.

4. **Run the validator:**

   ```bash
   python3 <skill-path>/scripts/validate_spec.py <change-dir>/spec.md --delta
   ```

   Fix every reported error before presenting.

5. **Present for review.** Iterate until approved.

## Output

Write `<change-dir>/spec.md`:

```markdown
# Product Change Spec: <name>

## Summary

[2-5 sentences: what changes from the user/system perspective. No implementation.]

## Problem

[Why this change is needed — user, business, compliance, or operational. No solution.]

## Goals

[Observable/testable outcomes. Not tasks. No "build endpoint / add component".]

## Non-Goals

[Explicit exclusions a reader might otherwise assume.]

## ADDED Requirements

### Requirement: <Short name>

Capability: <capability-name>

The system SHALL <new behavior that does not exist today>.

#### Scenario: <Short name>

- **GIVEN** <precondition>
- **WHEN** <the behavior being specified>
- **THEN** <the observable outcome>

## MODIFIED Requirements

### Requirement: <Short name — matching the existing requirement it replaces>

Capability: <capability-name>

[The complete final text of the requirement, not a diff. Sync replaces the
existing block wholesale, so this must stand alone.]

#### Scenario: <Short name>

- **GIVEN** ...
- **WHEN** ...
- **THEN** ...

## REMOVED Requirements

### Requirement: <Short name — matching the existing requirement to delete>

Capability: <capability-name>

[One line stating what behavior ceases to exist. No scenarios — the block is
being deleted, not respecified.]

## Open Questions

[Only genuinely undecided items. If it is decided, it belongs in a requirement.]
```

Omit any of the three delta sections that has no entries.

## Example

> ## ADDED Requirements
>
> ### Requirement: Organization invitations
>
> Capability: organization-access
>
> The system SHALL allow an organization owner to invite a user by email.
>
> An invite SHALL remain `pending` until the invitee accepts.
>
> #### Scenario: Invite an existing member
>
> - **GIVEN** an email already tied to an active membership
> - **WHEN** the owner submits an invite
> - **THEN** no invite is created
> - **AND** the owner is told the user is already a member

## Gate

The user must approve the spec. It is the artifact handed downstream.

## Rules

- **Written in English**, regardless of the language of surrounding product docs.
- Every `### Requirement:` in ADDED or MODIFIED MUST own at least one `#### Scenario:`. REMOVED requirements carry none.
- Scenarios nest under the requirement they prove. There is no separate acceptance-scenarios section — a scenario detached from its requirement rots when the requirement changes.
- MODIFIED requirements state the **complete final text**, not a diff.
- Every behavior change is **observable**. Write the final behavior, not how to build it.
- No backend/frontend/database details. No task breakdown.
- `SHALL`/`MUST` for required behavior; `SHOULD` only when exceptions are acceptable.
- Do not duplicate the same behavior across ADDED/MODIFIED/REMOVED.
- Open Questions holds only unresolved decisions — nothing already decided.

## Next

Run `6_sync.md` against the change directory.

## When to go back

If writing the spec exposes a decision that is actually unresolved, return to `4_design.md`, decide it, then come back.
