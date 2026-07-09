# State Management

State has more than one home. Pick the home before writing the code, not after.

## The Four Homes

In priority order — when more than one would work, prefer the higher-priority one:

1. **Server state** — TanStack Query. Anything originating from a server: lists, entities, pagination, mutations. Always.
2. **URL state** — search params and route params. Anything that should be linkable, shareable, or survive reload: filters, pagination, tabs, drawer-open flags.
3. **Cross-component client state** — Jotai atoms or Zustand slices. UI-only state that two or more unrelated components must share: a multi-step wizard's draft, a global selection set, modal queue.
4. **Local state** — `useState` / `useReducer`. State that lives inside one component or a small parent–child pair.

When you find yourself reaching for category 3 or 4 to hold server data, stop — that data belongs in TanStack Query's cache. When you find yourself reaching for category 3 to hold a filter, ask whether the URL should hold it instead.

## Server State (TanStack Query)

**One QueryClient per app**, created in `store/queryClient.ts` and passed via `QueryClientProvider` in `index.tsx`. Reuse it; do not new up clients per render or per feature.

### Query Keys

Treat keys as a typed namespace. Keep keys close to the hook that owns them:

```ts
const vmKeys = {
  all: ['vms'] as const,
  list: (filters: VmFilters) => [...vmKeys.all, 'list', filters] as const,
  detail: (id: string) => [...vmKeys.all, 'detail', id] as const,
}
```

This makes invalidation explicit (`queryClient.invalidateQueries({ queryKey: vmKeys.all })`) and avoids stringly-typed bugs.

For small apps, plain literal keys (`['vms', filters]`) are fine. Promote to a key factory when more than one mutation invalidates the same family.

### Defaults

Set sensible defaults on the QueryClient and override per-query:

```ts
new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      retry: 1,
    },
    mutations: { retry: 0 },
  },
})
```

Per-query overrides for known-volatile or known-static data: `staleTime: 0` for live status, `staleTime: Infinity` for an enum list that rarely changes.

### Mutations

A mutation hook owns four moments: `mutationFn`, `onMutate` (optimistic update + rollback context), `onError` (toast + rollback), `onSuccess` (toast + navigate), `onSettled` (invalidate). Centralize this — components should call `mutate(input)`, not write their own toast logic.

Invalidate at the lowest meaningful key. `invalidateQueries({ queryKey: vmKeys.all })` is fine; invalidating the whole cache is not.

For optimistic updates: snapshot the previous data in `onMutate`, set the optimistic value, restore in `onError`, refetch in `onSettled`.

### Suspense

Use `useSuspenseQuery` (or the framework's suspense mode) when a parent `<Suspense>` boundary should drive the loading state. This keeps page components free of `if (isLoading) return <Spinner />` ladders.

Wrap suspense queries in error boundaries — a thrown promise without a boundary blanks the tree.

### Pagination And Infinite

Use `keepPreviousData: true` for paginated tables to avoid layout flicker. Use `useInfiniteQuery` for infinite scroll, with a single key family that the API client knows how to extend with cursor/offset.

## URL State

Search params are a database. Validate them on read, type them on write.

```ts
const searchSchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  status: z.enum(['active', 'terminated', 'all']).default('active'),
})
```

Read with the framework's `useSearch`; write with typed `navigate({ search: ... })`. Components consume them through a small hook (`useVmFilters`) that wraps both directions.

When a filter belongs in URL state, every consumer reads it from URL state — do not duplicate into an atom "for convenience."

## Cross-Component Client State

Use **Jotai** by default; Zustand is also fine, especially for slices with related actions. Pick one and stick to it.

### Atoms

Keep atom definitions in `infrastructure/store.ts` of the feature that owns them:

```ts
export const vmStatusFilterAtom = atom<VmStatus>('active')
export const vmSelectionAtom = atom<Set<string>>(new Set())
```

Atoms should hold **small, serializable** values: enums, ids, primitives, simple objects. They should not hold:

- API responses (TanStack Query owns those)
- React refs, DOM nodes, class instances
- Promises (for async, use `atomWithQuery` only when not duplicating an existing query hook)

Cross-feature atoms (active modal, global theme) live in `store/`. If `store/` has more than five files, audit — most of them probably belong to a feature.

### When To Promote

Local → cross-component:

- two unrelated parents need the same value, and lifting state would cross unrelated subtrees
- a value should outlive a route change inside the same session

Cross-component → URL:

- a user reasonably expects to share or reload to the same view
- a filter or selection is meaningful enough to bookmark

URL → server-persisted:

- the user expects this to follow them across devices

## Local State

Default. Use `useState` for booleans, strings, small objects. Use `useReducer` when transitions are non-trivial (`'idle' | 'loading' | 'success' | 'error'`).

Do not reach for atoms to avoid prop drilling that is two levels deep. Composition or context is usually cleaner.

## Form State

Use **react-hook-form** + **zod**. Keep the zod schema in `domain/` so the same validation works in tests, server-side checks, and the form. Derive the TS type via `z.infer`.

Do not store form values in atoms or query cache. Form state is local to the form component.

## Derived State

Prefer derivation over caching. If `selectedCount = selectedIds.size`, do not store `selectedCount` — compute it. The exception is expensive derivation (memoize with `useMemo` or, in atoms, derived atoms).

## Patterns To Avoid

- A component that calls `useQuery`, then copies the result into `useState` "to make it editable." Use the form library and submit the patch back through a mutation.
- A component that reads from both URL state and an atom for "the same" filter. Pick one source.
- A custom global event bus. Atoms or query cache cover the same need with better tooling.
- `useEffect` chains that synchronize one piece of state into another. Compute it instead, or move ownership.
- Selectors that return new arrays/objects every render without memoization, causing re-render storms.

## Pitfalls

- Storing server data outside TanStack Query.
- Forgetting to invalidate after a mutation.
- Wide invalidations (`invalidateQueries()` with no key) on every mutation.
- Atom state that should have been search params, breaking link-sharing.
- Re-creating the QueryClient on each render.
- Reading `import.meta.env.VITE_*` directly in feature code instead of a typed `config/` export.
- Deeply nested context providers when a small atom would do.
