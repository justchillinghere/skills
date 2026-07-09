---
description: Design the product change at the intersection of intent and facts — a discussion surface, not implementation
model: opus
argument-hint: "product/changes/<id>/"
---

# Design — Where Are We Going?

At the intersection of the **intent** (the frame) and the **facts** (research), propose how to shape the product change. This document is a discussion surface: it captures the desired behavior in detail and is the lowest-cost place to change direction. Get alignment here before investing in the spec.

## Input

- `framed-intake.md` (the intent) and `research.md` (the facts). Read both fully.

## Process

1. **Read `framed-intake.md` and `research.md` fully.**

2. **Deepen only if needed.** If research flagged an area that a design decision hinges on, spawn a focused sub-agent to examine that specific pattern or current behavior. Do not redo research wholesale.

3. **Present blocking questions first — and wait.** Before writing anything, list the open questions that block the design and get answers. Their purpose: remove ambiguity, resolve conflicting patterns or requests, surface possible scenarios, and validate behavior in edge cases, states, and statuses so **every outcome is covered**. Without the user's answers, do not create the document.

4. **Write `design.md`** (~200 lines) using the skeleton below. Ground the current state in research with `file:line`/doc references. Express desired behavior as BDD scenarios — include both positive (when to act) and negative (when *not* to act) cases.

5. **Present for review and iterate.** On changes, edit `design.md` in place — no `design-v2.md`.

## Output

Write `<change-dir>/design.md`:

```markdown
# Design Discussion

## Current State
[What exists today, grounded in research findings with source refs]

## Desired End State
[What we're building toward and how to verify it is correct]

## Proposed behavior
[Scenarios in given/when/then. Include positive and negative cases —
when to do something and when explicitly not to.]

## Design Decisions
1. **[Decision name]**: [chosen option] — [why]
2. **[Decision name]**: [chosen option] — [why]

## Out of scope
[What this change is deliberately not doing]

## Decisions needed
[Unresolved questions that require the user's decision]

## Open Risks
[Anything uncertain that might surface during implementation, if any]
```

## Example

A positive/negative BDD pair keeps behavior unambiguous:

> **Given** an owner invites an email already tied to an active membership,
> **when** the invite is submitted,
> **then** no new invite is created and the owner is told the user is already a member.
>
> **Given** an owner invites an email with no existing membership,
> **when** the invite is submitted,
> **then** a pending invite is created and an invitation email is sent.

## Gate

Blocking questions must be answered before the document is written. After writing, present the design and iterate until the user approves.

## Rules

- This is the cheapest point to change direction — surface ambiguity now, not in the spec.
- Describe **behavior**, never implementation.
- Edit the document in place across iterations.
- Every current-state claim is cited from research.

## Next

Run `5_spec.md` against the change directory.

## When to go back

If a gap or contradiction surfaces that research didn't cover, return to `3_research.md` (or `2_questions.md`); if the problem itself was mis-scoped, return to `1_frame.md`.
