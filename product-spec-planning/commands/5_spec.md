---
description: Produce the final, self-contained Product Change Spec consumed by engineering flows
model: opus
argument-hint: "product/changes/<id>/"
---

# Spec — The Product Change Contract

Turn the approved design into a concise, self-contained **Product Change Spec**: the final document engineering flows (backend, frontend) consume, as plain text, to plan their work. It states the whole change in terms of observable behavior and nothing more.

## Input

- `design.md` from the change directory. Read it fully.

## Process

1. **Read `design.md` fully.**

2. **Write `spec.md`** using the skeleton below. Distill design into what matters for implementation planning — drop discussion, rationale depth, and alternatives. State behavior with `SHALL`/`MUST` (required) and `SHOULD` (exceptions acceptable).

3. **Present for review.** Iterate until approved.

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

## Behavior changes
### ADDED
[New behavior that does not exist today. SHALL/MUST.]
### MODIFIED
[Existing behavior that remains but changes.]
### REMOVED
[Behavior that must no longer exist.]

## Acceptance Scenarios
[Concrete given/when/then examples that prove the behavior above.
These are examples/tests, not new requirements.]

## Open Questions
[Only genuinely undecided items. If it is decided, it belongs in Behavior changes.]
```

## Example

> ### ADDED: Organization invitations
> The system SHALL allow an organization owner to invite a user by email.
> An invite SHALL remain `pending` until the invitee accepts.
>
> #### Scenario: Invite an existing member
> - GIVEN an email already tied to an active membership
> - WHEN the owner submits an invite
> - THEN no invite is created AND the owner is told the user is already a member

## Gate

The user must approve the spec. It is the artifact handed downstream.

## Rules

- Every behavior change is **observable**. Write the final behavior, not how to build it.
- No backend/frontend/database details. No task breakdown.
- `SHALL`/`MUST` for required behavior; `SHOULD` only when exceptions are acceptable.
- Do not duplicate the same behavior across ADDED/MODIFIED/REMOVED.
- Acceptance Scenarios are examples of the behavior, not additional requirements.
- Open Questions holds only unresolved decisions — nothing already decided.

## Next

Run `6_sync.md` against the change directory.

## When to go back

If writing the spec exposes a decision that is actually unresolved, return to `4_design.md`, decide it, then come back.
