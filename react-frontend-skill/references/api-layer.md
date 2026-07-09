# API Layer

The API layer is the only place that knows the backend's URL, headers, and wire format. Everything above it (hooks, domain, components) sees typed functions and typed responses.

## One Typed Client

Generate types from the backend's OpenAPI document. Two solid options:

- **`openapi-fetch`** + `openapi-typescript` — minimal, generates a `paths` type from OpenAPI; the runtime client is ~5 KB, types are derived at request time.
- **`orval`** or **`hey-api`** — generate full SDK functions and TS types from OpenAPI. More code, less inference at call sites.

Default to `openapi-fetch` for small/medium apps. Switch to `orval`/`hey-api` when call sites benefit from named functions or when teams want a generated SDK with hooks per endpoint.

Either way, **do not hand-write fetch calls** in feature code. The cost is type drift and per-feature middleware.

## Layout

```text
src/api/
├── client.ts            # createClient<paths>({ baseUrl }) + .use(middleware)
├── authMiddleware.ts    # injects Authorization header
├── retryMiddleware.ts   # optional
├── telemetryMiddleware.ts  # optional
├── types.ts             # generated paths/components types (or pinned re-exports)
└── <area>-api.ts        # named wrappers per area (vmsApi.ts, billingApi.ts)
```

`<area>-api.ts` files expose named functions that thin-wrap client calls — useful when call sites benefit from a name like `fetchVms({...})` or `createVm(body)` rather than the long `client.GET('/vms', ...)` form. They also concentrate path/method choices so endpoint changes touch one file.

If the app talks to multiple backends, give each its own `client*.ts` (`gpuClient.ts`, `billingClient.ts`) sharing middleware definitions.

## Middleware

Middleware is the right home for cross-cutting request behavior:

- **Auth**: read the current token (from auth domain), set `Authorization` header. On 401, attempt a refresh once; on refresh failure, sign out.
- **Telemetry**: tag requests with a request id, time them, send failures to Sentry/PostHog through the analytics service.
- **Retry**: limited retry on 5xx for safe verbs only (GET/HEAD).
- **Error normalization**: convert non-2xx responses to a typed `ApiError { status, code, message, fieldErrors? }`.

Each middleware is a small, single-responsibility file. Compose them on the client with `client.use(...)`.

Do not put auth state directly in the middleware module — read it from the auth domain. Module globals make tests painful.

## Error Shape

Define one typed error at the API boundary:

```ts
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly fieldErrors?: Record<string, string[]>,
  ) {
    super(message)
  }
}
```

Hooks above the API layer expect to `throw new ApiError(...)`. Mutation `onError` handlers branch on `status`/`code` and surface a toast or inline error.

Do not throw raw `Response`/network errors past the API boundary; map them in middleware.

## Hooks Wrap The API

Application hooks are the only public consumers of API functions:

```ts
export function useVms(filters: VmFilters) {
  return useQuery({
    queryKey: vmKeys.list(filters),
    queryFn: () => fetchVms(filters),
    staleTime: 30_000,
  })
}
```

Components import `useVms`. They never import `fetchVms` directly. This boundary lets you change cache strategy, add retries, swap clients, or migrate endpoints in one place.

## Mutations

Mutation hooks own the side-effect lifecycle:

```ts
export function useCreateVm() {
  const queryClient = useQueryClient()
  const analytics = useAnalytics()

  return useMutation({
    mutationFn: (input: CreateVmInput) => createVm(input),
    onMutate: async (input) => {
      await queryClient.cancelQueries({ queryKey: vmKeys.all })
      const previous = queryClient.getQueryData(vmKeys.list(currentFilters))
      // optimistic update if appropriate
      return { previous }
    },
    onError: (error, _input, context) => {
      queryClient.setQueryData(vmKeys.list(currentFilters), context?.previous)
      toast.error(formatApiError(error))
    },
    onSuccess: (_data, input) => {
      analytics.capture('vm_created', { name: input.name })
      toast.success('VM created')
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: vmKeys.all })
    },
  })
}
```

Components consume `mutate` / `mutateAsync`; the hook owns toasts, invalidations, and analytics. This keeps screens free of duplicated mutation glue.

## Auth Token Handling

Tokens are owned by the auth domain (`domains/auth/infrastructure/`), not by the API layer:

- the auth domain reads/writes the access token and refresh token
- the API middleware reads the current access token from the auth domain
- on 401 + valid refresh token, middleware calls `domains/auth/application/refreshSession()` and retries the request once

Do not store tokens in atoms or query cache. Tokens are auth-domain state with their own lifecycle (refresh, expiry, sign-out).

## Pagination, Cursors, Filters

Encode pagination and filters in the API function signature. Map URL search params or atoms into that shape inside the hook:

```ts
export function useVmsPaginated(
  pagination: { pageIndex: number; pageSize: number },
  filters: { status?: VmStatus; name?: string },
) {
  return useQuery({
    queryKey: vmKeys.list({ pagination, filters }),
    queryFn: () =>
      fetchVms({
        offset: pagination.pageIndex * pagination.pageSize,
        limit: pagination.pageSize,
        ...filters,
      }),
    placeholderData: keepPreviousData,
  })
}
```

The hook is the translation layer between view-friendly params (page index) and API-friendly params (offset).

## File Uploads And Streaming

For file uploads, wrap `fetch`/`XMLHttpRequest` in a small named function under `api/uploads.ts` that exposes a typed promise + progress callback. Wrap that function in a hook that integrates with the query client.

For streaming (SSE/WebSocket), keep the connection in `infrastructure/` of the owning feature (or a dedicated `services/` module if shared) — not in `api/`, because the cache and lifecycle differ from request/response.

## Mocking

In tests and Storybook, swap the network with **MSW** rather than mocking the client itself. MSW intercepts at the network layer so the same hooks, the same middleware, and the same error normalization run in tests.

## Pitfalls

- Hand-rolling `fetch` in components.
- Hand-writing TS types that mirror backend responses instead of generating from OpenAPI.
- Putting auth state in the middleware module.
- Throwing raw `Response` objects out of the API layer.
- Mixing two HTTP libraries (axios + fetch) in the same app.
- Centralizing all endpoints into one mega `api.ts` — split per area.
- Implicit retries on POST/PATCH/DELETE.
