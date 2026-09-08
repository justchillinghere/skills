---
name: review-swarm
description: Use to run a panel of independent code reviewers over a change and collect their findings, e.g. "review these changes", "run the review panel", "ревью на этот диф". Selects which review lenses to run from the changed files, runs each as an isolated clean-context subagent, and delivers findings inline to the PR if one exists or back to the caller if not. The `plan-execution` skill calls this after implementation. This skill owns the reviewer roster and the delivery harness; the review rules themselves live in separate lens skills.
---

# Review Swarm

Use this skill to review a change with several independent reviewers at once. Each reviewer
looks at the same diff through a different **lens** and reports what it finds. A caller (a
human, or the `plan-execution` orchestrator) runs this skill; it does not run itself.

## Two things this skill separates

The core idea: **the review rules and the delivery of findings are different things.** Keep
them apart.

- **Lens** — the review rules. What to look for, what to flag. A lens is delivery-agnostic:
  it produces findings, it does not know where they go. A lens is one of two kinds:
  - **Ours** — a lens file we write and maintain, in `assets/lenses/` (e.g. `backend.md`).
    This is the home for review rules we own.
  - **External** — a third-party tool we call by name (e.g. `/ponytail-review` from the
    ponytail plugin, the built-in `/code-review`, or Codex's own reviewer via the codex
    plugin as the cross-provider second opinion).
- **Harness** — the wrapper this skill owns. For every reviewer it applies the lens to the
  diff, enforces the shared finding discipline (below), then **delivers** the findings
  (inline PR comments, or a returned report). The harness is the same for every reviewer.

So this skill owns the **harness**, the **roster**, and **our lens files**. It does not own
the external tools — those it only calls. One axis keeps this clear: **ours vs external**. To
change our review rules, edit a file in `assets/lenses/`. To change an external reviewer, edit
its tool. To change who runs or where findings go, edit the roster and harness here.

## The roster

The roster is the list of reviewers, keyed to what changed. This is the modularity seam:
**edit this table** to add, remove, or re-target a reviewer, or to change its model. Each row
names a lens skill — never inline rules.

| Lens | Source | Run when files change | Model |
|---|---|---|---|
| correctness bugs | external · `/code-review` | any code | sonnet |
| over-engineering | external · `/ponytail-review` | any code | sonnet |
| backend architecture | ours · `assets/lenses/backend.md` | Python backend (`*.py`) | sonnet |
| frontend architecture *(TODO: lens not written yet)* | ours · `assets/lenses/frontend.md` | frontend (`*.tsx`, `*.ts`) | sonnet |
| cross-provider second opinion | external · the other provider's own reviewer | any code | see below |

Our lenses run on `sonnet` — a lens is our rules, so it needs a host that reads it. The one
reviewer that is not our lens is the cross-provider second opinion, below.

Selection: read the diff, match rows by changed files, run only the matching rows. Always run
the two "any code" lenses and the cross-provider second opinion. Add stack-specific rows as
they match. The frontend row is a placeholder — skip it until `assets/lenses/frontend.md`
exists.

### Cross-provider second opinion

A reviewer on a **different provider** than the one driving catches errors the driving model
is blind to. The rule: the second opinion runs on the *other* provider, using that provider's
**own** reviewer — genuinely fresh eyes, not our lens.

- Driving from **Claude** (the case today) → the second opinion is **Codex**. Run Codex's
  built-in reviewer through the connected codex plugin: `/codex:review` (which calls
  `codex-companion.mjs review --base <ref>`). Codex uses its own review prompt; we pass no
  lens.
- Driving from **Codex** → the second opinion would be **Claude**. The codex plugin lives only
  inside Claude Code, so it is not run there — Codex reviewing Codex is pointless.

Run only **one** cross-provider reviewer. Not every reviewer is Codex; the rest stay on the
driving provider (`sonnet`). One other-provider pass is the second opinion; more is waste.

