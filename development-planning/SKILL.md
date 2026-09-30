---
name: development-planning
description: Use when the user asks to research, assess, or scope a task, or to plan, execute, continue, resume, follow up, maintain, or organize a development task using repository plans. Planning optionally starts with a research.md (facts, causes, three fix scopes A/B/C to choose from), then a human-owned Design Note (decisions: problem, domain, use cases, contracts), which is grilled with a review lens and then drives an agent-owned ExecPlan (execution: order, files, tests, progress). Reads its Design Note and ExecPlan templates from the skill itself — it does not copy them into the repository. Ensures docs/plans/ exists, records deferred cleanup in TECH_DEBT.md, and uses stable task IDs for plan directories and branches.
---

# Development Planning

Use this skill for development work that should be planned, resumed from an existing plan,
or executed from a living task document.

The repository owns the actual planning files — the filled-in Design Notes and ExecPlans
for each task. This skill owns the templates. The canonical `DESIGN_NOTE.md` and `PLANS.md`
templates and the review lens stay in the skill's `assets/`, and the ID helper in the
skill's `scripts/`. Read them from there. Do not copy the templates into the repository.

## Two artifacts, two readers

A feature is planned with two documents, at two altitudes, for two readers. Keeping them
separate is the point — do not merge them.

- **Design Note** (`design-note.md`) — the **decision** artifact, **human-owned**. What we
  build and how it is shaped: problem, domain model, use cases, contracts. An agent may
  draft it, but the human decides the domain, use cases, and contracts. Both the backend
  and frontend build agents build from it. Template + full guidance: `assets/DESIGN_NOTE.md`
  in this skill. Read it there; do not copy it into the repository.
- **ExecPlan** (`exec-plan.md`) — the **execution** artifact, **agent-owned**, generated
  **from** an approved Design Note. How to build exactly what was decided, step by step.
  Template + full guidance: `assets/PLANS.md` in this skill. Read it there; do not copy it
  into the repository.
- **Review lens** (`assets/REVIEW_LENS.md`) — generic gap-finding questions to grill a
  Design Note before build. Skill-only: never copied into the repository.

Optionally, a **Research** (`research.md`) comes before the Design Note: facts about the
system as it is, then what they imply and at what level to fix it. It records the options
that were compared; the Design Note covers only the chosen one and links back instead of
repeating them. See "Research" below.

### Research

Write `research.md` when the task is not obvious from the ticket: the cause is unclear, the
fix could land at more than one level, or the same failure may exist elsewhere. For a plain
local change skip it. No template — the data shapes it — but keep this order:

Facts (what is):

0. **Header** — ticket, code commit, data window, date the queries ran. Facts go stale; this
   says how stale.
1. **Ticket claim and expected behavior** — what should hold (the invariant), in one place.
2. **How it works now** — trace the flow through every layer with `file:line`. Trace the
   sibling paths too (other callers, other providers of the same kind), not only the one the
   ticket names — that is what answers "one instance or a class".
3. **Data** — counts, timing, who is affected. This is the impact estimate and the "before"
   number the fix is measured against. Full queries go at the end of the file.

Analysis (what it means):

4. **Causes** — symptom → immediate cause → systemic cause (the deepest one we control).
   State whether this is an isolated instance or a class of failures.
5. **Options** — exactly three scopes: A. local patch, B. local/systemic hardening,
   C. broader redesign. Compare impact, cost, blast radius, reversibility, future leverage.
   Recommend the smallest option that captures most of the justified impact.
6. **Out of this ticket** — what was found but will not be done here. Rejected systemic
   options and side findings go to `TECH_DEBT.md` with a link to this section.
7. **Open questions.**

Research does not hold contracts, domain model, non-goals, or build steps — those belong
to the Design Note for the chosen option.

The facts part (0–3) may be delegated to a subagent that gets only the questions, not your
hypothesis about the fix, so the facts are not bent toward it. Optional; worth it when you
already have a strong hypothesis.

**Scope gate.** If the recommended option materially exceeds the original ticket, stop
before the Design Note and put the trade-off to the human.

### What the ExecPlan is for, and why

The ExecPlan adds no decisions and no domain knowledge — those live in the Design Note.
It adds exactly what a long, resumable, autonomous build needs and neither the Design Note
nor the code carries:

1. **Build order** — migration → domain → use cases → API → tests; pilot slice then
   fan-out; one commit per milestone, so the agent does not build in the wrong order.
