# Architecture

This frontend style separates business behavior from React, the router, and the network. The goal is that domain rules and use cases stay testable without rendering a tree, and that swapping the router or HTTP client is a contained change.

## Conceptual Model

The app has four kinds of code:

- **Presentation** receives input and shows output: routes, pages, containers, components.
- **Application** decides what should happen on input: hooks shaped as use cases, orchestrating data and side effects.
- **Domain** describes the business itself: types, models, value objects, validation, derived state.
- **Infrastructure** talks to the outside world: HTTP clients, browser storage, third-party SDKs, client-state stores.

Presentation should be thin. Infrastructure should be replaceable. Application and domain code should remain understandable without knowing React or the router.

## Dependency Rule

Dependencies point inward:

```text
routes/, pages/, containers/, components/
  -> features/<F>/application/ (hooks)
       -> features/<F>/domain/
       -> domains/<d>/domain/

features/<F>/infrastructure/, api/, services/
  -> features/<F>/domain/
  -> domains/<d>/domain/

index.tsx
  -> all layers (composition root)
```

The `domain/` layer never imports React, the router, the API client, atoms, browser APIs, or any other framework. The `application/` layer imports domain freely and infrastructure through narrow interfaces (the API client functions, the analytics hook). UI imports application; the composition root imports everything.

A quick check: open any file under `domain/`. If it has a `from 'react'`, `from '@tanstack/react-query'`, `from '@/api/...'`, or `from 'jotai'` import, it does not belong there.

## Features vs Domains

This is the load-bearing distinction in this style.

- **Feature** = product surface with UI. Owns pages, containers, components, the hooks that drive them, and feature-scoped state. Examples: `Auth`, `Billing`, `Settings`, `VM`.
- **Domain** = shared business logic without UI. Examples: `auth` (session, tokens), `authorization` (capabilities, role checks), `pricing` (formulas), `clock` (time semantics).

Heuristics for placement:

- One feature uses it → keep it inside the feature's `domain/`.
- Two or more features use it → lift to `domains/<name>/domain/`.
- It would still make sense in a CLI version of this product → it is domain, not feature.
- It is "how this surface looks" → it is feature, not domain.

Never let one feature import from another. If `Billing` needs something from `VM`, that something is either shared domain logic (move to `domains/`) or a UI primitive (move to `components/`). Cross-feature imports turn the layout back into a flat soup.

## Package Ownership (Reference Layout)

```text
src/
├── index.tsx
├── App.tsx
├── routes/
├── features/<F>/
│   ├── pages/
│   ├── containers/
│   ├── components/
│   ├── application/
│   ├── domain/
│   └── infrastructure/
├── domains/<d>/
│   ├── domain/
│   ├── application/
│   └── infrastructure/
├── components/
├── hooks/
├── api/
├── services/
├── store/
├── config/
├── constants/
├── utils/
├── types/
└── assets/
```

### `index.tsx`

Composition root. Creates singletons (query client, root store, API client, analytics) and mounts every provider in a single tree. The only file allowed to import concrete infrastructure to instantiate it.

Typical responsibilities:

- import side-effect-only config modules (Sentry, analytics init)
- create or import the QueryClient and root atom store
- mount providers in a fixed order: state → server-state → SDK contexts → app contexts → app
- render `<App />` into the DOM root

Do not put logic here beyond composition. Do not branch on environment except by reading typed values exported from `config/`.

### `App.tsx`

Owns the router instance and top-level effects that need access to providers (analytics page-view subscription, global keyboard shortcuts, theme bootstrap). Stays small.

### `routes/`

Owns URL → page mapping. Each route file declares the route, optional guard (`beforeLoad`), optional loader, and a thin component that renders a page from `features/`. Routes do not contain business logic, layout decisions beyond which page to render, or data fetching beyond what the loader returns.

### `features/<Feature>/`

Owns one product surface end-to-end.

- `pages/` — top-level page components used by route files. Responsible for layout-level composition: which containers, which feature-scoped state, which suspense boundaries.
- `containers/` — connect data hooks to presentational components. A container's job is to call hooks, pass data and callbacks down, and render a component tree. Containers do not style or lay out beyond what is needed to host children.
- `components/` — feature-specific presentational UI. Pure props in, callbacks out. No hooks beyond local UI state (`useState` for hover, `useId`).
- `application/` — hooks that are use cases. `useVms`, `useCreateVm`, `useTerminateVm`. They own query keys, mutation flow, optimistic updates, and analytics.
- `domain/` — types, zod schemas, model classes, value objects, derived calculations. Pure TypeScript.
- `infrastructure/` — Jotai atoms/Zustand slices for filters, selection, drafts; feature-local persistence; adapters that need feature-specific knowledge.

A new feature does not need every folder. Start with `pages/` + `application/` + `components/` and grow as the surface earns more code.

### `domains/<domain>/`

Same internal split as a feature, minus UI:

- `domain/` — pure types, models, schemas.
- `application/` — services and hooks that orchestrate domain logic, e.g. `AuthSessionManager`, `useCapabilities`.
- `infrastructure/` — token storage, session repositories, persistence adapters.

Use a domain when the same logic appears in two or more features, when the logic has its own lifecycle (auth session), or when it is naturally testable as a pure unit independent of any specific surface.

### `components/`

