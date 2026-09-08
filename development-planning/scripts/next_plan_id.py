#!/usr/bin/env python3
"""Return the next local ExecPlan task ID or name."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


NUMBERED_NAME = re.compile(r"^(\d+)")
SLUG_ALLOWED = re.compile(r"[^a-z0-9]+")


def normalize_slug(raw_slug: str) -> str:
    slug = SLUG_ALLOWED.sub("-", raw_slug.lower()).strip("-")
    if not slug:
        raise SystemExit("slug must contain at least one letter or number")
    return slug


def used_ids(plans_dir: Path) -> set[int]:
    if not plans_dir.exists():
        return set()

    ids: set[int] = set()
    for path in plans_dir.rglob("*"):
        match = NUMBERED_NAME.match(path.name)
        if match is None:
            continue
        ids.add(int(match.group(1)))
    return ids


def next_id(plans_dir: Path) -> int:
    ids = used_ids(plans_dir)
    if not ids:
        return 1
    return max(ids) + 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find the next three-digit local ExecPlan task ID.",
    )
    parser.add_argument(
        "--plans-dir",
        default="docs/plans",
        help="Directory containing active and archived plans.",
    )
    parser.add_argument(
        "--slug",
        nargs="+",
        help="Optional task slug. It will be normalized to lowercase kebab-case.",
    )
    parser.add_argument(
        "--branch",
        help="Optional branch type prefix, for example feat, fix, or chore.",
    )
    args = parser.parse_args()

    identifier = f"{next_id(Path(args.plans_dir)):03d}"

    if args.slug is None:
        print(identifier)
        return

    slug = normalize_slug(" ".join(args.slug))
    name = f"{identifier}-{slug}"

    if args.branch is not None:
        branch = normalize_slug(args.branch)
        print(f"{branch}/{name}")
        return

    print(name)


if __name__ == "__main__":
    main()
