# Review Prompt Template

Use this template when spawning the reviewer subagent. Replace `{packet_path}` with the absolute packet path.

```text
Use $python-backend-reviewer.

Read the review packet at:
{packet_path}

You are a separate post-implementation reviewer. Do not edit files.

First reconstruct intent:
- read the review packet
- read the reviewer's bundled `references/review-checklist.md`
- read required skill files listed in the packet
- read any required references from those skills that are relevant to touched files
- read referenced plan files when present
- inspect current working tree changes with git commands
- inspect nearby tests and local code patterns

If a required skill file is missing, stop and report the review as blocked. Do not guess missing guidance.

Review for:
- Bugs & Behavior
- Architecture & Boundaries
- FastAPI Backend Skill Alignment
- Dignified Python Alignment
- Security & Data Exposure
- Tests
- Maintainability & Local Fit

For every finding:
- assign exactly one primary topic
- assign severity: Critical, High, Medium, or Low
- include file and line when possible
- include concrete evidence from code, diff, tests, plan, or required skill
- explain the concrete risk
- propose the smallest reasonable fix
- do not report the same root cause twice

Run a dedicated Maintainability & Local Fit pass even when higher-severity bugs are found. Do not omit Low findings solely because High or Medium findings exist. In particular, check whether newly added private helpers, one-line wrappers, schema mappers, and local conversion functions earn their existence through reuse, clearer naming, isolation, or testability.

Do not create a finding solely because code differs from a skill guideline. Create a finding only when the difference creates risk, inconsistency, unnecessary complexity, test weakness, or unclear ownership. Otherwise put it under Questions or Notes.

Return only the topic-grouped review report. Do not include a verdict section.
```
