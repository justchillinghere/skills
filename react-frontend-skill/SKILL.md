---
name: react-frontend-skill
description: Build, scaffold, evolve, and maintain React frontend SPAs using Vite, TypeScript, file-based routing (TanStack Router or React Router), TanStack Query for server state, a typed API client generated from OpenAPI, an explicit feature/domain layout, ESLint/Prettier, and Vitest/RTL testing. Use when starting a new React app, adding pages or features, refactoring an existing SPA toward layered architecture, wiring server/client state, designing an API layer, or making decisions about where new code belongs.
---

# React Frontend

Use this skill to build single-page React applications with a layered, feature-oriented structure. It describes a default project style from first principles, sized to the app. Match the structure to what the app does today; layers, sub-packages, and providers are added when there is concrete code to put in them, not preemptively. The full layout below is the shape of a fully-grown app, not a checklist for a new scaffold. Local project docs and explicit user instructions override these defaults.

## Frontend Model

A frontend SPA is a long-running browser process that turns three streams of input into a rendered UI:

- URL changes from the router (deep links, navigation, back/forward).
- User interactions (clicks, typing, keyboard, focus).
- Remote data from HTTP/WebSocket APIs and from the browser itself (storage, location, system events).

The app should keep business behavior independent from how it is rendered. React, the router, fetch/HTTP libraries, and third-party SDKs are details at the edge of the system; domain logic and use cases should be testable without mounting a component or hitting a network.

## Render Flow

Default flow for a page-backed feature:

```text
URL change / navigation
  -> router resolves a route, runs guards/loaders
  -> page component mounts inside its layout
  -> page calls feature hooks (use cases) for data and actions
  -> hooks coordinate API client, server-state cache, client-state stores
  -> domain models normalize and enforce rules on the returned data
  -> presentational components render props, emit events
  -> user event -> mutation hook -> API call -> cache invalidation -> re-render
```

Default flow for a cross-cutting concern (auth, theme, analytics):

```text
process startup (index/main)
  -> create singletons (query client, store, API client, analytics)
  -> mount providers in a single composition root
  -> features consume providers through hooks
```

## Layer Responsibilities

- `routes/`: URL → page wiring. Route definitions, guards, loaders, layouts. No business logic; route components are thin.
- `features/<Feature>/pages/`: top-level page components for one product surface. Compose containers, layouts, and feature-level state.
- `features/<Feature>/containers/`: smart components that wire data hooks to presentational UI. Contain no JSX layout primitives beyond what is needed to host children.
- `features/<Feature>/components/`: feature-specific presentational UI. Props in, events out. No data fetching.
- `features/<Feature>/application/`: hooks that act as use cases — `useX`, `useCreateX`, `useTerminateX`. Coordinate API + cache + domain.
- `features/<Feature>/domain/`: pure types, models, value objects, derived computations, validation schemas. No React, no fetch, no router.
- `features/<Feature>/infrastructure/`: feature-scoped state stores (Jotai atoms, Zustand slices), local persistence, side-effect adapters.
- `domains/<domain>/`: cross-cutting business logic shared by features (auth, authorization, billing primitives). Same internal split as a feature, minus UI.
- `components/`: app-wide reusable UI primitives — Button, Input, Modal, Layout, Table, Tooltip. Presentational only.
- `hooks/`: app-wide reusable hooks — `useDebounce`, `useLocalStorage`, `useWindowSize`. No feature-specific data.
- `api/`: typed HTTP client(s), middleware, request/response types. One owner of the API surface.
- `services/`: wrappers for external SDKs that need React integration (analytics, error tracking) — provider + hook pairs.
- `store/`: global client-state singletons — query client, root atom store. Tiny by design.
- `config/`: third-party SDK initialization that runs at module load (Sentry, GA) and environment-driven config helpers.
- `constants/`, `utils/`, `types/`: self-explanatory. Keep narrow; do not let `utils/` become a dumping ground.
- `assets/`: images, SVGs, fonts.

Do not create a generic `core/`, `lib/`, or `common/` package by default. If a module does not have a clear owner, decide whether it is a UI primitive (`components/`), a hook (`hooks/`), an API concern (`api/`), composition (`index.tsx`), configuration (`config/`), or a small utility (`utils/`).

