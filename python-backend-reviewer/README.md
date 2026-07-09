# Python Backend Reviewer

Manual post-implementation review workflow for Python backend changes.

## Manual Use

From the repository you want to review, ask Codex:

```text
Use $python-backend-reviewer to review current changes.
```

Or run the packet builder directly:

```bash
python3 <skill-dir>/scripts/prepare_review_packet.py --manual
```

If Python/backend changes are detected, the script writes a packet under:

```text
<repo>/.agents/reviews/
```

Then spawn a separate reviewer subagent with the prompt printed by the script.

## Optional Hook Setup

The hook is intentionally not installed by default because it can slow down iterative work. To re-enable the user-scoped Stop hook later, run:

```bash
python3 <skill-dir>/scripts/install_user_hook.py
```

This adds a Stop hook to:

```text
~/.codex/hooks.json
```

The hook does not review code directly. It prepares a review packet only when Python/backend files changed, then asks the main agent to launch a separate reviewer subagent before final response.

To disable it again, remove this command from `~/.codex/hooks.json`:

```bash
python3 <skill-dir>/scripts/prepare_review_packet.py --hook-event stop
```
