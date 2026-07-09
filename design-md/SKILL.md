---
name: design-md
description: Work with DESIGN.md files using Google's @google/design.md toolchain — author, edit, lint, diff, and export design systems. Use when the user asks to create or modify a DESIGN.md file, set up a design system in design.md format, generate Tailwind / CSS-variables / DTCG output from design tokens, adapt a glassmorphism or other community theme, or run the design.md CLI (lint/diff/export/spec).
---

# design.md skill

A self-contained reference for working with `DESIGN.md` files — Google's open format for describing a visual identity to coding agents. Use this in place of re-reading the GitHub docs each session.

Canonical source: <https://github.com/google-labs-code/design.md>. The CLI ships its own spec — when in doubt about an edge case, run `design.md spec --rules` for the always-current rules (see CLI section below).

## What DESIGN.md is

A plain-text file with two parts:

1. **YAML frontmatter** (delimited by `---` fences) — machine-readable design tokens: colors, typography, rounded, spacing, components.
2. **Markdown body** — `##` sections explaining design rationale and application guidelines.

Tokens are normative; prose is context. Tokens convert cleanly to/from `tokens.json` (DTCG), Figma variables, and Tailwind theme configs.

## CLI

The package binary is `design.md` (yes, with a dot). Two installation modes:

- **Global:** `npm install -g @google/design.md` → run `design.md <cmd>` directly.
- **Ad-hoc:** `npx -y @google/design.md@latest <cmd>` — no install, always latest.

Four commands, used in this order in a typical session:

| Command | Purpose | Example |
|---|---|---|
| `design.md spec --rules` | Output the full format spec (markdown) | Pipe to a file when learning a new edge case |
| `design.md lint <file>` | Validate structure, refs, contrast, section order | Run after every edit |
| `design.md diff <a> <b>` | Compare two versions for token changes | Spot regressions when iterating |
| `design.md export --format <tailwind\|dtcg> <file>` | Convert tokens to Tailwind config or DTCG JSON | Wire tokens into actual UI code |

After every meaningful edit, run `design.md lint` and address any errors before claiming the file is good. Warnings are judgment calls — usually fix `broken-ref` and `contrast-ratio`, sometimes ignore `orphaned-tokens` if intentional.

## Frontmatter schema

```yaml
---
version: alpha           # optional
name: <string>           # required
description: <string>    # optional
colors:
  <name>: "#RRGGBB"      # sRGB hex only
typography:
  <name>:
    fontFamily: <string>
    fontSize: <Dimension>           # px | em | rem
    fontWeight: <number>            # 100..900
    lineHeight: <Dimension|number>  # number = unitless multiplier (preferred)
    letterSpacing: <Dimension>
    fontFeature: <string>           # optional, font-feature-settings
    fontVariation: <string>         # optional, font-variation-settings
rounded:
  <scale>: <Dimension>              # xs/sm/md/lg/xl/full or any string
spacing:
  <scale>: <Dimension|number>
components:
  <component-name>:
    <prop>: <string|tokenRef>
---
```

**Color:** sRGB hex only (`"#1A1C1E"`). No `rgba()` in tokens — for transparency, write the literal `rgba(...)` value as a string under a component property.

**Token references:** wrap in braces — `"{colors.primary}"`, `"{spacing.lg}"`. Most token groups require references to a *primitive* leaf (e.g. `colors.primary-60`, not `colors`). The `components` section is the only place where references to *composite* values (like `{typography.label-md}`) are allowed.

**Component properties:** common keys are `backgroundColor`, `textColor`, `typography`, `rounded`, `padding`, `size`, `height`, `width`. Variants like hover/active are separate component entries with related names: `button-primary`, `button-primary-hover`.

## Section order (enforced)

Body uses `##` headings in this canonical order. Sections are optional but those present must appear in this sequence:

1. **Overview** (or "Brand & Style")
2. **Colors**
3. **Typography**
4. **Layout** (or "Layout & Spacing")
5. **Elevation & Depth** (or "Elevation")
6. **Shapes**
7. **Components**
8. **Do's and Don'ts**

Unknown sections are preserved without error but break the linter's `section-order` rule if interleaved.

An optional `<h1>` may appear for document title; not parsed as a section.

## Lint rules

