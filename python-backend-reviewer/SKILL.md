---
name: python-backend-reviewer
description: Post-implementation Python backend review workflow for Codex. Use when reviewing current working-tree Python/backend changes manually or from a Stop hook after code was written, especially to launch a separate reviewer subagent that checks bugs, architecture, FastAPI layering, Dignified Python alignment, security, tests, and maintainability without editing files.
---

# Python Backend Reviewer

Use this skill to run a separate post-implementation review for Python backend changes. The reviewer is report-only by default; the implementation agent remains responsible for deciding and applying fixes.

## Required External Skills

First resolve `SKILL_DIR` as the directory containing this `SKILL.md`; its parent is the canonical skill library. Require these files before reviewing:

- `$SKILL_DIR/../fastapi-backend-skill/SKILL.md`
- `$SKILL_DIR/../dignified-python/SKILL.md`

Require this file when the review packet includes plan files:

- `$SKILL_DIR/../development-planning/SKILL.md`

If a required skill file is missing, stop the review and report it as blocked. Do not infer or reconstruct missing skill guidance.

## Manual Workflow

When asked to review current Python backend changes:

1. Run `python3 "$SKILL_DIR/scripts/prepare_review_packet.py" --manual`.
2. If the script reports noop, say no Python/backend review is required.
3. If it writes a packet, spawn a separate reviewer subagent with the prompt from the script or packet.
4. The reviewer subagent must read the packet, required skills, relevant skill references, changed files, nearby tests, and local patterns.
5. After the reviewer returns, address each finding or explain why it is not applicable before the final response.

## Hook Workflow

The user-scoped Stop hook calls the same packet script. The hook does not review code. It detects relevant Python/backend changes, prepares a packet under the repository's `.agents/reviews/`, and asks the current agent to continue by launching the reviewer subagent.

The hook should noop for non-Python work.

## Review Packet

The packet intentionally does not include the full diff. It gives the reviewer stable context and commands to run:

- repository root and current directory
- changed Python/backend files
- base ref or HEAD comparison mode
- required skill paths
- plan files when detected or supplied
- suggested git commands
- topic-grouped report requirements

## Reviewer Contract

The reviewer must not edit files. It must produce a report only.

Before forming findings, the reviewer must reconstruct intent from the packet, plan files, current diff, tests, and local code style. The reviewer must read required skills thoroughly enough to apply their guidance, including referenced files that are relevant to the touched areas.

Use `references/review-checklist.md` for finding criteria, severity ranking, and topic definitions. Use `references/review-prompt-template.md` for the subagent prompt shape.

## Finding Rules

A finding must have all of:

- observation
- violated expectation
- concrete risk
- affected location
- actionable correction

Do not create findings for taste alone. If a guideline deviation may be justified by local context, put it under Questions or Notes instead of treating it as a defect.

Group findings by topic and tag each finding with severity. Omit empty topic sections.
