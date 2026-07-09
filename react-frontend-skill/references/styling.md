# Styling

Pick one styling approach. Mixing two costs more than picking the "wrong" one.

## The Three Reasonable Choices

### Tailwind CSS

Default for new projects unless you have a strong reason otherwise.

- Zero runtime cost. Class names compile to CSS.
- Encourages design-token consistency through `tailwind.config.ts`.
- Pairs well with Radix UI primitives for accessible, unstyled components.
- Trade-off: long class strings on elements; mitigate with `clsx`/`tailwind-merge` and component composition.

Add `tailwind-merge` and `clsx` (or `tailwind-variants` / `cva`) to manage variants. Define theme tokens (colors, spacing, font sizes) in `tailwind.config.ts`.

### CSS-in-JS (Emotion / styled-components)

Reasonable if the team already uses it or theming needs runtime dynamism.

- Co-locates styles with components.
- Strong theme support via `<ThemeProvider>` and `useTheme`.
- Trade-off: runtime cost, larger bundle, slower SSR. Picks SSR-friendly variants if SSR matters (rare in pure SPAs).

If you go this route, pick **Emotion** for new projects (smaller, better TS support). Use a single `theme.ts` exported from `config/` or `styles/`.

### CSS Modules

Reasonable for projects that want plain CSS with scoping.

- Zero runtime cost.
- Standard CSS, easy to onboard.
- Trade-off: no design-token enforcement out of the box; pair with CSS custom properties for theming.

## Don't Mix

Pick one and ban the others in code review. The cost of two systems is more than just bundle size:

- two ways to do the same thing → unclear which to use
- design tokens duplicated across systems
- harder to refactor or theme later

If migrating, do it as a single concerted effort, not opportunistically.

## Design Tokens

Whichever system you pick, keep tokens in one place. Tailwind: `tailwind.config.ts` `theme.extend`. CSS-in-JS: `theme.ts`. CSS modules: `:root` custom properties in `tokens.css`.

Token categories:

- Color (semantic — `primary`, `surface`, `text-muted`, not raw `slate-500`)
- Spacing scale
- Typography scale (size, weight, line-height)
- Radius scale
- Shadow scale
- Z-index scale (named, never raw)
- Motion (durations, easing)

Components reference tokens, never raw values.

## Theming And Dark Mode

Two patterns:

- **CSS variables**: define light/dark tokens on `:root[data-theme]` selectors; flip the attribute on `<html>`. Zero runtime, works for Tailwind (with `darkMode: 'class'` or `[data-theme]`) and CSS modules.
- **Provider state**: keep current theme in an atom or context, expose it through `useTheme`. Required for CSS-in-JS that re-renders on theme change.

Read system preference (`matchMedia('(prefers-color-scheme: dark)')`) once, persist user override in `localStorage`, expose through a single `useTheme` hook.

## Layout Primitives

Define a small set of layout primitives once, use everywhere:

- `Stack` — vertical flex with gap
- `Inline` / `Cluster` — horizontal flex with gap and wrap
- `Grid` — CSS grid with template/columns props
- `Center`, `Spacer`

These primitives keep components free of inline `display: flex; gap: 12px; flex-direction: column` repetition. Prefer them over `<div className="flex flex-col gap-3">` patterns when the same shape recurs.

## Responsive

Mobile-first. Define a small breakpoint set (`sm`, `md`, `lg`, `xl`), match the design's intent, and use it consistently.

For component-level responsive logic that CSS cannot express (showing a drawer on mobile, a popover on desktop), use a `useMediaQuery` hook reading from one source of breakpoint truth.

## Accessibility & Styling

- Color contrast meets WCAG AA. Verify in design tokens, not at use sites.
- Focus styles are visible by default. Do not strip `:focus-visible` outlines without replacement.
- Animations respect `prefers-reduced-motion`.
- Touch targets ≥ 44×44 px on mobile.

## Pitfalls

- Two styling systems in one app.
- Raw color/spacing values scattered across components instead of tokens.
- Inline styles (`style={{ ... }}`) for what design tokens should own.
- Z-index values picked at random; use a named scale.
- Stripping focus outlines for aesthetics.
- Importing component-library themes (MUI, Chakra) into a Tailwind project.
- Building a "Card" component six times in different feature folders.
