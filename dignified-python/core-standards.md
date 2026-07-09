# Style guide for writing dignified python

## WHY

Modern LLMs are trained on an enormous and unruly mix of code: questionable StackOverflow snippets, half-finished projects, and hobbyist repositories. When agents generate code from that background, the results can be fast but unfocused. Even when you don’t fully defer to them, the constant cycle of nudging, correcting, and rewriting can make development feel fragmented rather than cohesive.

My opinion is that intent has always mattered and we should build so other engineers never have to guess what a system is doing or why it behaves the way it does or spawn hidden bugs. LLMs are excellent at reproducing patterns, but they rarely understand the principles that make a codebase feel deliberate and unified.

Python’s flexibility amplifies this problem. There are often many valid ways to solve the same problem, and without guidance an LLM will default to whichever pattern it has seen most often. The result is code that technically works, but feels inconsistent. And can lead to a codebase that feels like it is authors with very different philosophies.

To address this, this codified document is created with opinions about how Python should be written into a set of rules called Dignified Python. Rather than relying on post-hoc cleanup through reviews or rewrites, the goal is to load these rules directly into the model’s context from the start. This gives agents a clear sense of our standards, conventions, and design philosophy.

By encoding intent upfront, we get the speed benefits of LLMs without sacrificing the clarity and consistency that make a shared codebase feel like a single system.

Python's flexibility is one of its greatest strengths, but that flexibility becomes a liability when agents are involved. There are often many valid ways to accomplish the same task, and without guidance an LLM will pick whichever pattern it has seen most frequently. The result is inconsistent code that feels like it was written by a dozen different people with a dozen different philosophies.

Being opinionated cuts through this. By defining clear guidelines and loading them into models' context, we can drastically accelerate our engineering velocity while maintaining the quality and consistency of our codebase. The key insight is that one must impart the expertise to the model. An LLM has no understanding of your team's conventions, your architectural decisions, or the hard-won lessons that shaped your codebase. By encoding that expertise into rules, you ensure the AI produces code that reflects your standards rather than generic patterns.

The goal of Dignified Python is not just to generate code that works, it is to generate code that communicates intent. That is where LLMs often fall short. Models are excellent at reproducing patterns, but far less adept at expressing the design principles behind them. Intent is not about choosing the right snippet; it is about applying a coherent philosophy for how Python should be used. The rules ensure that the code produced by agents reflects that philosophy.

## Rules to follow

This document contains the core Python coding standards that apply to 80%+ of Python code. These
principles are loaded with every skill invocation.

---

## The Cornerstone: LBYL Over EAFP

**Look Before You Leap: Check conditions proactively, NEVER use exceptions for control flow.**

```python
# CORRECT: Check first
if key in mapping:
    value = mapping[key]
    process(value)

# WRONG: Exception as control flow
try:
    value = mapping[key]
    process(value)
except KeyError:
    pass
```

---

## Exception Handling Basics

### Core Principle

**ALWAYS use LBYL, NEVER EAFP for control flow**

LBYL means checking conditions before acting. EAFP (Easier to Ask for Forgiveness than Permission)
means trying operations and catching exceptions. In dignified Python, we strongly prefer LBYL.

### Dictionary Access Patterns

```python
# CORRECT: Membership testing
if key in mapping:
    value = mapping[key]
    process(value)
else:
    handle_missing()

# ALSO CORRECT: .get() with default
value = mapping.get(key, default_value)
process(value)

# CORRECT: Check before nested access
if "config" in data and "timeout" in data["config"]:
    timeout = data["config"]["timeout"]

# WRONG: KeyError as control flow
try:
    value = mapping[key]
except KeyError:
    handle_missing()
```

### When Exceptions ARE Acceptable

Exceptions are ONLY acceptable at:

1. **Error boundaries** (API/service boundary level)
2. **Third-party API compatibility** (when no alternative exists)
3. **Adding context before re-raising**

**Default: Let exceptions bubble up to the boundary and process them there**

For detailed exception handling patterns including B904 chaining, third-party API examples, and
anti-patterns, see `references/exceptions.md`.

---

## Path Operations

### The Golden Rule

**ALWAYS check `.exists()` BEFORE `.resolve()` or `.is_relative_to()`**

### Why This Matters

