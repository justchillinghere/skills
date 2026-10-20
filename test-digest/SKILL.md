---
name: test-digest
description: Explain a PR/MR in plain language for a human who is about to read the code themselves — a map of the substantive changes, then every test as setup / action / check / why. Run ONLY when the user explicitly asks, e.g. "/test-digest", "разбери тесты в этом MR", "объясни, что тут тестируется". Never run it unasked. If the user starts reading an already-reviewed PR/MR themselves, you may offer it in one line, then wait. Accepts an optional focus ("/test-digest billing"). Works with GitHub PRs, GitLab MRs, or a local branch.
---

# Test Digest

The user runs this skill after the work is done: reviews have run, findings are closed,
conflicts are discussed. Now the user reads the code themselves and must understand it.
Agent-written PRs often add a lot of tests. This skill gives the picture before the code.

This skill explains. It does not review. Do not hunt for bugs, judge test quality, or list
coverage gaps — the reviewers already did that. Read-only: post nothing to the PR/MR.

## Get the change

Pick the first source that fits:

- GitHub PR link or number → `gh pr view <pr> --json baseRefName,title,body` and `gh pr diff <pr>`.
- GitLab MR link or number → `glab mr view <mr>` and `glab mr diff <mr>`.
- Nothing given → the current branch against its base: `git diff <base>...HEAD`.
  The base is the PR/MR target if one exists for this branch, else the default branch.

If the user gave a focus ("billing", a path, a feature), cover only that part.
Say in one line what you left out.

## Read before you write

- Read each changed test in full, not only its diff hunk.
- Follow fixtures, factories, and helpers to their source (`conftest.py`, factory files,
  test utils). The real setup usually hides there. A setup line you cannot explain from
  code you read is a guess — do not write guesses.
- Read the production code each test calls, enough to name the behavior it exercises.
- If this session has a Design Note, ExecPlan, task text, or PR/MR description, use it for
  the "why". It beats inference from code.

## Output

Write in the language of the conversation. Plain text in chat — no files, no artifacts.
Three sections, in this order.

### 1. Summary

Three to five sentences. What the change does for the system or the user, and the shape
of the tests (how many, which areas, which kind: unit / integration / e2e).

### 2. Map of substantive changes

The production changes that matter, grouped by behavior, not by file. Number the groups;
section 3 refers to them. One to three sentences each: what was there before, what is
there now. End each group with the main files as anchors.

Leave out noise: renames, formatting, moves, generated code, lockfiles, mechanical
boilerplate (a migration that only mirrors a model change, wiring, re-exports). If noise
is large, say so in one line ("plus ~40 files of renames and generated clients").

### 3. Tests, grouped by behavior

Group the tests under the map groups from section 2. Tests that cover no map group go
under a last group, "Other", with one line on what they cover.

For each test:

> **<What the test shows, as one plain sentence>** (`test_identifier`)
> - **Setup:** the world the test builds.
> - **Action:** what happens.
> - **Check:** what the test expects.
> - **Why:** the risk or the rule the test protects.

Example:

> **A retry after a failed generation does not charge twice** (`test_retry_does_not_double_charge`)
> - **Setup:** the user has 10 credits; the first generation fails at the provider.
> - **Action:** the user retries, and the generation succeeds.
> - **Check:** exactly 5 credits are charged in total, not 10.
> - **Why:** retries could charge the same generation twice.

## Language rules

These rules are the point of the skill.

- Speak the domain, not the code. "A user without a subscription who used up the daily
  limit", not `user_factory(subscription=None, quota=0)`.
- Code identifiers appear only as anchors, in parentheses or backticks, after the plain
  description. Never as the description.
- Keep numbers and thresholds that carry meaning ("the limit is 3 generations a day").
  Drop values that are arbitrary test data (a random email, an id).
- Mocks: say what is faked and why it matters, in plain words ("the payment provider is
  faked and always declines"), not the patch target.
- Why: name a concrete risk or rule. If you cannot tell from the code and the session
  context, write "unclear". Never invent a motive — "unclear" is a useful signal.
- Do not restate the same setup in every test. If a group shares it, state it once at the
  group head, and per test say only what differs.

## Scale

- Merge parametrized cases and near-identical tests into one entry with a "Variants:" line
  ("Variants: empty, null, over 255 characters").
- If there are more than about 30 tests: trivial tests (simple getters, plain validation,
  obvious wiring) get one line each — the plain sentence and the anchor. Keep the full
  four lines for tests whose setup, action, or reason is not obvious.
- Never drop a test silently. If you compress a block, say what it holds and how many.
