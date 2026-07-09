# Centralize portable user-level skills

This ExecPlan is a living document. Maintain it according to `docs/PLANS.md`.

## Purpose / Big Picture

Create one Git repository at `/Users/leo/Projects/skills` as the source of truth for portable user-level Agent Skills. After completion, `just sync` links each top-level portable skill into both `~/.agents/skills` for Codex and `~/.claude/skills` for Claude Code without depending on the repository's old location.

## Progress

- [x] (2026-07-09) Inventory the existing user-level skill roots and identify portable candidates.
- [x] (2026-07-09) Create the repository and its planning structure.
- [x] (2026-07-09) Copy the seven selected portable skills into the repository.
- [x] (2026-07-09) Replace harness-specific installation copies with symlinks and remove only verified duplicate copies.
- [x] (2026-07-09) Correct portable skills that contain hard-coded harness paths.
- [x] (2026-07-09) Validate the managed links, Git state, and the `just sync` idempotence behavior.
- [ ] Commit, rename the branch to `main`, add the requested remote, and push the initial commit.

## Surprises & Discoveries

- Observation: `development-planning`, `dignified-python`, and `excalidraw-diagram` had byte-identical `SKILL.md` copies across their installed locations.
  Evidence: SHA-256 hashes from the inventory matched.
- Observation: the two `fastapi-backend-skill` copies differ in architectural guidance.
  Evidence: the user selected the `.agents` copy as canonical and asked to drop the older Claude copy.

## Decision Log

- Decision: Manage only the portable skills in this repository: `development-planning`, `dignified-python`, `fastapi-backend-skill`, `react-frontend-skill`, `excalidraw-diagram`, `python-backend-reviewer`, and `design-md`.
  Rationale: the user asked to leave the scanned Claude-specific skills untouched.
  Date/Author: 2026-07-09 / user and Codex
- Decision: Use the `.agents` copy of `fastapi-backend-skill` as canonical.
  Rationale: the user identified it as the latest version and expects to revise it later.
  Date/Author: 2026-07-09 / user
- Decision: `just sync` discovers only top-level directories that contain `SKILL.md`, and refuses to overwrite non-symlink paths.
  Rationale: new portable skills are automatically linked while unmanaged directories remain protected.
  Date/Author: 2026-07-09 / Codex

## Outcomes & Retrospective

Seven portable skills now live in this repository. Each is linked from both user-level discovery roots, while the six Claude-specific skill directories remain untouched. The Excalidraw renderer now reports setup commands using its own real script directory. The Python backend reviewer resolves the canonical skill library from its own location, so its packet and installed hook remain valid after the migration.

## Context and Orientation

The installed skill roots currently contain separate directories. Codex discovers user skills through `~/.agents/skills`; Claude Code discovers personal skills through `~/.claude/skills`. A symbolic link is a filesystem entry that points to a real directory elsewhere. The repository will contain the real directories, while both discovery roots contain links to them.

The excluded Claude-specific skills remain in `~/.claude/skills`: `peon-ping-config`, `peon-ping-use`, `peon-ping-log`, `peon-ping-toggle`, `sourcing-pipeline`, and `skill-developer`. `~/.codex/skills/development-planning` is a verified duplicate and will be removed after the canonical copy is established; Codex will use the managed `~/.agents/skills/development-planning` link.

## Plan of Work

Copy the selected canonical skill directories from the existing roots into the repository root. Use the `.agents` copy for every selected skill except `design-md`, which exists only in the Claude root. Preserve scripts, references, assets, and optional `agents/openai.yaml` files.

Revise `excalidraw-diagram/SKILL.md` and `python-backend-reviewer/SKILL.md` so their instructions locate their own `SKILL.md` directory rather than assuming `.claude/skills` or `.agents/skills`. Update any bundled Python scripts that make the same assumption.

Remove only the verified selected installation directories and duplicate copies. Then run `just sync` to install links for every repository skill into both user-level roots. Do not alter excluded Claude-specific directories.

## Concrete Steps

From `/Users/leo/Projects/skills`, run `just sync`. It should report links or unchanged links for every top-level skill directory. Inspect each link with `readlink` and confirm it resolves under `/Users/leo/Projects/skills`.

Run `just sync` a second time. The second run should only report `unchanged` messages, demonstrating idempotence.

Run `git status --short`, add the repository files, create the requested `first commit`, rename the branch to `main`, set `origin` to `git@github.com:justchillinghere/skills.git`, and push `main`.

## Validation and Acceptance

Acceptance requires seven real skill directories in the repository root, links to every one in both managed roots, no remaining real duplicate directory for those managed skill names, and all excluded Claude-specific skill directories still present. `just sync` must complete twice without changing any link on the second run. `git status --short` must be clean after the commit, and `git remote -v` must show the requested `origin` URL.

## Idempotence and Recovery

`just sync` is safe to repeat. It changes only symbolic links it manages and exits before replacing a real directory. If a migration step fails before old copies are deleted, rerun after comparing the canonical repository directory with the source. The Git repository retains the canonical copies for recovery.

## Artifacts and Notes

The canonical FastAPI directory is sourced from `~/.agents/skills/fastapi-backend-skill`. The older Claude copy is intentionally discarded by user direction.

## Interfaces and Dependencies

The `sync` recipe requires `zsh`, `mkdir`, `readlink`, `rm`, and `ln`, which are available on the target macOS environment. It treats a top-level directory with `SKILL.md` as the repository interface for a portable skill.

Plan created on 2026-07-09 to record the user-authorized centralization and link migration. Updated on 2026-07-09 after the migration and idempotence validation completed.
