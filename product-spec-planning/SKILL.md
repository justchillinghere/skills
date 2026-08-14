---
name: product-spec-planning
description: Use when planning a PRODUCT change — turning a feature request or business ask into a reviewed Product Change Spec through staged artifacts (Frame → Questions → Research → Design → Spec → Sync). Not for engineering/implementation planning. The spec it produces is a self-contained document consumed separately by engineering planning flows. Produces durable, scannable artifacts under a `product/` store and keeps a canonical product spec current.
---

# Product Spec Planning

A staged workflow for thinking through a **product** change and emitting a self-contained **Product Change Spec**. Each stage produces one durable artifact on disk. Later stages read earlier artifacts from disk, not from chat history — so any session (or a future orchestrator) can resume or re-run a stage identically.

This skill plans *what the product should do and why*. It does **not** plan implementation. The `spec.md` it produces is handed, as plain text, to separate backend/frontend planning flows that live in their own repos.

## When to use / when not

- Use when a request changes product behavior a user or operator can observe.
- Do **not** use for purely technical work with no product-visible behavior (e.g. add a Dockerfile label, bump a dependency). That goes straight to the engineering flow.
- If you are unsure, run `1_frame.md` — it is cheap and will reveal whether there is a real product problem.

## The store

All artifacts live in a **product store**, independent of repo topology (works whether the product lives in its own repo, a monorepo, or a docs folder):

```text
product/
  specs/                 # canonical CURRENT product truth (strict), folded in on Sync
    <capability>/
      spec.md
    <domain>/            # a domain groups related capabilities
      spec.md            # optional: rules that hold across the whole domain
      <capability>/
        spec.md
  changes/
    <change-id>/         # one in-flight product change = the working directory for a run
      framed-intake.md
      questions.md
      research.md
      design.md
      spec.md
    archive/             # completed changes moved here after Sync
  index.md               # thin status table: change-id → stage/status → BE/FE PR links
```

- The **change directory** `product/changes/<change-id>/` is the argument every command operates on. It is a parameter, never hardcoded.
- If `product/` is missing, create it from `assets/store-scaffold/` on first use.
- `specs/` is the durable "current behavior" truth. During normal operation it is *generated* — written only by `6_sync.md`, never hand-edited mid-change. It may additionally be **seeded once** by migrating existing product documentation; see *Seeding* below.
- Loose product notes, opinions, rationale, roadmap, and backlog stay wherever the human keeps them (e.g. `docs/product_description`) — they are not this store.
- **Specs are written in English**, regardless of the language of the surrounding product docs. Engineering flows downstream and the validator both assume it.

## Spec shape

One capability per directory, one `spec.md` per capability. Inside it, every `### Requirement:` owns its `#### Scenario:` blocks — scenarios are never collected into a separate section, because a scenario detached from the requirement it proves rots silently when that requirement changes.

Capabilities may nest under a domain when a domain has several of them — `specs/memo/draft/spec.md`, `specs/memo/active-work/spec.md`. A domain directory may also carry its own `spec.md` for rules that hold across the whole domain, such as lifecycle invariants. Nest only where a domain actually has siblings; a domain with one capability stays flat and can gain children later by moving its spec down a level.

The capability name is its path under `specs/`, so a nested capability is named `memo/draft`. That name is what appears in the file's `# Spec:` title and in a change's `Capability:` routing line, and the validator checks that the title agrees with the directory it sits in.

The same requirement blocks appear in a change's `spec.md` under `## ADDED|MODIFIED|REMOVED Requirements`. That is deliberate: Sync folds a change in by *moving whole blocks*, with no rewriting and no second copy of the behavior to maintain. See `5_spec.md` and `6_sync.md` for the exact skeletons.

Validate before any gate:

```bash
python3 <skill-path>/scripts/validate_spec.py product/specs/
python3 <skill-path>/scripts/validate_spec.py <change-dir>/spec.md --delta
```

