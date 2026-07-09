# skills

Canonical, user-level Agent Skills shared by Codex and Claude Code.

Each top-level directory containing `SKILL.md` is a portable skill. Run `just sync` after adding or updating a skill to point both harnesses at this repository:

- `~/.agents/skills/<skill-name>` for Codex
- `~/.claude/skills/<skill-name>` for Claude Code

`sync` refuses to replace a real directory, so it will not silently overwrite an unmanaged skill installation.

Claude-specific skills remain in `~/.claude/skills` and are intentionally not managed here.