How Codex's built-in review delivers its findings — whether it comments on the PR itself or
returns a report the harness folds in — must be confirmed on a live run. This is the first
Codex wiring; treat it as provisional.

### Extending the roster

- Add a reviewer → add a row: the lens, its source (ours/external), the file trigger, model.
- New lens of our own → write a file in `assets/lenses/`, then add a row pointing to it.
- New external tool → add a row naming the tool to call.
- The frontend row is a placeholder. Write `assets/lenses/frontend.md`, then drop the TODO.
- If a lens file grows large or needs its own scripts, promote it to a standalone skill later
  and change the row to call that skill. Starting as a file here is the low-commitment path.

## Running a reviewer (the harness)

For each selected row, spawn **one subagent**. Fill the lens and model from the row.

- Model: from the row (default `sonnet`; `codex` where the row says so).
- Prompt, in essence:
  - "You are a code reviewer. Apply this review lens — it is the authority on what to look
    for:" then either the contents of our lens file, or an instruction to run the external
    tool the row names.
  - "Review this change:" (embed the diff, or name the base ref so the subagent produces it).
  - The **finding discipline** (below).
  - The delivery instruction (below).

### Finding discipline (every lens, every reviewer)

This discipline is shared by all lenses. It was salvaged from the backend reviewer, because
it is generic — it is not backend rules, it is how any reviewer turns observations into
findings.

- **A finding needs all five parts**, or it is a Question or a Note, not a finding:
  observation (what the code does); violated expectation (what the plan, local pattern, or
  lens wants instead); concrete risk (the bug, unsafe behavior, bad boundary, weak test, or
  maintenance cost); affected location (`file:line`); actionable correction (the smallest
  reasonable fix).
- **Severity follows risk, not which rule was named:**
  - `critical` — data loss, auth bypass, money or billing corruption, migration breakage,
    outage, irreversible destruction.
  - `high` — likely runtime bug, wrong behavior, broken transaction, security exposure,
    missing required validation, data leak.
  - `medium` — boundary or architecture issue likely to bite soon, real test gap, infra
    leakage, fragile integration.
  - `low` — localized readability, an unneeded helper, minor duplication, small guideline
    drift with real navigation cost.
- **Discipline:** do not report taste alone. Do not report one root cause twice — name related
  locations under one finding. Small helpers and one-line wrappers must earn their place.
  Prefer specific, fixable findings over broad complaints. Always end with a low-severity
  maintainability sweep; do not stop at the high ones. No verdict — the caller triages.

### Isolation

Each reviewer runs in its own clean-context subagent. Do not tell a reviewer about the other
reviewers, their count, or that it is part of a panel. Each one reviews as if it were the only
reviewer. Independent reviews are the point: when two of them flag the same thing, that is a
strong signal — and the caller sees that naturally when reading the findings. Do not build a
"convergence" feature; it falls out of reading independent reports.

## Delivery adapter

Where findings go depends on whether a pull request exists for this change.

- **A PR exists** → the reviewer posts each finding as an inline comment on the PR, near the
  line, prefixed `QA review · <lens>` (e.g. `QA review · ponytail`). Use `gh` for this. This
  is the natural surface: comments are explicit and can be resolved.
- **No PR** → the reviewer returns its findings as text to the caller.

The lens does not change between the two. Only the harness's delivery step does.

## What this skill returns

- With a PR: the reviewers' comments are on the PR. This skill returns a short index — which
  lenses ran, and how many findings each posted, by severity.
- Without a PR: the collected findings, grouped by lens, each with severity and rationale.

This skill does **not** decide what to fix or what to escalate. That triage belongs to the
caller (the `plan-execution` orchestrator, or you). It reports; the caller acts.

## What this skill is not

- Not a merge gate. It computes no aggregate verdict, no approve/block, no auto-stamp.
- Not a token-optimized swarm. No cache-warming, no persona-claim scripts, no shared
  byte-for-byte prompt. Reviewers are launched directly with the Agent tool.
- Not a lens. The rules live in the lens skills; this skill only runs them and delivers.