## Features vs Domains

This split is the most important architectural decision in this style.

- A **feature** is a product surface a user interacts with (Auth, Billing, VM, Settings). It owns UI, pages, containers, and the hooks that drive them.
- A **domain** is shared business logic that multiple features depend on (auth session, authorization/capabilities, money math). It has no UI.

If two features import the same logic, lift it into `domains/`. If a feature imports another feature, redesign — features should not depend on each other directly.

Default to a single feature until a product surface clearly needs its own folder. Empty `features/Foo/` with one component is overhead.

## Reference Layout (Fully-Grown App)

The layout below is the shape of an app that has grown into all its layers. A new scaffold ships only the parts it actually uses today — typically `routes/`, one feature, `components/`, `api/`, `store/`. Add `domains/`, `services/`, feature-internal `infrastructure/`, and similar packages when there is concrete code that belongs in them.

```text
<repo>/
├── index.html
├── vite.config.ts
├── tsconfig.json
├── package.json
├── public/
└── src/
    ├── index.tsx                   # composition root: providers, render
    ├── App.tsx                     # router instance, top-level effects
    ├── routes/                     # file-based routes, layouts, guards
    │   ├── __root.tsx
    │   ├── index.tsx
    │   └── <segment>/
    ├── features/
    │   └── <Feature>/
    │       ├── pages/
    │       ├── containers/
    │       ├── components/
    │       ├── application/        # hooks (use cases)
    │       ├── domain/             # pure types, models, schemas
    │       └── infrastructure/     # atoms, persistence, adapters
    ├── domains/
    │   └── <domain>/
    │       ├── domain/
    │       ├── application/
    │       └── infrastructure/
    ├── components/                 # app-wide UI primitives
    ├── hooks/                      # app-wide reusable hooks
    ├── api/                        # typed client, middleware, types
    ├── services/                   # external SDK wrappers (analytics, etc.)
    ├── store/                      # query client, root atom store
    ├── config/                     # SDK init, env helpers
    ├── constants/
    ├── utils/
    ├── types/
    └── assets/
```

## Defaults

- Use **Vite** + **React 18+** + **TypeScript strict**. Path alias `@/*` to `src/*`.
- Use **file-based routing** with TanStack Router (preferred) or React Router. Keep route components thin.
- Use **TanStack Query** for all server state. Do not store fetched data in component state, Redux, or atoms.
- Use **Jotai** or **Zustand** for cross-component client state. Use `useState`/`useReducer` for local state. Use URL search params for state that should survive reload or be shareable.
- Use a **typed API client** generated from OpenAPI (`openapi-fetch`, `orval`, or `hey-api`). Do not hand-write fetch calls in components.
- Use **react-hook-form** + **zod** for forms; share zod schemas with the domain layer when validation rules overlap.
- Use **ESLint** (typescript-eslint, react, react-hooks, simple-import-sort) and **Prettier**. Enforce in pre-commit.
- Use **Vitest** + **React Testing Library** + **MSW** for tests. Co-locate `*.test.tsx` next to source or under `__tests__/`.
- Use **error boundaries** and **Suspense** at route boundaries. Use a single global toast/notification component.
- Use one **composition root** (`index.tsx`) that mounts every provider in a fixed order. No provider should be created at module import time outside this file.
- Treat auth flows, design-system choice (CSS-in-JS vs Tailwind vs CSS modules), analytics provider, and deployment target as project-local decisions unless explicitly requested.

## Existing Projects

When modifying an existing app, first read local docs such as `AGENTS.md`, `CLAUDE.md`, `README.md`, and project-local skills. Inspect `package.json`, `vite.config.ts`, `tsconfig.json`, `src/index.tsx`, `src/routes/`, and one or two existing features to learn the conventions. Prefer the existing layout and idioms over the defaults in this skill — consistency inside a codebase is more valuable than matching this skill's reference layout.

When the existing layout is messier than this skill suggests, do not refactor opportunistically; only restructure when the task explicitly asks for it.

## Add A Feature

