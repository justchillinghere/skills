#!/usr/bin/env python3
"""Prepare a Python backend review packet for manual use or a Codex Stop hook."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILL_LIBRARY_ROOT = SKILL_ROOT.parent
REVIEW_TEMPLATE_PATH = SKILL_ROOT / "references" / "review-prompt-template.md"

REQUIRED_SKILLS = [
    str(SKILL_ROOT / "SKILL.md"),
    str(SKILL_ROOT / "references" / "review-checklist.md"),
    str(SKILL_LIBRARY_ROOT / "fastapi-backend-skill" / "SKILL.md"),
    str(SKILL_LIBRARY_ROOT / "dignified-python" / "SKILL.md"),
]
PLAN_SKILL = str(SKILL_LIBRARY_ROOT / "development-planning" / "SKILL.md")

PYTHON_SUFFIXES = {".py"}
PYTHON_CONFIG_NAMES = {
    "pyproject.toml",
    "uv.lock",
    "requirements.txt",
    "requirements-dev.txt",
    "requirements-test.txt",
    "pytest.ini",
    "mypy.ini",
    "ruff.toml",
}
PYTHON_CONFIG_PREFIXES = ("requirements-",)
BACKEND_PATH_PARTS = {
    "alembic",
    "migrations",
    "tests",
}


@dataclass(frozen=True)
class ChangedFile:
    status: str
    path: str


def run_git(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def git_stdout(args: list[str], *, cwd: Path) -> str | None:
    result = run_git(args, cwd=cwd)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def repo_root(cwd: Path) -> Path | None:
    output = git_stdout(["rev-parse", "--show-toplevel"], cwd=cwd)
    if output is None or output == "":
        return None
    return Path(output).resolve()


def changed_files(root: Path) -> list[ChangedFile]:
    output = git_stdout(["status", "--short", "--untracked-files=all"], cwd=root)
    if output is None:
        return []

    files: list[ChangedFile] = []
    for line in output.splitlines():
        if len(line) < 4:
            continue
        status = line[:2].strip()
        raw_path = line[3:].strip()
        if " -> " in raw_path:
            raw_path = raw_path.split(" -> ", maxsplit=1)[1]
        files.append(ChangedFile(status=status, path=raw_path))
    return files


def is_python_backend_path(path: str) -> bool:
    path_obj = Path(path)
    if path_obj.suffix in PYTHON_SUFFIXES:
        return True
    if path_obj.name in PYTHON_CONFIG_NAMES:
        return True
    if path_obj.name.startswith(PYTHON_CONFIG_PREFIXES) and path_obj.suffix == ".txt":
        return True
    return bool(BACKEND_PATH_PARTS.intersection(path_obj.parts)) and path_obj.suffix == ".py"


def relevant_files(files: list[ChangedFile]) -> list[ChangedFile]:
    return [item for item in files if is_python_backend_path(item.path)]


def ensure_reviews_dir(root: Path) -> Path:
    reviews_dir = root / ".agents" / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    exclude_path = root / ".git" / "info" / "exclude"
    if exclude_path.exists():
        current = exclude_path.read_text(encoding="utf-8")
    else:
        exclude_path.parent.mkdir(parents=True, exist_ok=True)
        current = ""
    ignore_line = ".agents/reviews/"
    if ignore_line not in current.splitlines():
        suffix = "" if current.endswith("\n") or current == "" else "\n"
        exclude_path.write_text(f"{current}{suffix}{ignore_line}\n", encoding="utf-8")
    return reviews_dir


def detect_plan_files(root: Path) -> list[Path]:
    plans_root = root / "docs" / "plans" / "active"
    if not plans_root.exists():
        return []
    changed = {item.path for item in changed_files(root)}
    plan_paths: list[Path] = []
    for raw in sorted(changed):
        path = root / raw
        if path.suffix == ".md" and plans_root in path.parents:
            plan_paths.append(path.resolve())
    return plan_paths


def fingerprint(root: Path, files: list[ChangedFile]) -> str:
    hasher = hashlib.sha256()
    status = git_stdout(["status", "--short", "--untracked-files=all"], cwd=root) or ""
    hasher.update(str(root).encode("utf-8"))
    hasher.update(status.encode("utf-8"))
    for item in files:
        hasher.update(item.status.encode("utf-8"))
        hasher.update(item.path.encode("utf-8"))
        path = root / item.path
        if path.is_file():
            hasher.update(hashlib.sha256(path.read_bytes()).digest())
    return hasher.hexdigest()[:16]


def packet_path_for(reviews_dir: Path, digest: str) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return reviews_dir / f"python-backend-review-{stamp}-{digest}.md"


def latest_marker_path(reviews_dir: Path) -> Path:
    return reviews_dir / ".latest-python-backend-review.json"


def load_latest_marker(reviews_dir: Path) -> dict[str, str] | None:
    path = latest_marker_path(reviews_dir)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return {str(key): str(value) for key, value in data.items()}


def write_latest_marker(reviews_dir: Path, *, digest: str, packet_path: Path) -> None:
    latest_marker_path(reviews_dir).write_text(
        json.dumps(
            {
                "fingerprint": digest,
                "packet_path": str(packet_path),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def render_prompt(packet_path: Path) -> str:
    template_text = REVIEW_TEMPLATE_PATH.read_text(encoding="utf-8")
    return template_text.replace("{packet_path}", str(packet_path))


def write_packet(
    *,
    root: Path,
    cwd: Path,
    files: list[ChangedFile],
    plan_files: list[Path],
    packet_path: Path,
    digest: str,
) -> None:
    required_skills = [*REQUIRED_SKILLS]
    if plan_files:
        required_skills.append(PLAN_SKILL)

    changed_lines = "\n".join(f"- `{item.status}` `{item.path}`" for item in files)
    required_skill_lines = "\n".join(f"- `{path}`" for path in required_skills)
    expanded_required_skill_lines = "\n".join(
        f"- `{Path(path).expanduser()}`" for path in required_skills
    )
    plan_lines = "\n".join(f"- `{path}`" for path in plan_files) if plan_files else "- None detected"
    prompt = render_prompt(packet_path)

    packet = f"""# Python Backend Review Packet

