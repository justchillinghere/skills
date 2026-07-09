# Routing

Routing is the HTTP-equivalent boundary of an SPA: it translates URLs into mounted page trees and translates user navigation back into URL changes. Keep it thin.

## Default: File-Based Routing

Prefer **TanStack Router** with the file-based plugin. The router auto-generates a typed route tree from the `routes/` directory, gives a typed context, and supports loaders, guards (`beforeLoad`), and search-param schemas out of the box.

If the project already uses **React Router**, follow its conventions instead. Do not mix routers.

A typical layout:

```text
src/routes/
├── __root.tsx                # root layout, router context type
├── index.tsx                 # "/"
├── sign-in.tsx               # "/sign-in"
├── 403.tsx                   # "/403"
├── billing/
│   ├── route.tsx             # "/billing" layout segment
│   ├── index.tsx             # "/billing"
│   └── invoices.tsx          # "/billing/invoices"
└── settings/
    ├── route.tsx
    └── profile.tsx
```

Auto-generated route tree (`routeTree.gen.ts`) is checked into the repo or regenerated on `dev`/`build`. Treat it as generated code: do not hand-edit, but commit it for stable diffs.

## Route Files

A route file should:

- declare the route via the framework's API
- declare the typed search-param schema if the route reads search
- attach a guard (`beforeLoad`) and/or a loader if the route needs them
- render a thin component that mounts a page from `features/<F>/pages/`

It should not:

- contain business logic or data transformations
- declare its own layout primitives beyond a wrapping `<div>` for global concerns (alerts, breadcrumbs)
- call API functions directly

Sketch:

```tsx
export const Route = createFileRoute('/billing/invoices')({
  beforeLoad: requireCapability('canViewBilling'),
  validateSearch: invoiceSearchSchema.parse,
  component: RouteComponent,
})

function RouteComponent() {
  return <InvoicesPage />
}
```

## Root Route And Context

The root route (`__root.tsx`) declares the router context type and the top-level layout (sidebar, header, outlet). Context is the router's typed bag of dependencies — usually the QueryClient, an auth context, and analytics:

```ts
export interface RouterContext {
  queryClient: QueryClient
  authContext: AuthContextType
  analytics: Analytics
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootLayout,
  notFoundComponent: NotFound,
})
```

Context is provided once when constructing the router (in `App.tsx`). Guards and loaders read from it instead of importing singletons directly, which keeps them testable.

## Guards

Guards run before a route mounts. Use them for:

- redirecting unauthenticated users to a sign-in page
- enforcing capabilities/permissions
- hydrating route-required state (rare; usually a loader is better)

Guards should be small, pure factories that return a `beforeLoad` function. They take options and return a check:

```ts
export const requireCapability = (cap: Capability) => ({ context }) => {
  if (!context.authContext.capabilities?.has(cap)) {
    throw redirect({ to: '/403' })
  }
}
```

A guard should not perform data fetching. If a route needs data to decide where to send the user, that is a loader, not a guard.

Group reusable guards in `domains/auth/application/` or `utils/routeGuards.ts`.

## Loaders vs Hook-Driven Data

Two valid styles for fetching data on a page:

**Loader-driven** — declare data dependencies on the route; the router awaits them before mounting the component. Good for SSR-shaped flows, data that gates render, and search-param-driven queries that should be available immediately.

**Hook-driven** — the page component calls hooks (`useQuery`) inside `<Suspense>`. Good for highly composable pages, optional sections, and parallel fetches with independent loading states.

Prefer hook-driven for most SPA features — it keeps `application/` hooks as the single source of truth. Use loaders when:

- the data must be present before the page renders to avoid layout shift
- the route should preload data on hover (TanStack Router supports this)
- you need router-level error boundaries for the fetch

Mixing both is fine: a loader can `queryClient.ensureQueryData(...)` to warm the cache; the component still calls `useQuery` and reads from it.

## Layouts

Use route segments (`routes/billing/route.tsx`) as layout boundaries. A layout segment renders shared chrome (sub-nav, breadcrumbs, sidebar) plus an `<Outlet />`.

Avoid global layouts that conditionally hide chrome based on URL strings. Instead, use opt-out routes: a `/(auth)/sign-in.tsx` segment without the main layout is clearer than `if (pathname.startsWith('/sign-in')) return null` inside the global layout.

## Search Params

Treat search params as typed state. Validate with zod:

```ts
const invoiceSearchSchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  status: z.enum(['paid', 'unpaid', 'all']).default('all'),
})

validateSearch: invoiceSearchSchema.parse
```

Use search params for state that should be linkable, shareable, or survive reload: pagination, filters, tab selection. Read them with the framework's typed hook (`useSearch`) and write them with typed navigation (`navigate({ search: ... })`).

Do not store filter state in atoms when search params would do. Atoms are the right home for filter state only when the filter is genuinely local to the session and should not appear in the URL.

## Code-Splitting

The default file-based router code-splits each route automatically. Avoid manual `lazy()` boundaries inside features unless a specific module is large and rarely used (a heavy chart library, a rich-text editor).

## Navigation

Navigate via the framework's typed `Link` / `navigate`. Do not use `<a href>` for in-app navigation — it triggers a full reload.

For programmatic navigation from hooks (e.g. after a successful mutation), import the router instance or use the framework's `useNavigate`. Keep the navigation call at the call site of the mutation, not deep inside a domain method.

## Pitfalls

- Putting page layout, forms, or business logic directly inside route files.
- Performing data fetching inside guards.
- Calling singletons (auth, analytics) inside guards instead of reading them from router context.
- Using `<a href>` instead of typed `Link` for in-app links.
- Storing filter state in atoms when search params would also make the URL shareable.
- Hand-editing the generated route tree.
- Multiple routers in the same app (TanStack + React Router) — pick one.
