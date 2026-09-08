---
name: plan-execution
description: Use when the user asks to implement, build, execute, or ship an approved plan (an ExecPlan and Design Note produced by development-planning), e.g. "поимплементируй 007", "implement this plan", "build stage 003". The orchestrator delegates implementation to a fast subagent under strict guardrails, then always runs a fresh-context review fan-out, triages the findings, fixes clear bugs with a fixer subagent, and escalates only the ambiguous ones to the human. Implementation is not done until review has run.
---

# Plan Execution

Use this skill to execute an approved plan. The plan already exists: an `exec-plan.md`
and its `design-note.md` in a `docs/plans/active/NNN-slug/` directory, authored via the
`development-planning` skill. This skill is the **orchestration playbook** for turning that
plan into shipped, reviewed code.

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
read plan → delegate implementation → (always) review fan-out → triage
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
- Do **not** push and do **not** open a PR until the human asks.
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
  `CLAUDE.md` or `PLANS.md` rather than guessing.
- The feature branch name (from the plan's `NNN-slug`, e.g. `feat/003-voice-transcription`).
- Any temporary observability the human wants for manual testing, behind a settings flag so
  it is removable in one line — not commented-out code.
- Which secrets are already in `.env`, so the implementer neither asks for nor logs them.

The implementer keeps the ExecPlan living sections (`Progress`, `Decision Log`,
`Surprises & Discoveries`) current as it works.

### Parallel implementation

If the plan's milestones or tasks are genuinely independent, you may spawn more than one
implementer subagent in parallel, one per independent slice. Only do this when the slices do
not touch the same files or depend on each other's output. When in doubt, go sequential.

## Step 3 — Review fan-out (always)

When implementation returns, run the review. Each reviewer runs in its **own subagent with a
clean context** — never the implementer's context, and never the implementer reviewing its
own work. A reviewer that shares the author's context inherits the author's blind spots. The
orchestrator conducts; the implementer does not spawn its own reviewers.

### Reviewer roster

Run these reviewers, each as a separate subagent, on the working-tree changes. This roster is
the modularity seam: **edit this list** to add, remove, or re-target reviewers, or to change a
reviewer's model — without touching the flow above.

| Reviewer | How to run | Focus | Model |
|---|---|---|---|
| Backend correctness | `python-backend-reviewer` skill (or `/code-review`) | bugs, clean-layering, FastAPI, dignified-python, security, tests | `sonnet` |
| Over-engineering | `/ponytail-review` | speculative abstractions, duplication, what to delete | `sonnet` |

Notes for editing the roster:

- Match reviewers to the stack. For a frontend task, swap the backend reviewer for the
  frontend one. For a non-Python repo, drop `python-backend-reviewer`.
- A reviewer's model may differ from the implementer's. You may point a reviewer at a
  different model when the user has one configured for it.
- Reviewers are report-only. They find and explain; they do not edit. Fixing is Step 5.

## Step 4 — Triage the findings yourself

You (the smart orchestrator) read all the findings and decide. For each finding:

- **Clear, real, and simple** (a genuine bug, a safe simplification) → fix it (Step 5). Do
  not ask the human.
- **Ambiguous, risky, or a judgment call** (a contract change, a trade-off, anything you are
  unsure is real) → do not fix silently. Collect it for the human (Step 6).

When you agree a finding is real but non-trivial, deepen it: confirm it against the code
before acting. Do not act on a finding you have not verified.

## Step 5 — Fix clear bugs (delegate)

Spawn a fixer subagent (default model `sonnet`) with the confirmed, simple findings. Give it
the same code-style guardrails as the implementer. Keep the fix diff small and targeted. If a
fix touches non-trivial logic, it leaves a runnable check behind, per the repo's testing
convention.

After fixes land, re-run only the relevant reviewer if a fix was substantial. Do not loop
endlessly: one fix pass, plus a targeted re-check, is normally enough.

## Step 6 — Report and escalate

Give the human a short summary:

- What was implemented and that it is committed (not pushed).
- The review findings you fixed, in one line each.
- The ambiguous findings you did **not** act on, as a list, so the human can decide.

Stop there. Do not push or open a PR unless the user asks.

## What this skill is not

This is a written order of work, not a "feature factory". No machine per task, no automatic
test-and-deploy pipeline, no long-running agents. It is the record of how the human likes the
build → review → fix loop to run, so the orchestrator runs it the same way every time without
being reminded.
