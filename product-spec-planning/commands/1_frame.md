---
description: Frame the product problem and scope from a raw request — problem, not solution
model: opus
argument-hint: "<feature request, ticket file, or business ask> [product/changes/<id>/]"
---

# Frame — State the Problem and Scope

Turn a raw request into a crisp **frame**: the problem, the desired outcome, and the boundaries — **not** a solution. This is the cheapest point to correct direction, so get the problem right before anything else.

## Input

The user's request: a short description, a ticket file path, or a business ask. Read any referenced file fully before doing anything else. This is the only input.

## Process

1. **Read the request and any referenced files fully.**

2. **Establish the change directory.**
   - If the user passed one, use it.
   - Otherwise derive a `<change-id>` (external ticket id if one exists, else `YYYY-MM-DD-short-slug`) and create `product/changes/<change-id>/` (create the `product/` store from `assets/store-scaffold/` if it does not exist yet).

3. **Write `framed-intake.md`** to the change directory using the skeleton below. Keep it short and concrete.
   - Do **not** invent a problem or fabricate evidence when the ask is self-evident. A request like "add a country dropdown when creating an organization" needs only a plain statement of the need — not a manufactured pain narrative. Depth is for changes where the value actually needs justification.

4. **Present the frame to the user** and ask the gate question: *"Are we solving the right problem?"* Incorporate corrections by editing the file. Do not move on until the user confirms.

## Output

Write `product/changes/<change-id>/framed-intake.md`:

```markdown
# Product Frame

## Problem
[The user/business problem in plain language. What is wrong or missing today,
from the perspective of the person who feels it. No solution.]

## Desired outcome
[What the user should be able to understand or do once this is addressed.]

## Business outcome
[The business, operational, or compliance result we expect. Omit if the change
is self-evidently scoped and no business justification is needed.]

## Initial idea
[The proposed direction in one or two sentences, if there is one. This is a
starting point for discussion, not a commitment.]

## Non-goals
- [Things a reader might reasonably assume are included but are not]
- [Explicit exclusions for this iteration]

## Known constraints
- [Existing behavior, policies, or invariants this change must respect]
```

## Example

Bad frame (a solution wearing a problem's clothes):

> Add an email on every status change.

Good frame:

> **Problem:** Users don't know what is happening with their order without repeatedly checking the site, and can miss important status changes (payment, cancellation, refund).
> **Desired outcome:** Users understand whether their order is confirmed, cancelled, refunded, or failed.
> **Non-goals:** marketing emails, a full notification center, push notifications this iteration.

The bad one names a mechanism and a trigger. The good one names who is hurting, why, and what "better" looks like — leaving the solution open for the stages that follow.

## Gate

The user must confirm the frame ("right problem?") before proceeding. Without confirmation, stop here.

## Rules

- Describe the **problem and scope**, never a solution or implementation.
- Do not fabricate problems, metrics, or evidence. If the ask is obvious, keep the frame minimal.
- Make non-goals explicit — they prevent scope creep downstream.
- Keep it short. The frame is a shared understanding, not a document to admire.

## Next

Run `2_questions.md` against the change directory. For a simple, well-understood change with no real unknowns, you may instead skip straight to `5_spec.md` — that is your call, not a required classification.

## When to go back

The frame is the first stage, but it is not frozen. If Research or Design later reveals the problem was mis-scoped, return here, edit `framed-intake.md`, and let the affected downstream stages re-run.