2. **Anchoring in this repository** — which files/modules to touch, where new code lives,
   which fixtures/factories to reuse. The Design Note is codebase-agnostic; the ExecPlan is
   where it meets the actual tree.
3. **Acceptance → tests + validation commands** — each criterion mapped to the test that
   proves it, with exact commands. Definition of done, made runnable.
4. **Progress state + surprises log across sessions** — what is done and what is next, so a
   resumed agent continues instead of re-deriving; plus a log of where reality diverged. A
   file survives context summarization and session boundaries; in-context planning does not.

Its value scales with autonomy and run length. For a small single-session change, a Design
Note may be enough and the ExecPlan can be skipped — go straight to code.

### The one hard rule

**The ExecPlan never decides architecture, domain, or contracts.** If execution forces such
a change, stop: update the Design Note (and surface it to the human), then let the ExecPlan
follow. Do not silently re-decide upstream concerns inside the ExecPlan. This artifact
boundary is the forcing function that keeps architecture a human decision made up front.

## Repository Setup

At the repository root, expect only the filled-in plans, not the templates:

```text
docs/
└── plans/
    ├── active/
    │   └── NNN-slug/
    │       ├── research.md        (optional)
    │       ├── design-note.md
    │       └── exec-plan.md
    ├── archived/
    └── TECH_DEBT.md
```

The `PLANS.md` and `DESIGN_NOTE.md` templates stay in this skill's `assets/`. Do not copy
them into `docs/`. The repository holds only per-task plans under `docs/plans/`.

Create `docs/plans/active/` and `docs/plans/archived/` if missing.

`TECH_DEBT.md` is a real data file, not a template. If `docs/plans/TECH_DEBT.md` is missing,
create it from `assets/TECH_DEBT.md` in this skill. It is created once, then it grows with
real entries.

## Required First Step

Before authoring, editing, or executing a plan, read the templates in full: `assets/PLANS.md`
and `assets/DESIGN_NOTE.md` from this skill.

A team may still customize the convention. If the repository has its own `docs/PLANS.md` or
`docs/DESIGN_NOTE.md`, read that file instead and follow it over the skill on any conflict.
Do not create these files yourself. Read the skill's templates by default; use a repo-local
file only when the team already put one there.

## Planning workflow

When the user asks to plan a new task:

1. **Research, if the task needs it.** Write `research.md` per "Research" above. The human
   picks the option (A/B/C); respect the scope gate. Skip this step for a plain local change.
2. **Design Note for the chosen option.** Draft `design-note.md` from the skill's `assets/DESIGN_NOTE.md`
   template (or a repo-local `docs/DESIGN_NOTE.md` if the team has one), filling only
   the relevant sections. The human owns the domain, use cases, and contracts — draft with
   options and let them decide; do not resolve architecture unilaterally.
3. **Grill it in a clean context.** Launch a **subagent** whose only inputs are the
   `design-note.md` path, `research.md` if present, and `assets/REVIEW_LENS.md` — not the conversation that produced the
   draft. The author's context has already absorbed and rationalized every decision; a
   reviewer that shares it inherits the same blind spots. A fresh reviewer sees only what the
   Design Note actually says and grills it soberly. Have it return concrete gaps (not a
   rewrite), then close them. Do not proceed until the head (problem → use cases) and the
   contract are settled. Only grill in-context yourself when a subagent is unavailable — and
   then say so, since it is the weaker check.
4. **Then the ExecPlan.** Generate `exec-plan.md` from the approved Design Note, following
   the skill's `assets/PLANS.md` template (or a repo-local `docs/PLANS.md` if the team has
   one). It is execution only (order, files, acceptance→tests, progress) and is
   subordinate to the Design Note per the hard rule above.
5. **Build.** Execute the ExecPlan, keeping its `Progress`, `Surprises & Discoveries`, and
   validation sections current. Do not prompt for "next steps"; proceed milestone to
   milestone and commit frequently. When the build should be orchestrated — delegated to an
   implementer subagent and then reviewed — use the `plan-execution` skill, which owns that
   loop (implement → always review → triage → fix).

When the user asks to continue, resume, follow up, or execute an existing task:

