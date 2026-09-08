# Design review lens (gap-finding questions)

A set of generic questions for grilling a Design Note **before** the ExecPlan is written
and the build starts. These are not part of the Design Note and are never copied into the
repository — the Design Note stays a clean fill-in structure ("what we write and how"),
and this file stays the separate lens ("what we might have missed").

How to use: after a Design Note draft exists, hand this file and the Design Note to a
**subagent with a clean context** — one that did not draft the note — and ask it to walk the
sections against these questions and return concrete gaps. A reviewer that shares the
author's context inherits the author's blind spots; a fresh one grills what the note
actually says. Walking it yourself in-context is the fallback when no subagent is available.
Skip any question that does not apply — this is a lens, not a checklist to satisfy.

Each question carries the failure it typically catches.

## Problem / scope

- Is every endpoint, field, and filter tied to a real screen or consumer? No speculative
  "for the future" surface? *(catches: shipping unused filters/columns/counters)*
- Are the non-functional requirements only the ones that matter here, not a reflexive
  latency/scale section? *(catches: over-engineering)*

## Domain

- Is any "new entity" actually without its own durable state — its own table, identity,
  source of truth? If so it is a **role / attribute / view** of an existing entity, and it
  gets no domain layer of its own. *(catches: an audience/role modeled as a module)*
- Does every durable state have exactly one source of truth, no duplicated truth?
- Are aggregate / transaction boundaries chosen deliberately?

## Behavior (use cases)

- Is this a single use case, or a **composite** of several? If composite, which primitives,
  and where does the orchestration live — frontend flow vs backend calls? *(catches: a
  fused "do everything" operation that hides its parts)*
- For create / place operations: is the **input state-space** enumerated (the grid)? For
  each cell, is it a valid path or a rejection — and **at which level** (backend contract
  vs frontend UX)? *(catches: modeling one cell of the matrix and treating the rest as
  errors)*
- Does each use case have an explicit actor, preconditions, and failure cases? Idempotency
  / transaction where non-trivial?

## Decomposition / design

- Along **what axis** are the parts split, and why is it the right one? Has an
  audience/actor (e.g. "admin") leaked into structure below the router where the logic is
  actually viewer-agnostic? *(catches: parallel per-audience modules/repos/DTOs)*
- Is "reuse / change / add / do not touch" stated explicitly? Is there a parallel stack
  being built for something that should be reused?

## Contracts

- For an entity that already has a contract elsewhere: new schema, or reuse the existing
  one? Is every field that diverges justified as genuinely viewer-relative — or removed?
  *(catches: near-duplicate schemas that silently drift apart)*
- Is the contract a single source shared by backend and frontend? Who produces it, who
  consumes it?

## Cross-cutting

- What here is **load-bearing** — a decision that determines the shape of everything above
  it — and is it settled before slicing/stacking work on top of it? *(catches: deferring
  the foundational decision and paying compound interest on it)*
- For each open question: how will it be closed before build (mock / prior-art / ask)?