Use this path for a typical page-backed feature. Tests can be written before, alongside, or after implementation, but plan the test cases before changing code.

1. **Define the behavior**: route(s), data shown, mutations, loading/empty/error states, permissions, analytics events.
2. **Pick the home**: a new `features/<Feature>/`, an existing one, or — if it is shared business logic without UI — a domain under `domains/`.
3. **Domain first**: add types, zod schemas, and any pure model classes/functions in `features/<Feature>/domain/`. No imports from React, the router, or `api/`.
4. **Application hooks**: write `useXs` (query) and `useCreateX`/`useUpdateX`/`useDeleteX` (mutation) in `features/<Feature>/application/hooks/`. They call the typed API client and own query keys + invalidations.
5. **Infrastructure if needed**: add Jotai atoms / Zustand slice in `features/<Feature>/infrastructure/` for filter state, selection, drafts.
6. **Presentational components**: build dumb pieces in `features/<Feature>/components/`. No hooks beyond local UI state.
7. **Containers**: wire hooks to components in `features/<Feature>/containers/`.
8. **Page**: assemble layout + containers in `features/<Feature>/pages/`.
9. **Route**: add the file in `routes/`. Wire guards/loaders. Keep the route component a few lines.
10. **Tests**: domain logic with Vitest, hooks with RTL `renderHook` + MSW, components with RTL, page-level happy path.
11. **Analytics + error states**: add events through the analytics service hook; verify error boundary behavior.

## Pitfalls

- Do not fetch data in components. Wrap every API call in a hook in `application/`.
- Do not store server data in atoms, Redux, or component state. Use TanStack Query and read from its cache.
- Do not let features import from each other. Lift shared logic into `domains/`, shared UI into `components/`, shared hooks into `hooks/`.
- Do not let `domain/` import from React, the router, the API client, or any infrastructure.
- Do not create singletons (query client, API client, analytics, store) at the top of random modules. Create them once in `store/` or `services/` and mount through `index.tsx`.
- Do not couple route components to specific UI internals; route files should compose pages, not lay out forms.
- Do not duplicate types between API responses, domain models, and view props. Map at the boundary in hooks or domain models.
- Do not introduce a second styling system once one is chosen. Pick CSS-in-JS, Tailwind, or CSS modules and stick to it.
- Do not skip Suspense/error boundaries around routes; a single uncaught render error blanks the whole app.
- Do not put environment access (`import.meta.env.*`) in feature code. Read it once in `config/` and export typed values.
- Do not use `any` to silence TypeScript at boundaries; map to `unknown` and narrow.
- Do not generate prop drills three levels deep when composition or context would do.

## Detailed References

Read only what the task needs:

- `references/architecture.md`: conceptual model, dependency direction, package ownership, features vs domains, DTO boundaries between API/domain/view.
- `references/routing.md`: file-based routing, guards, loaders vs hook-driven data, layouts, code-splitting.
- `references/state-management.md`: server vs client vs local vs URL state, query keys, invalidation, atoms vs slices.
- `references/api-layer.md`: typed client from OpenAPI, middleware (auth, retry, logging), error normalization, hook patterns.
- `references/components.md`: presentational vs container split, composition, compound components, accessibility baseline, error boundaries.
- `references/feature-anatomy.md`: step-by-step scaffold of a new feature with concrete example structure.
- `references/testing.md`: Vitest, RTL, MSW, hook testing, accessible queries, naming, anti-patterns.
- `references/tooling.md`: Vite config, TS strict settings, path aliases, ESLint/Prettier baseline, scripts.
- `references/styling.md`: pick-one approach, design tokens, theming, dark mode.

Reusable starter snippets live in `assets/snippets/`, including `vite.config.ts.snippet`, `tsconfig.json.snippet`, `eslint.config.js.snippet`, `index.tsx.snippet`, `query-client.ts.snippet`, `api-client.ts.snippet`, `auth-middleware.ts.snippet`, `feature-query-hook.ts.snippet`, `feature-mutation-hook.ts.snippet`, `domain-model.ts.snippet`, `route-with-guard.tsx.snippet`, and `error-boundary.tsx.snippet`.
