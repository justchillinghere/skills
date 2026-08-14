#!/usr/bin/env python3
"""Validate product spec documents against the structure the skill requires.

Two modes:

  Canonical  — ``product/specs/<capability>/spec.md``, the current-truth store.
               Every requirement needs a ``Verified:`` marker.

  Delta      — ``<change-dir>/spec.md``, one in-flight product change.
               Requirements sit under ``## ADDED|MODIFIED|REMOVED Requirements``
               and each needs a ``Capability:`` routing line.

Usage:

    python3 validate_spec.py product/specs/
    python3 validate_spec.py product/changes/2026-08-14-foo/spec.md --delta

Exit status is 0 when every checked file passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REQUIREMENT_RE = re.compile(r"^### Requirement:\s*(\S.*?)\s*$")
SCENARIO_RE = re.compile(r"^#### Scenario:\s*(\S.*?)\s*$")
SECTION_RE = re.compile(r"^##(?!#)\s*(\S.*?)\s*$")
DELTA_SECTION_RE = re.compile(r"^(ADDED|MODIFIED|REMOVED) Requirements$")
TITLE_RE = re.compile(r"^# Spec:\s*(\S.*?)\s*$")

CYRILLIC_RE = re.compile(r"[Ѐ-ӿ]")
MODAL_RE = re.compile(r"\b(?:SHALL|MUST|SHOULD)\b")
VERIFIED_RE = re.compile(r"^Verified:\s*(?:\d{4}-\d{2}-\d{2}|NO)\b")
CAPABILITY_RE = re.compile(r"^Capability:\s*[a-z0-9][a-z0-9-]*$")
WHEN_RE = re.compile(r"^\s*-\s+\*\*WHEN\*\*\s+\S")
THEN_RE = re.compile(r"^\s*-\s+\*\*THEN\*\*\s+\S")

REQUIRED_CANONICAL_SECTIONS = ("Purpose", "Requirements")


@dataclass
class Scenario:
    name: str
    line: int
    body: list[str] = field(default_factory=list)


@dataclass
class Requirement:
    name: str
    line: int
    section: str
    body: list[str] = field(default_factory=list)
    scenarios: list[Scenario] = field(default_factory=list)


@dataclass
class Document:
    path: Path
    title: str | None = None
    sections: list[str] = field(default_factory=list)
    requirements: list[Requirement] = field(default_factory=list)


def parse(path: Path, text: str) -> Document:
    """Split a spec file into sections, requirements, and nested scenarios."""
    doc = Document(path=path)
    section = ""
    requirement: Requirement | None = None
    scenario: Scenario | None = None

    for number, raw in enumerate(text.splitlines(), start=1):
        title_match = TITLE_RE.match(raw)
        if title_match is not None:
            doc.title = title_match.group(1)
            continue

        section_match = SECTION_RE.match(raw)
        if section_match is not None:
            section = section_match.group(1)
            doc.sections.append(section)
            requirement = None
            scenario = None
            continue

        requirement_match = REQUIREMENT_RE.match(raw)
        if requirement_match is not None:
            requirement = Requirement(
                name=requirement_match.group(1), line=number, section=section
            )
            doc.requirements.append(requirement)
            scenario = None
            continue

        scenario_match = SCENARIO_RE.match(raw)
        if scenario_match is not None and requirement is not None:
            scenario = Scenario(name=scenario_match.group(1), line=number)
            requirement.scenarios.append(scenario)
            continue

        if scenario is not None:
            scenario.body.append(raw)
        elif requirement is not None:
            requirement.body.append(raw)

    return doc


def check_scenario(scenario: Scenario, requirement: Requirement) -> list[str]:
    problems: list[str] = []
    label = f"{requirement.name} / {scenario.name}"

    if not any(WHEN_RE.match(line) for line in scenario.body):
        problems.append(f"{scenario.line}: scenario '{label}' has no '- **WHEN**' line")
    if not any(THEN_RE.match(line) for line in scenario.body):
        problems.append(f"{scenario.line}: scenario '{label}' has no '- **THEN**' line")

    return problems


def check_requirement(requirement: Requirement, *, delta: bool) -> list[str]:
    problems: list[str] = []
    body = requirement.body
    removed = delta and requirement.section == "REMOVED Requirements"

    if delta:
        if not any(CAPABILITY_RE.match(line) for line in body):
            problems.append(
                f"{requirement.line}: requirement '{requirement.name}' has no "
                f"'Capability: <name>' routing line"
            )
    elif not any(VERIFIED_RE.match(line) for line in body):
        problems.append(
            f"{requirement.line}: requirement '{requirement.name}' has no "
            f"'Verified: <YYYY-MM-DD|NO>' marker"
        )

    if removed:
        if requirement.scenarios:
            problems.append(
                f"{requirement.line}: REMOVED requirement '{requirement.name}' "
                f"must not carry scenarios"
            )
        return problems

    if not requirement.scenarios:
        problems.append(
            f"{requirement.line}: requirement '{requirement.name}' has no scenario"
        )
    if not any(MODAL_RE.search(line) for line in body):
        problems.append(
            f"{requirement.line}: requirement '{requirement.name}' states no "
            f"SHALL/MUST/SHOULD behavior"
        )

    for scenario in requirement.scenarios:
        problems.extend(check_scenario(scenario, requirement))

    return problems


def check_document(doc: Document, *, delta: bool) -> list[str]:
    problems: list[str] = []

    if delta:
        delta_sections = [s for s in doc.sections if DELTA_SECTION_RE.match(s)]
        if not delta_sections:
            problems.append(
                "0: no '## ADDED|MODIFIED|REMOVED Requirements' section found"
            )
        for requirement in doc.requirements:
            if not DELTA_SECTION_RE.match(requirement.section):
                problems.append(
                    f"{requirement.line}: requirement '{requirement.name}' sits "
                    f"under '## {requirement.section}', not a delta section"
                )
    else:
        if doc.title is None:
            problems.append("0: missing '# Spec: <capability>' title")
        for required in REQUIRED_CANONICAL_SECTIONS:
            if required not in doc.sections:
                problems.append(f"0: missing '## {required}' section")
        if not doc.requirements:
            problems.append("0: no '### Requirement:' blocks found")

    seen: dict[str, int] = {}
    for requirement in doc.requirements:
        first = seen.get(requirement.name)
        if first is not None:
            problems.append(
                f"{requirement.line}: duplicate requirement name "
                f"'{requirement.name}' (first at line {first})"
            )
        else:
            seen[requirement.name] = requirement.line
        problems.extend(check_requirement(requirement, delta=delta))

    return problems


def check_language(text: str) -> list[str]:
    """Specs are English regardless of the language of surrounding product docs."""
    problems: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if CYRILLIC_RE.search(line):
            problems.append(f"{number}: non-English (Cyrillic) text in spec")
            break
    return problems


def collect_targets(root: Path, *, delta: bool) -> list[Path]:
    if root.is_file():
        return [root]
    if not root.is_dir():
        return []
    pattern = "*.md" if delta else "**/spec.md"
    return sorted(root.glob(pattern))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="spec file, or directory to walk")
    parser.add_argument(
        "--delta",
        action="store_true",
        help="validate a change-folder spec.md instead of a canonical spec",
    )
    args = parser.parse_args()

    if not args.path.exists():
        print(f"error: no such path: {args.path}", file=sys.stderr)
        return 1

    targets = collect_targets(args.path, delta=args.delta)
    if not targets:
        print(f"error: no spec files found under {args.path}", file=sys.stderr)
        return 1

    failed = 0
    for target in targets:
        text = target.read_text(encoding="utf-8")
        problems = check_language(text)
        problems.extend(check_document(parse(target, text), delta=args.delta))

        if problems:
            failed += 1
            print(f"FAIL {target}")
            for problem in problems:
                print(f"  {target}:{problem}")
        else:
            print(f"ok   {target}")

    print(f"\n{len(targets) - failed}/{len(targets)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