- `.resolve()` raises `OSError` for non-existent paths
- `.is_relative_to()` raises `ValueError` for invalid comparisons
- Checking `.exists()` first avoids exceptions entirely (LBYL!)

### Correct Patterns

```python
from pathlib import Path

# CORRECT: Check exists first
for wt_path in worktree_paths:
    if wt_path.exists():
        wt_path_resolved = wt_path.resolve()
        if current_dir.is_relative_to(wt_path_resolved):
            current_worktree = wt_path_resolved
            break

# WRONG: Using exceptions for path validation
try:
    wt_path_resolved = wt_path.resolve()
    if current_dir.is_relative_to(wt_path_resolved):
        current_worktree = wt_path_resolved
except (OSError, ValueError):
    continue
```

### Pathlib Best Practices

**Always Use Pathlib (Never os.path)**

```python
# CORRECT: Use pathlib.Path
from pathlib import Path

config_file = Path.home() / ".config" / "app.yml"
if config_file.exists():
    content = config_file.read_text(encoding="utf-8")

# WRONG: Use os.path
import os.path
config_file = os.path.join(os.path.expanduser("~"), ".config", "app.yml")
```

**Always Specify Encoding**

```python
# CORRECT: Always specify encoding
content = path.read_text(encoding="utf-8")
path.write_text(data, encoding="utf-8")

# WRONG: Default encoding
content = path.read_text()  # Platform-dependent!
```

---

## Import Organization

### Core Rules

1. **Default: ALWAYS place imports at module level**
2. **Use absolute imports only** (no relative imports)
3. **Inline imports only for specific exceptions** (circular deps, TYPE_CHECKING, conditional
   features)

```python
# CORRECT: Module-level imports
import json
from pathlib import Path
from myapp.config import load_config

def my_function() -> None:
    data = json.loads(content)

# CORRECT: Absolute import
from myapp.config import load_config

# WRONG: Relative import
from .config import load_config

# WRONG: Inline imports without justification
def my_function() -> None:
    import json  # NEVER do this
```

For detailed inline import patterns and when they're legitimate, see `references/module_design.md`.

---

## Enums

### Prefer StrEnum For String-Valued Enums

If an enum's values are strings, use `enum.StrEnum` or `from enum import StrEnum` instead of `enum.Enum`.

```python
# CORRECT: string-valued enum uses StrEnum
from enum import StrEnum

class JobStatus(StrEnum):
    PENDING = "PENDING"
    DONE = "DONE"

# WRONG: string-valued enum uses Enum
import enum

class JobStatus(enum.Enum):
    PENDING = "PENDING"
    DONE = "DONE"
```

Use plain `Enum` only when the values are not strings or when string-enum behavior is explicitly undesirable.

---

## Logging: Always Use f-strings

**Use f-string formatting in all logger calls. Never use %-style or `.format()`.**

```python
# CORRECT: f-string
logger.info(f"Processing instance id={instance.id} step={step}")
logger.error(f"Failed to provision instance {inst.id}: {exc}")

# WRONG: %-style formatting
logger.info("Processing instance id=%s step=%s", instance.id, step)

# WRONG: .format()
logger.info("Processing instance id={} step={}".format(instance.id, step))
```

---

## Performance Guidelines

### Properties Must Be O(1)

```python
# WRONG: Property doing I/O
@property
def size(self) -> int:
    return self._fetch_from_db()

# CORRECT: Explicit method name
def fetch_size_from_db(self) -> int:
    return self._fetch_from_db()

# CORRECT: O(1) property
@property
def size(self) -> int:
    return self._cached_size
```

### Magic Methods Must Be O(1)

```python
# WRONG: __len__ doing iteration
def __len__(self) -> int:
    return sum(1 for _ in self._items)

# CORRECT: O(1) __len__
def __len__(self) -> int:
    return self._count
```

---

## None Is Not a Default — It's a Design Decision

**Values exist by default. `None` is only acceptable when absence is a meaningful domain concept.**

Most `| None` annotations are defensive laziness — agents add them because they're unsure if a value
will exist. This creates a cascade: one `Optional` parameter forces `if x is not None` checks
downstream, which forces more `Optional` return types, which forces more checks. The code becomes a
maze of None-guards instead of a clean flow.

