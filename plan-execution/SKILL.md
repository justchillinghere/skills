---
name: plan-execution
description: Use when the user asks to implement, build, execute, or ship an approved plan (an ExecPlan and Design Note produced by development-planning), e.g. "поимплементируй 007", "implement this plan", "build stage 003" — or a small, clear fix or technical change that needs no plan, e.g. "сделай этот фикс по полной программе". The orchestrator delegates implementation to a fast subagent under strict guardrails, opens a ready merge request, always runs a fresh-context review fan-out, waits for the project's CI and external review (per the project's MR skill), triages all findings, fixes clear bugs with a fixer subagent, and escalates only the ambiguous ones to the human. Implementation is not done until review has run.
---

# Plan Execution

Use this skill to execute an approved plan. Usually the plan already exists: an
`exec-plan.md` and its `design-note.md` in a `docs/plans/active/NNN-slug/` directory, authored
via the `development-planning` skill. A small, clear change needs no plan (see "No plan:
small, clear changes"). This skill is the **orchestration playbook** for turning the work
into shipped, reviewed code.

You (the session running this skill) are the **orchestrator**. You are the smart model. You
do not write the feature code yourself. You delegate labor to faster subagents and keep the
judgment — sequencing, triage, and what to escalate to the human — for yourself.

## The one rule that makes this work

**Implementation is not finished until review has run.** When you execute a plan, the review
fan-out (below) is part of the job, not a separate request the human must make. Do not stop
and report "implementation done" after the implementer returns. Run the review, act on it,
and only then report. If the human ever has to say "now review it", this skill has failed.

## The flow

```text
read plan → delegate implementation → open ready MR → (always) review fan-out
          → wait for project CI and external review → triage
          → fix clear bugs (delegate) / escalate ambiguous (to human) → report
```

Independent tasks may be implemented in parallel (see "Parallel implementation"). Review
always follows implementation. Keep the loop; do not add machinery beyond it.

## Step 1 — Read the plan yourself

Before delegating anything, read the plan directory in full: `exec-plan.md` and
`design-note.md`. You need enough context to write a good implementer prompt and to triage
review findings later. Note the milestones, the acceptance criteria, and the test command.

If the user named work that is already merged (e.g. "007 я влил в main"), sync first: pull
the default branch before creating the feature branch.

### No plan: small, clear changes

Not every change needs `development-planning`. If the change is a clear fix or a technical
change with nothing to design — no new contract, no domain decision, no trade-off to choose —
skip planning and execute directly. The user's task text (or the Asana task) is the plan.

- Read the code the change touches yourself, so you can write the implementer prompt and
  triage later.
- Give the implementer the task text in place of the plan documents. Drop the guardrails
  that name the ExecPlan and Design Note; keep all the others.
- Name the branch by the repo's branch convention, not by a plan ID.
- Every step after implementation runs the same: ready MR, review, project CI, triage, fix.
- If the work turns out to need a design decision, stop. Tell the human, and propose
  `development-planning` for it. Do not decide the design inside the fix.

## Step 2 — Delegate implementation

Spawn an implementer as a subagent. **Default model: `sonnet`** (fast, and the plan already
carries the thinking). Override only if the user asks. The orchestrator stays on the smart
model; the implementer does not need to be.

Give the implementer a prompt built from these **fixed guardrails** plus the **task-specific
context** you fill from the plan and repo:

Fixed guardrails (always include):

- Role: "You are an engineer in a Claude Code session. Implement strictly from the ExecPlan."
- Read the plan documents **in full** before starting. Do not paraphrase them into code.
- Follow the ExecPlan milestone order. Commit per milestone, frequently, with clear messages.
- When implementation is done: push the branch and open the MR as **ready, not draft**,
  unless the project's MR skill says otherwise. External reviewers skip drafts. The review
  runs on that MR. This is the linear path — implement, push, review — not a gated one.
- Resolve ambiguity autonomously through the Design Note. Record decisions in the ExecPlan
  `Decision Log` and keep `Progress` current. Do not ask "what next" between milestones.
- **STOP rule**: if execution reveals a Design Note decision is wrong or missing, stop,
  update the Design Note, surface it to the human, and only then continue. Never re-decide
  architecture or contracts inside the ExecPlan.
- Load and follow the repository's code-style skill (e.g. `dignified-python` for Python).
- No long docstrings. No comments that reference plans, use cases, or invariants
  (`# BR-3`, `# see design-note`, etc.). The code is self-explaining; the "why" lives in the
  plan. Reuse existing repo patterns; do not build parallel stacks.
- Never hardcode or log secrets. Read them from the environment.

Task-specific context (fill from the plan and repo):

- The plan directory path and the one- or two-sentence summary of what this task adds.
- Repo root, language/version, test command, migration tool — read these from the repo's
  `CLAUDE.md` or the task's `exec-plan.md` rather than guessing.
- The feature branch name (from the plan's `NNN-slug`, e.g. `feat/003-voice-transcription`).
- Any temporary observability the human wants for manual testing, behind a settings flag so
  it is removable in one line — not commented-out code.
- Which secrets are already in `.env`, so the implementer neither asks for nor logs them.

The implementer keeps the ExecPlan living sections (`Progress`, `Decision Log`,
`Surprises & Discoveries`) current as it works.

### Parallel implementation

Parallelism is a win only when three things hold. Miss one and it costs time, not saves it.

- **Architecture is frozen.** The Design Note is settled and the contracts are fixed. Before
  that, "independent" is a guess, and parallel work on a guessed boundary produces rework.
- **The slices are coarse and independent.** Spawn one implementer per heavy, self-contained
  chunk — a whole adapter, the backend vs the frontend — that does not touch another slice's
  files or depend on its output. Do **not** fan out fine, similar units: four CRUD endpoints
  that share one pattern are faster in one implementer that already holds the pattern than in
  four that each re-derive it. Parallelize chunks, not lines.
- **Review still follows every slice.** Step 3 runs on the combined result exactly as it does
  for one implementer. Parallel implementation without that fan-out just moves the bottleneck
  onto you; the review is what keeps your attention on triaged findings, not raw diffs.

The plan should already name the parallelizable chunks — the ExecPlan's `Parallelizable units`
list, filled during planning. Do not rediscover them from memory here; if that list is absent,
the plan was not decomposed for parallel work, so go sequential. Cap concurrent implementers at
what one review pass can trace. When in doubt, go sequential.

## Step 3 — Review fan-out (always)

When implementation returns, run the review by calling the **`review-swarm`** skill, targeting
the MR the implementer opened. That skill owns the reviewer roster (which lenses run for which
changed files), launches each reviewer in its own clean-context subagent, and posts findings
inline on the MR (prefixed `QA review · <lens>`).

This skill does not hold the review logic. It only triggers the review and then acts on the
result. To change who reviews, which model each uses, or how findings are delivered, edit
`review-swarm` — not this file.

Two principles this skill relies on `review-swarm` to keep:

- **Clean context.** No reviewer runs in the implementer's context, and the implementer never
  reviews its own work. A shared-context reviewer inherits the author's blind spots.
- **Independence.** Reviewers do not know about each other. When two independently flag the
  same thing, that agreement is a strong signal you will see when you read the findings.

### Wait for the project's CI and external review

Some projects add their own steps after the MR opens: an external reviewer (a bot that
comments on the MR), CI jobs to wait for, manual gates to start. These live in the project's
MR skill, not here. ZenCreator: `branch-and-pr` (CodeRabbit, `mr-ci`, integration tests).
If the project has such a skill, follow it before Step 4.

How to wait, in any project: run one wait command in the background and act when it exits.
Do not poll in a loop of your own, do not `sleep`, do not start a subagent only to wait.
Always set a time limit. If it runs out, report what is still running and go on.

## Step 4 — Triage the findings yourself

You (the smart orchestrator) read all the findings — the comments `review-swarm` posted on
the MR, each carrying a severity (`critical` / `high` / `medium` / `low`) and a rationale,
and the comments of any external reviewer — and decide. For each finding:

- **Clear, real, and simple** (a genuine bug, a safe simplification) → fix it (Step 5). Do
  not ask the human.
- **Ambiguous, risky, or a judgment call** (a contract change, a trade-off, anything you are
  unsure is real) → do not fix silently. Collect it for the human (Step 6).

When you agree a finding is real but non-trivial, deepen it: confirm it against the code
before acting. Do not act on a finding you have not verified.

External reviewer comments also follow the rules in the project's MR skill (for example,
which kinds of comments to answer as not valid).

## Step 5 — Fix clear bugs (delegate)

Spawn a fixer subagent (default model `sonnet`) with the confirmed, simple findings. Give it
the same code-style guardrails as the implementer. Keep the fix diff small and targeted. If a
fix touches non-trivial logic, it leaves a runnable check behind, per the repo's testing
convention.

The fixer commits and pushes to the same MR branch. For each MR comment it fixes —
`review-swarm` or an external reviewer — it replies briefly with what it changed, then marks
the thread resolved.

After fixes land, re-run only the relevant reviewer if a fix was substantial. An external
reviewer may review the new push; do not wait for it a second time. Do not loop endlessly:
one fix pass, plus a targeted re-check, is normally enough.

After the last push, run the project's final CI gates, if its MR skill has any (ZenCreator:
integration tests). A gate started before the last push is lost: the push resets it.

## Step 6 — Report and escalate

Give the human a short summary:

- What was implemented, and a link to the MR.
- The review findings you fixed, in one line each (their MR threads are resolved).
- The external reviewer comments you answered as not valid, in one line each.
- The state of the final CI gates.
- The ambiguous findings you did **not** act on, as a list, so the human can decide. Their MR
  threads stay open, waiting on the human.

Stop there. Do not merge the MR unless the user asks.

## What this skill is not

This is a written order of work, not a "feature factory". No machine per task, no automatic
test-and-deploy pipeline, no long-running agents. It is the record of how the human likes the
build → review → fix loop to run, so the orchestrator runs it the same way every time without
being reminded.
