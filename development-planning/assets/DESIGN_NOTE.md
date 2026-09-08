# Design Note (feature design + decisions)

A Design Note is the **decision** artifact for a change. It is where a human decides
*what* we build and *how it is shaped* — problem, domain, use cases, contracts — before
any code is written and before a long autonomous build starts.

It is NOT the step-by-step build plan. Concrete build order, file targets, test lists,
and progress tracking live in the ExecPlan (`exec-plan.md`), which is generated **from**
an approved Design Note. See `PLANS.md`.

## Who it is for, and why

- **The human decides it.** An agent may draft the Design Note from the product spec,
  but the domain model, use cases, and contracts are the human's call — this is the
  altitude where the human adds the most value and where past features went wrong.
- **Both agents build from it.** The shared head and the contract are the single source
  a backend agent and a frontend agent both build to, so two autonomous agents cannot
  re-derive the same entity differently.
- **It survives the feature, not forever.** It is the cross-session memory for the
  current task. Its lasting invariants and decisions (§5, §10) are what get promoted to
  durable memory when the work is done.

## How to author it

- **Decisions, not prose.** Every line is a decision, a fact, or an open question — not
  narration. If a section holds no decision, delete the section.
- **Concrete over abstract.** Prefer a small entity list, a Pydantic/JSON shape, or a
  state list over a paragraph describing them. It matches how people actually reason and
  reads faster.
- **Your altitude only.** Problem → domain → use cases → contracts. No method bodies, no
  SQL, no file layout — those belong in the ExecPlan.
- **Drop what does not apply.** This is not a checklist to fill completely. For a small
  change most sections vanish (see "Shapes" below).
- **One screen per section.** If a section drifts past a screen, it has fallen into
  ExecPlan territory — pull it back up.

## Ownership: shared head, contract seam, per-side tails

Not every section is shared between backend and frontend. Mark each section's owner.

| Part | Sections | Owner |
| --- | --- | --- |
| Head | Problem · Scope · Requirements · Domain Model · Rules · Use Cases · Open Questions | **shared** — one truth, handed to both agents |
| Seam | Interfaces / Contracts | **shared contract** — backend produces (Pydantic → OpenAPI), frontend consumes |
| Backend tail | Design (app/domain) · Data Model · Observability/Rollout · Implementation | **backend** |
| Frontend tail | Components · screens/states · flow branching | **frontend** (its own tail; consumes the contract) |

Same feature, different altitude per side. Example: the head says "place a person into an
organization"; the contract says the backend primitives (`POST /users` → 409 if exists,
`POST /organizations`, `POST /members`); the frontend tail is the wizard that calls them
and handles "phone already exists" as a UX branch. Nobody is wrong — each concern sits at
its own level.

## Skeleton

Copy this into `design-note.md` and fill only the relevant sections. `[owner]` markers
are guidance — keep or drop them.

    # <NNN> · <Feature name> — Design Note

    ## 1. Problem / Context            [shared]
    How the system works now · what the problem is · what outcome we want.

    ## 2. Scope                        [shared]
    ### Goals
    ### Non-goals

    ## 3. Requirements                 [shared]
    ### Functional (FR-1, FR-2, ...)
    ### Non-functional
    Only the relevant ones (performance, consistency, security, auditability,
    availability, backwards compatibility). Do not over-specify what does not matter.

    ## 4. Domain Model                 [shared]
    Entities we work with, before rules. Tag each: [existing] / [changed] / [new].
    Fields, relationships, and — briefly — who owns durable state and where the source
    of truth is. Text is enough; no UML.

    ## 5. Business Rules & Invariants  [shared]
    ### Invariants
    What the system must never allow, regardless of use case.
    ### Business rules
    Concrete behavior rules. Note which entity / aggregate each belongs to.
    (These are the promote-to-memory candidates on completion.)

    ## 6. Use Cases                    [shared]
    The unit of business behavior. Per use case, keep it short:
    Actor · Input · Preconditions · Rules · Result · Side effects · Failure cases.
    For non-trivial ones add transaction boundary, concurrency, idempotency.

    ## 7. Design                       [backend]
    How requirements/use cases land on the existing system. What we add / change /
    reuse / do not touch. Where new use cases and rules live (application vs domain).
    No designing classes for the sake of it. (Frontend keeps its component/flow design
    in its own tail.)

    ## 8. Data Model                   [backend]
    Only if data changes. New / changed tables, constraints, indexes.

    ## 9. Interfaces / Contracts       [seam]
    Only the interfaces that matter for this task. Request/response as JSON or Pydantic.
    API · events · jobs · external calls. Errors per endpoint.

    ## 10. Important Decisions / Trade-offs   [shared]
    Only where there was a real choice. Options → Decision → Why → Trade-off.
    A big, long-lived decision may graduate into its own ADR.

    ## 11. Edge Cases / Risks          [either]
    Only the significant ones: concurrency, partial failure, stale state, retries,
    migration/back-compat risk.

    ## 12. Observability / Rollout     [backend]
    If needed: logs, metrics, audit, feature flag, migration, backfill, staged rollout.

    ## 13. Implementation              [→ ExecPlan]
    A rough decomposition only. This is the hand-off seam: the ExecPlan expands it into
    the real ordered, codebase-anchored build plan.

    ## Open Questions                  [shared]
    Each unknown + how it will be resolved before build (mock / prior-art / ask).

## Shapes — drop what does not apply

- **Business feature** (e.g. "remove a user from an organization"):
  Context → Requirements → Domain Model → Rules → Use Cases → Contracts/Data → Implementation.
- **System change / infra** (e.g. "move Redis queues to SQS"):
  most of Domain/Use Cases disappears →
  Context → Requirements/NFR → Current Design → Proposed Design → Decisions/Trade-offs → Failure Modes → Rollout.
- **Large change**: nearly the whole skeleton.

## Hand-off

When the Design Note is approved (run the review lens first — see the skill's
`REVIEW_LENS.md`), it becomes the source for two things: the ExecPlan (execution) and
both build agents (shared head + contract). Do not start the ExecPlan until the Design
Note's head and contract are settled.