```python
# WRONG: Defensive None everywhere
def create_deployment(
    provider: str | None = None,
    region: str | None = None,
    specs: DeploymentSpecs | None = None,
) -> Deployment | None:
    if provider is None:
        raise ValueError("provider required")  # Then why is it Optional?
    if specs is None:
        raise ValueError("specs required")
    ...

# CORRECT: Values are required — they exist
def create_deployment(
    provider: str,
    region: str,
    specs: DeploymentSpecs,
) -> Deployment:
    ...
```

```python
# WRONG: Optional env vars with None checks
def get_settings() -> Settings:
    db_url: str | None = os.environ.get("DATABASE_URL")
    if db_url is None:
        raise RuntimeError("DATABASE_URL not set")
    return Settings(db_url=db_url)

# CORRECT: Required values should fail loudly if missing
def get_settings() -> Settings:
    return Settings(db_url=os.environ["DATABASE_URL"])  # KeyError if missing — good
```

```python
# WRONG: None as "I don't know yet"
class OrderProcessor:
    def __init__(self):
        self.client: HttpClient | None = None  # "Will be set later"

    def process(self, order: Order):
        if self.client is None:
            raise RuntimeError("client not initialized")
        self.client.post(...)

# CORRECT: Required dependencies exist from construction
class OrderProcessor:
    def __init__(self, client: HttpClient):
        self.client = client

    def process(self, order: Order):
        self.client.post(...)
```

**When `None` IS meaningful:**

- Lookup that may not find a result: `def find_user(id: str) -> User | None`
- Truly optional configuration: `timeout: float | None` where None means "use system default"
- Database fields that are genuinely nullable by domain design

**The test:** Before adding `| None`, ask: *"Is absence a valid state in my domain, or am I just
unsure if I'll have the value?"* If unsure — make it required and let it fail. A crash on a missing
required value is a feature, not a bug.

---

## Anti-Patterns

### No Backwards Compatibility Preservation (Default)

```python
# WRONG: Keeping old API unnecessarily
def process_data(data: dict, legacy_format: bool = False) -> Result:
    if legacy_format:
        return legacy_process(data)
    return new_process(data)

# CORRECT: Break and migrate immediately
def process_data(data: dict) -> Result:
    return new_process(data)
```

### No Re-Exports: One Canonical Import Path

**Core Principle:** Every symbol has exactly one import path. Never re-export.

```python
# WRONG: __all__ exports create duplicate import paths
# myapp/__init__.py
from myapp.core import Process
__all__ = ["Process"]

# CORRECT: Empty __init__.py, import from canonical location
# from myapp.core import Process
```

**When re-exports ARE required** (plugin entry points): Use explicit `import X as X` syntax:

```python
# CORRECT: Explicit re-export syntax for required entry points
from myapp.core.feature import my_function as my_function
```

### Declare Variables Close to Use

```python
# WRONG: Variable declared far from use
def process_data(ctx, items):
    result_path = compute_result_path(ctx)  # Declared here...
    # 20+ lines of other logic...
    save_to_path(transformed, result_path)  # ...used here

# CORRECT: Inline at use site
def process_data(ctx, items):
    validate_items(items)
    transformed = transform_items(items)
    save_to_path(transformed, compute_result_path(ctx))
```

### Don't Destructure Objects Into Single-Use Locals

```python
# WRONG: Unnecessary field extraction
result = fetch_user(user_id)
name = result.name      # only used once below
email = result.email    # only used once below
send_notification(name, email, role)

# CORRECT: Access fields directly
user = fetch_user(user_id)
send_notification(user.name, user.email, user.role)
```

### No Single-Use Wrapper Helpers

**Do not extract a helper function just to rename one line of code.** A private helper must earn its
indirection.

Thin helpers that only call another function, wrap object construction, return the current time, or
forward fields into a schema usually make code harder to review. They force readers to jump between
functions without adding behavior, a boundary, or a reusable concept.