Generated: {datetime.now(UTC).isoformat()}
Fingerprint: `{digest}`

## Repository

- Root: `{root}`
- Current directory: `{cwd}`

## Changed Python/Backend Files

{changed_lines}

## Required Skills

The reviewer must verify these files exist before reviewing:

{required_skill_lines}

Expanded paths for shell/file reads:

{expanded_required_skill_lines}

If any required skill file is missing, the reviewer must stop and report the review as blocked.

## Plan Files

{plan_lines}

When plan files are present, read them before judging architecture or acceptance criteria.

## Suggested Commands

Run only what is useful for the review:

```bash
git status --short --untracked-files=all
git diff --stat
git diff -- {' '.join(item.path for item in files)}
```

Inspect changed files, nearby tests, and local patterns with `rg`, `sed`, and focused test commands as needed.

## Review Scope

Review the current working tree changes for:

- Bugs & Behavior
- Architecture & Boundaries
- FastAPI Backend Skill Alignment
- Dignified Python Alignment
- Security & Data Exposure
- Tests
- Maintainability & Local Fit

Do not edit files. Return a report only.

## Subagent Prompt

{prompt}
"""
    packet_path.write_text(packet, encoding="utf-8")


def hook_json_noop() -> None:
    print(json.dumps({"continue": True, "suppressOutput": True}))


def hook_json_continue(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}))


def continuation_reason(packet_path: Path) -> str:
    return f"""Python backend review is required before final response.

A review packet has been prepared:
{packet_path}

Spawn a separate reviewer subagent with this prompt:

Use $python-backend-reviewer.
Read the review packet at:
{packet_path}

Review the current working tree changes according to the packet. Do not edit files. Return only the topic-grouped review report with severity-tagged findings.

After the reviewer returns, address each finding or explicitly explain why it is not applicable. Then provide the final response."""


def manual_output(packet_path: Path) -> None:
    print("Python backend review packet prepared:")
    print(packet_path)
    print()
    print("Spawn a separate reviewer subagent with:")
    print()
    print(f"Use $python-backend-reviewer.\nRead the review packet at:\n{packet_path}")
    print()
    print("Do not edit files. Return only the topic-grouped review report.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manual", action="store_true", help="Print human-readable output.")
    parser.add_argument("--hook-event", choices=["stop"], help="Emit JSON for the Codex hook event.")
    args = parser.parse_args()

    hook_mode = args.hook_event == "stop"
    if hook_mode:
        try:
            _ = json.loads(sys.stdin.read() or "{}")
        except json.JSONDecodeError:
            hook_json_noop()
            return 0

    cwd = Path.cwd().resolve()
    root = repo_root(cwd)
    if root is None:
        if hook_mode:
            hook_json_noop()
        else:
            print("python-backend-reviewer: not inside a git repository; noop")
        return 0

    changed = relevant_files(changed_files(root))
    if not changed:
        if hook_mode:
            hook_json_noop()
        else:
            print("python-backend-reviewer: no Python/backend changes detected; noop")
        return 0

    reviews_dir = ensure_reviews_dir(root)
    digest = fingerprint(root, changed)
    marker = load_latest_marker(reviews_dir)
    if hook_mode and marker is not None and marker.get("fingerprint") == digest:
        hook_json_noop()
        return 0

    packet_path = packet_path_for(reviews_dir, digest)
    plan_files = detect_plan_files(root)
    write_packet(
        root=root,
        cwd=cwd,
        files=changed,
        plan_files=plan_files,
        packet_path=packet_path,
        digest=digest,
    )
    write_latest_marker(reviews_dir, digest=digest, packet_path=packet_path)

    if hook_mode:
        hook_json_continue(continuation_reason(packet_path))
    else:
        manual_output(packet_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
