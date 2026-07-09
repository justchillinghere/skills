---
name: development-planning
description: Use when the user asks to plan, execute, continue, resume, follow up, maintain, or organize a development task using repository execution plans. Ensures docs/PLANS.md and docs/plans/ exist, reads the planning instructions, creates or continues active plans, archives completed plans, records deferred cleanup in TECH_DEBT.md, and uses stable task IDs for plan files and branches.
---

# Development Planning

Use this skill for development work that should be planned, resumed from an existing plan, or executed from a living task document.

The repository owns the actual planning files. This skill only provides the setup convention, canonical `PLANS.md` template, and a helper for choosing the next local task ID.

## Repository Setup

At the repository root, expect:

```text
docs/
├── PLANS.md
└── plans/
    ├── active/
    ├── archived/
    └── TECH_DEBT.md
```

If `docs/PLANS.md` is missing, create the structure and copy `assets/PLANS.md` from this skill into `docs/PLANS.md`.

If `docs/plans/TECH_DEBT.md` is missing, copy `assets/TECH_DEBT.md` from this skill.

Create `docs/plans/active/` and `docs/plans/archived/` if missing.

## Required First Step

Before authoring, editing, or executing a plan, read `docs/PLANS.md` in full. Follow it over this skill whenever there is a conflict. The repository-local file is the source of truth because teams may customize it.

## Choosing or Creating a Plan

When the user asks to continue, resume, follow up, or execute an existing task:

1. Inspect `docs/plans/active/`.
2. If exactly one active plan is relevant, read it and continue from its `Progress`, `Decision Log`, and validation sections.
3. If multiple active plans could match, briefly ask which plan to use unless the user named one.
4. Keep the plan updated while working. Record decisions, discoveries, progress, validation, and outcomes in the plan itself.

When the user asks to plan a new task:

1. Generate a short lowercase kebab-case slug from the task name.
2. Use `scripts/next_plan_id.py` from this skill to find the next local task ID.
3. Create the plan under `docs/plans/active/NNN-slug.md`.
4. Re-check before writing that no `NNN-*.md` exists anywhere under `docs/plans/`; if a collision exists, rerun the helper and use the next ID.
5. Write a self-contained ExecPlan following `docs/PLANS.md`.

## Task IDs and Names

Use three-digit local task IDs:

```text
001-bootstrap-backend.md
002-auth-model.md
003-api-errors.md
```

The numeric prefix is globally reserved across active and archived plans. Never reuse an ID, even after a plan is archived.

Plan filenames use:

```text
NNN-short-task-slug.md
```

Branch names should normally use:

```text
feat/NNN-short-task-slug
fix/NNN-short-task-slug
chore/NNN-short-task-slug
```

One plan ID may have multiple branches for follow-up fixes or related PRs, for example `fix/001-bootstrap-backend-validation`. Do not create a new plan with an already-used numeric ID.

If an external tracker ID exists, such as a Linear ticket, prefer that external ID for the plan and branch name instead of local numbering.

## Helper Script

Run from the repository root, replacing the skill path with the actual path where this skill is installed:

```bash
python3 <skill-path>/scripts/next_plan_id.py --plans-dir docs/plans
python3 <skill-path>/scripts/next_plan_id.py --plans-dir docs/plans --slug bootstrap-backend
python3 <skill-path>/scripts/next_plan_id.py --plans-dir docs/plans --slug bootstrap-backend --branch feat
```

Expected outputs:

```text
004
004-bootstrap-backend.md
feat/004-bootstrap-backend
```

The helper scans recursively under `docs/plans`, parses filenames that start with digits, and returns the next three-digit ID. It ignores unnumbered files such as `TECH_DEBT.md`.

## Tech Debt

Use `docs/plans/TECH_DEBT.md` for intentional deferrals, cleanup notes, and follow-up work that is not part of the current plan. Entries should be short, concrete, and include a source plan ID when possible.

Do not use the tech debt file to hide acceptance criteria required for the current task.

## Archiving

When a plan is complete:

1. Update its `Outcomes & Retrospective`.
2. Confirm validation results are recorded.
3. Move it from `docs/plans/active/` to `docs/plans/archived/`.
4. Leave the filename and numeric ID unchanged.
