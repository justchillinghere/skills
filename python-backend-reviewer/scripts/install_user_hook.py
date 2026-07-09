#!/usr/bin/env python3
"""Install the user-scoped Codex Stop hook for python-backend-reviewer."""

from __future__ import annotations

import json
import shlex
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
HOOK_COMMAND = (
    f"python3 {shlex.quote(str(SKILL_ROOT / 'scripts' / 'prepare_review_packet.py'))} "
    "--hook-event stop"
)


def load_hooks(path: Path) -> dict:
    if not path.exists():
        return {"hooks": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError(f"{path} field 'hooks' must be an object")
    return data


def main() -> int:
    hooks_path = Path("~/.codex/hooks.json").expanduser()
    hooks_path.parent.mkdir(parents=True, exist_ok=True)
    data = load_hooks(hooks_path)
    stop_hooks = data["hooks"].setdefault("Stop", [])
    if not isinstance(stop_hooks, list):
        raise ValueError("hooks.Stop must be a list")

    hook_group = {
        "hooks": [
            {
                "type": "command",
                "command": HOOK_COMMAND,
                "timeout": 30,
                "statusMessage": "Checking Python backend review requirement",
            }
        ]
    }

    for existing in stop_hooks:
        if not isinstance(existing, dict):
            continue
        for hook in existing.get("hooks", []):
            if isinstance(hook, dict) and hook.get("command") == HOOK_COMMAND:
                print(f"Hook already installed in {hooks_path}")
                return 0

    stop_hooks.append(hook_group)
    hooks_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Installed hook in {hooks_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
