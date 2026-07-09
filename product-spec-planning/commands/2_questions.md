---
description: Turn the frame into a neutral map of what to learn about the current product — questions only, no solution
model: opus
argument-hint: "product/changes/<id>/"
---

# Questions — Map What We Need to Learn

Turn the frame into a small, neutral map of **what we need to understand about the product and system as it is today**, before deciding what to build. These questions drive Research, which runs blind to the frame — so the questions must stand on their own and reveal nothing about the intended solution.

## Input

- `framed-intake.md` from the change directory (read it fully).
- A **light, read-only scan** of the product and codebase — just enough to know what exists so the questions are well-aimed. Not a design exercise.

## Process

1. **Read `framed-intake.md` fully.**

2. **Light read-only scan.** Spawn a `codebase-locator` and a `product-docs-researcher` to find which areas of the product, docs, and code relate to the change. You need to know what exists to ask good questions; do not design anything.

3. **Generate questions through five lenses.** Each lens is a prompt for finding neutral, present-tense questions about the current product/system. Use only the lenses that apply — skip the rest.
   - **Problem** — what does the current flow around this area do, and where could the stated pain observably originate?
   - **Evidence** (only if the request needs justifying) — what complaint, support, or analytics data exists about this area?
   - **User experience** — how does the *current* UX handle this and adjacent areas? What scenarios, states, and statuses exist today?
   - **Product knowledge** — what existing use cases, policies, and data models relate to this area?
   - **Scope** — what existing behaviors and edge cases would a change here touch? What states/statuses must be accounted for?

4. **Hunt for contradictions.** Walk the frame's claims and ideas; where two statements conflict, or a behavior in some case/state/status is unclear, turn that into a question.

5. **Write `questions.md`** using the skeleton below. The `Context` section must be **intent-free** — it names areas to focus on, never what is being built or why.

6. **Present the questions to the user.** Wait for approval or edits before finalizing.

## Output

Write `product/changes/<change-id>/questions.md`:

```markdown
# Research Questions

## Context
[2-3 sentences naming which areas of the product/system to focus on.
Do NOT mention what is being built or why. The researcher answers these as
fact-finding and is not told the intent.]

## Questions

### Problem
1. [Neutral, present-tense question about the current system]

### Evidence
2. [Only if justification is needed]

### User experience
3. [How the current UX / scenarios / states work today]

### Product knowledge
4. [Existing use cases, policies, data models in this area]

### Scope
5. [Existing behaviors / edge cases / states a change here would touch]
```

## Example

Bad question (leaks the solution, asks how to build):

> What's the best way to send an invite email when a user is added to an org?

Good questions (neutral, about what exists):

> How does organization membership work today — how is a user added to an organization, and what states can a membership be in?
> What existing flows send transactional email, and how is delivery handled?

The bad one presupposes the answer. The good ones let the researcher describe reality without guessing at intent.

## Gate

The user must approve the questions before Research runs. Without approval, stop here.

## Rules

- `questions.md` must **not** carry the intent — no frame, goals, motivation, or desired behavior. The aim isn't to make the topic unguessable; it's that the researcher works from neutral questions and reports facts, rather than designing a solution or "doing the task".
- Questions ask **what exists and how it works** — never "how should we build X".
- Forward-looking decisions ("how *should* it work", "which policy do we pick") do **not** belong here. They are Design's blocking questions, answered later with the human.
- Keep the map small (roughly 3-7 questions). Do not turn it into product research or dig deeper than the change needs.
- Not every lens produces a question. Evidence in particular is optional when the ask is self-evident.

## Next

Run `3_research.md` against the change directory.

## When to go back

If writing questions reveals the frame is vague, mis-scoped, or self-contradictory, return to `1_frame.md`, fix `framed-intake.md`, and come back.
