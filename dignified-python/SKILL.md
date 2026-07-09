---
name: dignified-python
description: Opinionated Python coding standards for this repository. Use when writing, reviewing, or refactoring Python to enforce LBYL-over-EAFP flow control, pathlib-first path handling, absolute imports, explicit error boundaries, version-correct type syntax (Python 3.10-3.13), and interface/function design rules (ABC/Protocol decisions, keyword-only parameters, default-parameter discipline, minimal helper extraction).
---

# Dignified Python

Read files in this order to keep context focused and deterministic.

## 1) Load Core Standards

- Read `core-standards.md` first for default rules that apply in most edits.

## 2) Detect Python Version and Load Version Rules

Identify minimum supported Python version in this order:

1. `pyproject.toml` -> `requires-python`
2. `setup.py` or `setup.cfg` -> `python_requires`
3. `.python-version`
4. Default to Python 3.12 when unspecified

Then load one file:

- `versions/python-3.10.md`
- `versions/python-3.11.md`
- `versions/python-3.12.md`
- `versions/python-3.13.md`

## 3) Load References Only When Triggered

- `references/exceptions.md`: Write `try/except`, chain exceptions, or wrap third-party APIs.
- `references/interfaces.md`: Design ABC/Protocol interfaces or gateway ports.
- `references/typing-standards.md`: Use `typing.cast`, `Literal`, narrowing, or runtime assertion patterns.
- `references/module_design.md`: Add module-level code, caching, or inline imports.
- `references/functions-interface-design.md`: Design function signatures, extract helper functions, defaults, keyword-only args, or `ThreadPoolExecutor.submit` call style.
- `references/checklists.md`: Run a final rule compliance pass before completion.

## 4) Apply During Work

- Prefer LBYL checks instead of exceptions for control flow.
- Keep exceptions at explicit error boundaries or unavoidable interoperability points.
- Use `pathlib.Path` and explicit `encoding="utf-8"` for text IO.
- Keep imports absolute and module-level unless a documented exception applies.
- Require explicit values by default; treat `None` and default params as design choices.
- Enforce readable call sites with keyword-only arguments for higher-arity functions.
- Avoid thin wrapper helpers and shallow private helper chains unless they are reused heavily or required by a framework boundary.
