---
description:
  Helper extraction, default parameter dangers, keyword-only arguments, ThreadPoolExecutor patterns,
  speculative test infrastructure.
---

# Functions interface design

**Read when**: Extracting helper functions, adding default parameters, functions with 5+ params,
using ThreadPoolExecutor

---

## Helper Extraction Must Reduce Complexity

**Do not create thin private helpers that only wrap a call, object initialization, current-time
lookup, or simple field mapping.** They add indirection without reducing complexity.

Use this threshold before extracting a helper:

- At least three meaningful lines of logic, or
- Reused in three or more places, or
- Represents a real domain operation, policy, architectural boundary, or framework hook, or
- Explicitly agreed because the local code reads better with the abstraction.

Keyword argument lists, field forwarding, and object construction boilerplate do not count as
meaningful logic.

```python
# WRONG: One-line wrapper used once
def _utc_now() -> datetime:
    return datetime.now(UTC)

expires_at = _utc_now() + INVITE_TTL

# CORRECT: Inline the one action
expires_at = datetime.now(UTC) + INVITE_TTL
```

```python
# WRONG: Wrapper just hides a constructor
def _public_invite_schema(read_model: OrganizationInviteReadModel) -> PublicOrganizationInviteSchema:
    invite = read_model.invite
    return PublicOrganizationInviteSchema(
        id=invite.id,
        organization=_organization_schema(read_model.organization),
        recipient_phone_masked=mask_phone(invite.recipient_phone),
        role=invite.role,
        status=invite.status,
        expires_at=invite.expires_at,
        created_at=invite.created_at,
    )

# CORRECT: If this is used once, build the schema at the call site
invite = read_model.invite
return PublicOrganizationInviteSchema(
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
    recipient_phone_masked=mask_phone(invite.recipient_phone),
    role=invite.role,
    status=invite.status,
    expires_at=invite.expires_at,
    created_at=invite.created_at,
)
```

**Acceptable small helpers:**

- FastAPI dependency functions such as `get_user` used by `Depends`
- `@cache` resource factories required to defer import-time work
- Interface implementations required by an ABC, Protocol, callback, or framework signature
- Small policy validators that group related checks and domain-specific errors

Avoid chaining private helpers when each layer only delegates to another helper. Keep common
application flow around two or three meaningful function calls deep unless each level is a real
boundary, such as route -> use case -> repository.

---

## Default Parameter Values Are Dangerous

> **Scope:** This rule applies to **function definitions** (`def foo(bar: bool = False)`), NOT to
> **function calls** where you pass an argument named `default` (e.g.,
> `some_func(default=True)`). Passing `default=True` to a function that accepts a `default`
> parameter is perfectly valid—you're not creating a default parameter value, you're explicitly
> providing a value.

**Avoid default parameter values unless absolutely necessary.** They are a significant source of
bugs.

**Why defaults are dangerous:**

1. **Silent incorrect behavior** - Callers forget to pass a parameter and get unexpected results
2. **Hidden coupling** - The default encodes an assumption that may not hold for all callers
3. **Audit difficulty** - Hard to verify all call sites are using the right value
4. **Refactoring hazard** - Adding a new parameter with a default doesn't trigger errors at existing
   call sites

```python
# DANGEROUS: Default that might be wrong for some callers
def process_file(path: Path, encoding: str = "utf-8") -> str:
    return path.read_text(encoding=encoding)

# Caller forgets encoding, silently gets wrong behavior for legacy file
content = process_file(legacy_latin1_file)  # Bug: should be encoding="latin-1"

# SAFER: Require explicit choice
def process_file(path: Path, encoding: str) -> str:
    return path.read_text(encoding=encoding)

# Caller must think about encoding
content = process_file(legacy_latin1_file, encoding="latin-1")
```

**When you discover a default is never overridden, eliminate it:**

```python
# If every call site uses the default...
create_order(ctx, provider, specs, validate=True)  # Always True
create_order(ctx, provider, specs, validate=True)  # Always True

# CORRECT: Remove the parameter entirely
def create_order(ctx, provider, specs) -> None:
    # Always validate - it's just the behavior
    ...
```

**Acceptable uses of defaults:**

1. **Truly optional behavior** - Where the default is correct for 95%+ of callers
2. **Backwards compatibility** - When adding a parameter to existing API (temporary)
3. **Test helper functions** - Functions in `tests/test_utils/` that exist to reduce test
   boilerplate are explicitly exempt. These helpers often wrap complex constructors (like
   `format_plan_header_body`) with sensible defaults, and having many default parameters is their
   intended purpose—not a code smell