1. Inspect `docs/plans/active/`.
2. If exactly one active plan is relevant, follow its own scheme (see "Legacy plans and
   migration"): a `NNN-slug/` directory splits shape (`design-note.md`) from execution
   (`exec-plan.md`); a flat `NNN-slug.md` is a legacy single-file ExecPlan. Read what is
   there and continue from its `Progress`, decisions, and validation state. A directory with
   only `research.md` is waiting on the option choice — resume there, not at the Design Note.
3. If multiple active plans could match, briefly ask which to use unless the user named one.
4. Keep both documents updated while working — decisions and contract changes in the Design
   Note, execution/progress/deviations in the ExecPlan.

## Legacy plans and migration

The directory scheme (`NNN-slug/` with a human-owned `design-note.md` and an agent-owned
`exec-plan.md`) is the default for **new** plans from now on. Older plans predate it and
stay valid — do not be thrown by the difference:

- **Detect the scheme per plan.** A `NNN-slug/` directory is a new two-artifact plan. A flat
  `NNN-slug.md` file is a legacy single-file ExecPlan — decisions and execution combined in
  one document, with its own embedded `Decision Log`.
- **Continue legacy plans in place, as-is.** Read the flat file and continue from its
  `Progress`, `Decision Log`, and validation. Do not expect a separate `design-note.md`, and
  do not restructure the file into the new scheme.
- **Migrate only on request.** Split a legacy plan into a Design Note + ExecPlan only if the
  user asks. When you do, keep the same `NNN` ID: create `NNN-slug/`, move the decisions into
  `design-note.md` and the execution into `exec-plan.md`.
- **New work uses the new scheme** even in a repository full of legacy flat plans; the
  numbering helper already reserves IDs across both files and directories.

## Choosing or Creating a Plan directory

Each plan is a directory, not a single file:

1. Generate a short lowercase kebab-case slug from the task name.
2. Use `scripts/next_plan_id.py` from this skill to find the next local task ID and name.
3. Create `docs/plans/active/NNN-slug/` and, inside it, `design-note.md` (from the skill's
   `assets/DESIGN_NOTE.md`) and, once the design is approved, `exec-plan.md` (from the
   skill's `assets/PLANS.md`).
4. Re-check before writing that no `NNN-*` directory or file exists anywhere under
   `docs/plans/`; if a collision exists, rerun the helper and use the next ID.

## Task IDs and Names

Use three-digit local task IDs:

```text
001-bootstrap-backend/
002-auth-model/
003-api-errors/
```

The numeric prefix is globally reserved across active and archived plans. Never reuse an
ID, even after a plan is archived.

Plan directories use `NNN-short-task-slug/`; the files inside are `design-note.md` and
`exec-plan.md`.

Branch names should normally use:

```text
feat/NNN-short-task-slug
fix/NNN-short-task-slug
chore/NNN-short-task-slug
```

One plan ID may have multiple branches for follow-up fixes or related PRs, for example
`fix/001-bootstrap-backend-validation`. Do not create a new plan with an already-used
numeric ID.

If an external tracker ID exists, such as a Linear ticket, prefer that external ID for the
plan and branch name instead of local numbering.

## Helper Script

Run from the repository root, replacing the skill path with the actual path where this
skill is installed:

```bash
python3 <skill-path>/scripts/next_plan_id.py --plans-dir docs/plans
python3 <skill-path>/scripts/next_plan_id.py --plans-dir docs/plans --slug bootstrap-backend
python3 <skill-path>/scripts/next_plan_id.py --plans-dir docs/plans --slug bootstrap-backend --branch feat
```

Expected outputs:

```text
004
004-bootstrap-backend
feat/004-bootstrap-backend
```

The helper scans recursively under `docs/plans` and parses leading digits from the names of
both files and directories, so it reserves IDs from `NNN-slug/` plan directories as well as
legacy flat `NNN-*.md` files. It ignores unnumbered names such as `TECH_DEBT.md`. Use the
`--slug` output as the plan directory name.

## Tech Debt

Use `docs/plans/TECH_DEBT.md` for intentional deferrals, cleanup notes, and follow-up work
that is not part of the current plan. Entries should be short, concrete, and include a
source plan ID when possible.

Do not use the tech debt file to hide acceptance criteria required for the current task.

## Archiving

When a plan is complete:

1. Update the ExecPlan's `Outcomes & Retrospective` and confirm validation results are
   recorded.
2. Promote the Design Note's durable invariants (§5) and long-lived decisions (§10) to a
   permanent home (project memory or an ADR) — those outlive the plan; the rest does not.
3. Move the whole `NNN-slug/` directory from `docs/plans/active/` to `docs/plans/archived/`.
4. Leave the directory name and numeric ID unchanged.