```python
# WRONG: Single-use wrapper around one constructor call
def _owner_invite_schema(read_model: OrganizationInviteReadModel) -> OwnerOrganizationInviteSchema:
    invite = read_model.invite
    return OwnerOrganizationInviteSchema(
        id=invite.id,
        organization=_organization_schema(read_model.organization),
        recipient_phone=invite.recipient_phone,
        role=invite.role,
        status=invite.status,
        expires_at=invite.expires_at,
        resolved_at=invite.resolved_at,
        created_at=invite.created_at,
    )

return _owner_invite_schema(read_model)

# CORRECT: Inline the construction where it is used once
invite = read_model.invite
return OwnerOrganizationInviteSchema(
    id=invite.id,
    organization=organization_schema_from_values(
        id=read_model.organization.id,
        public_code=read_model.organization.public_code,
        name=read_model.organization.name,
        country_code=read_model.organization.country_code,
        country_name=read_model.organization.country_name,
        city_option_id=read_model.organization.city_option_id,
        city_name=read_model.organization.city_name,
        city_admin_area=read_model.organization.city_admin_area,
        status=read_model.organization.status,
    ),
    recipient_phone=invite.recipient_phone,
    role=invite.role,
    status=invite.status,
    expires_at=invite.expires_at,
    resolved_at=invite.resolved_at,
    created_at=invite.created_at,
)
```

**Extraction threshold:** Do not create an abstraction for fewer than three meaningful lines of logic
unless one of these is true:

- The helper is reused in three or more places.
- The helper names a real domain operation or architectural boundary.
- The helper is required by a framework hook or dependency injection boundary, such as a FastAPI
  `Depends(get_user)` provider.
- The helper is a cached resource factory required to defer import-time work.
- The team explicitly agreed that the indirection is useful.

Keyword argument lists, field forwarding, and object construction boilerplate do not count as
meaningful logic.

Validation helpers are acceptable when they group a coherent policy, even if each individual check
is short:

```python
# CORRECT: Coherent policy with multiple checks and domain errors
def ensure_invite_previewable(
    read_model: OrganizationInviteReadModel | None,
    *,
    now: datetime,
) -> OrganizationInviteReadModel:
    if read_model is None:
        raise OrganizationInviteNotFoundError()
    if read_model.invite.status is not OrganizationInviteStatus.PENDING:
        raise OrganizationInviteNotPendingError(current_status=read_model.invite.status)
    if read_model.invite.expires_at <= now:
        raise OrganizationInviteExpiredError()
    return read_model
```

### Avoid Shallow Helper Chains

Function call depth is also part of readability. A useful function can call lower-level functions,
but avoid private helper chains where each layer only forwards to the next layer.

```python
# WRONG: Three layers, each doing one shallow action
def build_response(read_model: OrganizationInviteReadModel) -> OwnerOrganizationInviteSchema:
    return _owner_invite_schema(read_model)

def _owner_invite_schema(read_model: OrganizationInviteReadModel) -> OwnerOrganizationInviteSchema:
    return OwnerOrganizationInviteSchema(organization=_organization_schema(read_model.organization))

def _organization_schema(organization: OrganizationReadModel) -> OrganizationSchema:
    return organization_schema_from_values(id=organization.id, name=organization.name)
```

Keep normal application flow around two or three meaningful function calls deep. Deeper chains are
acceptable when each level is a real boundary with a clear responsibility, such as API route -> use
case -> repository, or service -> gateway -> client.

### Indentation Depth Limit

**Maximum indentation: 4 levels**

```python
# WRONG: Too deeply nested (5 levels)
def process_items(items):
    for item in items:
        if item.valid:
            for child in item.children:
                if child.enabled:
                    for grandchild in child.descendants:
                        pass  # 5 levels deep!

# CORRECT: Extract helper functions
def process_items(items):
    for item in items:
        if item.valid:
            process_children(item.children)

def process_children(children):
    for child in children:
        if child.enabled:
            process_descendants(child.descendants)
```

---

## Backwards Compatibility Philosophy

**Default stance: NO backwards compatibility preservation**

Only preserve backwards compatibility when:

- Code is clearly part of public API
- User explicitly requests it
- Migration cost is prohibitively high (rare)

Benefits:

- Cleaner, maintainable codebase
- Faster iteration
- No legacy code accumulation
- Simpler mental models

---

## See Also

For detailed guidance on specialized topics:

- **Exception chaining (B904)**: `references/exceptions.md`
- **ABC vs Protocol**: `references/interfaces.md`
- **typing.cast() assertions**: `references/typing-standards.md`
- **Import-time side effects, @cache**: `references/module_design.md`
- **Default parameters, keyword-only args**: `references/functions-interface-design.md`
- **All decision checklists**: `references/checklists.md`