| Rule | Severity | What it catches |
|---|---|---|
| `broken-ref` | error | Token reference points to nothing — fix immediately |
| `missing-primary` | warning | No primary color defined |
| `contrast-ratio` | warning | Component bg/text below WCAG AA 4.5:1 — usually fix |
| `orphaned-tokens` | warning | Defined color never referenced — review, may be intentional |
| `missing-typography` | warning | No typography tokens at all |
| `section-order` | warning | Sections out of canonical order |
| `token-summary` | info | Token counts (no action needed) |
| `missing-sections` | info | Optional sections absent |

## Authoring workflows

### Starting from scratch

1. Decide the brand mood (one paragraph for Overview).
2. Define the palette — at minimum `primary`, usually also `secondary`, `tertiary`, `neutral`, plus on-color variants for legibility (`on-primary`, `on-surface`, etc.).
3. Pick 1–2 typefaces and define 9–15 type levels: `display-*`, `headline-*`, `body-*`, `label-*`, `caption-*`.
4. Define `rounded` and `spacing` scales — keep to a base unit (usually 8px).
5. Define `components` for the recurring patterns in your UI: `button-primary`, `button-ghost`, `input-field`, `card-standard`, etc.
6. Write the prose sections explaining *why* the choices were made. Token names are abstract; prose names them ("Midnight Forest Green") and explains intent.
7. Lint, fix, commit.

### Adapting a community theme

If the user pastes a theme (e.g. from `designdotmd.directory`), don't rewrite from zero. Lift the frontmatter as a base, then:
- Rename tokens if the brand context differs.
- Replace prose with the new brand's voice.
- Re-derive component tokens if the new product has different surface needs (e.g. data tables vs. dashboards).
- Lint to surface contrast or section-order issues introduced by the edits.

### Exporting to UI

Two common export targets:

- **Tailwind config:** `design.md export --format tailwind DESIGN.md > tailwind.config.js`. Use Tailwind via CDN or build, classes map directly to tokens.
- **DTCG JSON:** `design.md export --format dtcg DESIGN.md > tokens.json`. Convert manually to CSS custom properties (`:root { --color-primary: ... }`) for vanilla CSS workflows.

Pick one and stick with it within a project. Mixing leads to drift.

## Where community themes live

| Source | Notes |
|---|---|
| `github.com/google-labs-code/design.md/tree/main/examples` | Official examples — directly fetchable. `atmospheric-glass` is the canonical glassmorphism reference. |
| `github.com/VoltAgent/awesome-design-md/tree/main/design-md` | Community collection inspired by major brands (Apple, Stripe, etc.). Directly fetchable. |
| `designdotmd.directory` | **SPA with hash routing** (`/#/d/<theme>`). `WebFetch` returns only the homepage shell. To use a theme from here, the user must open it in a browser and paste the markdown. |
| `getdesign.md`, `designmd.app/en/` | Alternative directories — try direct fetch first; many use SPA routing. |

When the user references a theme by name and a direct fetch fails, ask them to paste the markdown rather than guessing.

## Practical pitfalls

- **`rgba(...)` in tokens:** the `colors` map only accepts hex. For glass/translucent surfaces, store hex in `colors` and write `rgba(...)` literals as strings inside `components.<x>.backgroundColor`.
- **Glassmorphism on data-dense UIs:** blur + transparency over vibrant gradients hurts legibility on tables and forms. Recommend a hybrid (glass for hero/empty states, flat for data) before authoring.
- **Section order silently warned:** the linter only warns, doesn't error. Catch in code review.
- **Designdotmd.directory:** SPA-routed, raw markdown not directly fetchable. Don't waste fetch budget — ask for paste.
- **Composite token refs only in components:** `colors.primary` cannot reference `{typography.body-md}`. Only `components.<x>.<prop>` can reference composite values.
- **Font weight as string:** YAML accepts both `fontWeight: 600` and `fontWeight: "600"` — both valid. Don't "fix" one to the other.

## When to refresh from source

This skill captures stable parts of the format. If the user hits an unfamiliar lint rule, schema field, or CLI flag, run `design.md spec --rules` (or `npx -y @google/design.md@latest spec --rules`) — that's the always-current source of truth. Update this skill if you find genuinely new stable surface area worth caching.

## Project setup checklist

When starting a design system in a new project:

1. Confirm where `DESIGN.md` should live — typically project root.
2. Confirm install mode — global `design.md` (cross-project), local devDep (per-project pin), or pure `npx` (zero install).
3. Confirm export target — Tailwind config or DTCG/CSS variables — based on the UI stack.
4. Add a one-line note in the project's `CLAUDE.md` pointing to `DESIGN.md` and the chosen export target, so the project loads with that context.
5. Author or paste the initial `DESIGN.md`. Lint immediately to surface contrast issues early.