App-wide reusable UI primitives: layout (`Flex`, `Container`), inputs (`Button`, `Input`, `Select`, `Checkbox`), structural (`Modal`, `Drawer`, `Table`, `Tooltip`), feedback (`Toast`, `Skeleton`, `Loading`). No knowledge of specific features. No data fetching.

If a component needs feature data, it belongs in the feature's `containers/`, not here.

### `hooks/`

App-wide reusable hooks with no feature coupling: `useDebounce`, `useDebouncedValue`, `useLocalStorage`, `useWindowSize`, `useMediaQuery`, `useClickOutside`. No data fetching for specific endpoints — those live in feature `application/`.

### `api/`

Owns the HTTP surface:

- one typed client (e.g. `openapi-fetch` configured against a generated `paths` type)
- middleware (auth header injection, retry, telemetry, error normalization)
- typed request/response helpers if a generator is not used
- thin functions that wrap raw client calls when call sites benefit from a name

Hooks in `application/` import functions from `api/`; components do not.

If the app talks to multiple backends, give each its own client module (`api/userApi.ts`, `api/billingApi.ts`) with a shared middleware layer. Do not invent a generic "API service" class.

### `services/`

Wrappers for external SDKs that need React integration. Typical shape: an init function, a context, a provider component, and a `useX` hook.

Examples: analytics (`PostHog`, GA), error tracking (`Sentry`), feature flags, real-time channels.

`services/` differs from `api/`: `api/` is the app's own backend, `services/` is third-party SDKs.

### `store/`

Tiny by design. Exports the QueryClient instance and the root atom store. Maybe a couple of cross-cutting atoms (active modal, sidebar collapsed). If `store/` grows past a handful of files, those atoms probably belong in a feature's or domain's `infrastructure/`.

### `config/`

Module-load-time configuration of third-party SDKs (Sentry, GA, PostHog) and typed access to environment variables. Side-effect imports (`import '@/config/sentry'`) are acceptable here and only here.

### `constants/`, `utils/`, `types/`

- `constants/` — frozen values: route paths, query keys (when shared across features), enums of strings, magic numbers with a name.
- `utils/` — small helpers: formatters, parsers, predicates. No I/O. No React.
- `types/` — global TypeScript types shared across layers. Generated API types live in `api/` (or alongside the client).

`utils/` should not become a second `core/`. If a util grows internal state, multiple methods, or a lifecycle, it belongs in domain or infrastructure.

## DTO Boundaries

Keep type categories explicit:

- **API types** — generated from OpenAPI. Live in `api/`. Shape is dictated by the backend.
- **Domain models** — owned by `domain/`. Shape is dictated by the business. Often a class or readonly type with derived getters and methods.
- **View props** — owned by components. Shape is dictated by the UI's needs (often a subset or projection of a domain model).
- **Form values** — owned by react-hook-form + zod, lives near the form (often `domain/` for the schema, with `z.infer` for the type).
- **Atom state** — small, serializable, owned by `infrastructure/`.

Map at the boundaries:

- `api/` returns API types unchanged.
- `application/` hooks call the API and either return API types directly (when the shape is already useful) or map to domain models.
- `domain/` models accept API types in static factories like `Model.fromApi(...)` and expose business methods.
- Components accept the simplest type they need: a domain model, a slice of one, or a primitive.

Avoid using API types as form values, view props, or atom state across many call sites — bind happens too tight to the backend.

## Composition Root

There is exactly one composition root: `src/index.tsx`. It builds the React tree:

```text
StrictMode
  Jotai Provider (with shared store)
    QueryClientProvider (with shared client)
      ThirdPartyContexts (auth SDK, theme)
        AppContexts (Auth, Authorization, Analytics)
          App
            RouterProvider
              Routes
```

Order matters: things that other contexts read from must mount above. Keep the order documented in code comments only when the dependency is non-obvious (e.g. "auth context must be inside the SDK provider because it calls SDK hooks").

Do not create a second composition root in tests. Test setups can mount a subset of providers via a `renderWithProviders(node, { overrides })` helper.

## State Topology

Three or four state homes, used in this order:

1. **Server state** — TanStack Query. All data that originates from a server. Owned by `application/` hooks via `useQuery`/`useMutation`.
2. **URL state** — search params and route params. State that should survive reload, be linkable, or be navigated by browser back/forward.
3. **Client state (cross-component)** — Jotai atoms or Zustand slices. UI-only state that multiple components share: filters, selection, draft inputs spanning steps, modal open/close.
4. **Local state** — `useState`/`useReducer`. State that lives in one component's lifetime.

When two of these could work, prefer the lower-numbered one. Server state in atoms duplicates the cache. Cross-component state in `useState` causes prop drills. Local state in atoms makes components implicitly coupled.

## Pitfalls

- Treating `features/` as a flat namespace and letting features import each other.
- Putting React imports in `domain/`.
- Wrapping every component in a hook to "make it reusable" — composition over indirection.
- Generic `core/`, `lib/`, `common/` packages that swallow ungrouped code.
- Mixing `services/` (third-party SDKs) and `api/` (your backend) into one folder.
- Letting `utils/` accumulate small files that should have been domain methods.
- Hand-writing API types instead of generating them from OpenAPI.
- Storing API responses in atoms, defeating the query cache.