**When reviewing code with defaults, ask:**

- Do all call sites actually want this default?
- Would a caller forgetting this parameter cause a bug?
- Is there a safer design that makes the choice explicit?

---

## Keyword-Only Arguments for Complex Functions

**Functions with 5 or more parameters MUST use keyword-only arguments.**

Use the `*` separator after the first positional parameter to enforce keyword-only at the language
level. This improves call-site readability by forcing explicit parameter names.

```python
# CORRECT: Keyword-only after first param
def fetch_data(
    url,
    *,
    timeout: float,
    retries: int,
    headers: dict[str, str],
    auth_token: str,
) -> Response:
    ...

# Call site is self-documenting
response = fetch_data(
    api_url,
    timeout=30.0,
    retries=3,
    headers={"Accept": "application/json"},
    auth_token=token,
)

# WRONG: All positional parameters
def fetch_data(
    url,
    timeout: float,
    retries: int,
    headers: dict[str, str],
    auth_token: str,
) -> Response:
    ...

# Call site is unreadable - what do these values mean?
response = fetch_data(api_url, 30.0, 3, {"Accept": "application/json"}, token)
```

**Exceptions:**

1. **`self`** - Always positional (Python requirement)
2. **`ctx` / context objects** - Can remain positional as the first parameter (convention)
3. **ABC/Protocol methods** - Exempt to avoid forcing all implementations to change signatures

```python
# CORRECT: ctx stays positional, rest are keyword-only
def create_deployment(
    ctx: AppContext,
    *,
    provider: str,
    specs: DeploymentSpecs,
    region: str,
    dry_run: bool,
) -> DeploymentResult:
    ...
```

---

## ThreadPoolExecutor.submit() Pattern

`ThreadPoolExecutor.submit()` passes arguments positionally to the callable. For functions with
keyword-only parameters, wrap the call in a lambda:

```python
# WRONG: submit() passes args positionally - fails with keyword-only functions
future = executor.submit(fetch_data, url, timeout, retries, headers, token)

# CORRECT: Lambda enables keyword arguments
future = executor.submit(
    lambda: fetch_data(
        url,
        timeout=timeout,
        retries=retries,
        headers=headers,
        auth_token=token,
    )
)
```

---

## Speculative Test Infrastructure

**Don't add parameters to fakes "just in case" they might be useful for testing.**

Fakes should mirror production interfaces. Adding test-only configuration knobs that never get used
creates dead code and false complexity.

```python
# WRONG: Test-only parameter that's never used in production
class FakeProvider:
    def __init__(
        self,
        offers: dict[str, Offer] | None = None,
        rate_limited: bool = False,  # "Might test this later"
    ) -> None:
        self._rate_limited = rate_limited  # Never set to True anywhere

# CORRECT: Only add infrastructure when you need it
class FakeProvider:
    def __init__(
        self,
        offers: dict[str, Offer] | None = None,
    ) -> None:
        ...
```

**The test for this:** If grep shows a parameter is only ever passed in test files, and those tests
are testing hypothetical scenarios rather than actual production behavior, delete both the parameter
and the tests.

---

## Speculative Tests

```python
# FORBIDDEN: Tests for future features
# def test_feature_we_might_add():
#     pass

# CORRECT: TDD for current implementation
def test_feature_being_built_now():
    result = new_feature()
    assert result == expected
```

---

## Decision Checklist

Before adding a default parameter value:

- [ ] Do 95%+ of callers actually want this default?
- [ ] Would forgetting to pass this parameter cause a subtle bug?
- [ ] Is there a safer design that makes the choice explicit?
- [ ] If the default is never overridden anywhere, should this parameter exist at all?

**Default: Require explicit values; eliminate unused defaults**

Before extracting a helper function:

- [ ] Does this helper contain at least three meaningful lines of logic?
- [ ] Is it reused in three or more places?
- [ ] Does it name a real domain operation, policy, boundary, or framework hook?
- [ ] Am I avoiding a private helper chain where each function only delegates to the next?

**Default: Inline single-use thin helpers**

Before adding a function with 5+ parameters:

- [ ] Have I added `*` after the first (or ctx) parameter?
- [ ] Is only `self`/`ctx` positional?
- [ ] Is this an ABC/Protocol method? (exempt)
- [ ] If using ThreadPoolExecutor.submit(), am I using a lambda wrapper?

**Default: All parameters after the first should be keyword-only**