It enforces the structure — requirement/scenario nesting, GIVEN-WHEN-THEN completeness, `Verified:` markers, `Capability:` routing, unique names, English-only — and exits non-zero on failure.

## Precedence against human product docs

Where a `specs/` file and a human product doc both describe the same area:

- On what the system does **today** — `specs/` wins.
- On **intent**, direction, or anything not yet built — the human docs win.
- When neither is certain — verify against code. Research does this by default.

## Seeding

A project that already has substantial product documentation may seed `specs/` from it once, rather than waiting for every capability to pass through a change. Seeded requirements are migrated, not verified: each carries `Verified: NO` until a change touches that area and Research checks it against code. An unverified spec is worse than no spec if it is mistaken for verified truth, so the marker is mandatory and the validator enforces it.

## Stage map

| # | Command | Artifact | Reads (only) | Human gate | Executor |
|---|---|---|---|---|---|
| 1 | `1_frame.md` | `framed-intake.md` | the raw request | "Right problem?" | inline |
| 2 | `2_questions.md` | `questions.md` | `framed-intake.md` + light scan | approve questions | inline |
| 3 | `3_research.md` | `research.md` | **`questions.md` only** | review facts | **sub-agent** |
| 4 | `4_design.md` | `design.md` | `framed-intake.md` + `research.md` | answer blocking Qs, approve | inline |
| 5 | `5_spec.md` | `spec.md` | `design.md` | approve | inline |
| 6 | `6_sync.md` | updates `specs/` + `index.md` | `spec.md` | — | inline |

The "Reads (only)" column is a hard access rule. In particular: **Research must never see `framed-intake.md`** — the intent is hidden so the researcher reports what *is* rather than steering toward a solution.

The full chain is the default. Depth is a judgment call the person makes, not a required classification: for a simple, well-understood change with no real unknowns you may skip forward — e.g. Frame straight to Spec — and not invent problems or evidence the ask does not need.

## Orchestration doctrine

- Drive the whole change in **one main dialogue**. The agent walks you gate to gate; you review, it writes the files.
- **Only Research is delegated.** At stage 3 the main agent spawns an intent-blind **research sub-agent (Opus)** and passes it *only* `questions.md`. The sub-agent does the noisy gathering (spawning `codebase-locator`/`codebase-analyzer`/`product-docs-researcher` workers, Sonnet) in its own context and returns `research.md` + a short summary. The main dialogue never fills with raw file reads, and the frame never leaks into research.
- Rule of thumb — **inline vs sub-agent**: inline if the step needs your dialogue AND is intent-aware AND not noisy (Frame, Questions, Design, Spec, Sync). Sub-agent if it is noisy OR must be blind to intent (Research).
- Everything the agent produces goes to a file. Product artifacts contain product behavior (given/when/then), never implementation detail.

## State is the filesystem — resume and re-run

There is **no external orchestrator**. The presence of files in a change directory *is* the state: `framed-intake.md` present but `research.md` absent → you are between Questions and Research.

To resume (new dialogue, or returning later): point this skill at the change directory. It runs `ls`, sees which artifacts exist, and continues from the next missing stage, loading only that stage's allowed inputs. Sessions are disposable; the files are the memory.

This is why the workflow is shell-agnostic: the same command files can be driven by (a) you inline, (b) a fresh session, or (c) a future headless orchestrator. All three read the same artifacts and the same access rules. Build the spine first; any shell sits on top for free.

## Conventions

- **change-id**: with an external ticket, use the ticket id; otherwise `YYYY-MM-DD-short-slug`.
- **Artifact filenames** are fixed (`framed-intake.md`, `questions.md`, …) so stages and shells can find them by convention.
- **No implementation detail** in any product artifact. Describe observable behavior.
- **Re-verify current behavior each change.** Code may have drifted from docs; Research documents the system as it actually is today, with `file:line` references.
- Commands are self-contained prompts: each declares its own Input, Output, Gate, Rules, and Next. Do not rely on prior chat context inside a command.
