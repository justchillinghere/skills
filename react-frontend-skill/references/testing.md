# Testing

Frontend tests should verify behavior at the layer where defects are most likely. Pure logic does not need a renderer; user-visible behavior should be tested through the UI; the network should be intercepted, not mocked module-by-module.

## Stack

- **Vitest** as the runner (Jest is fine for existing projects). Same TS config as the app.
- **React Testing Library** for component tests. Use accessible queries (`getByRole`, `getByLabelText`).
- **MSW** (Mock Service Worker) to intercept HTTP at the network layer.
- **@testing-library/user-event** v14+ for user interactions.
- **happy-dom** or **jsdom** as the test environment (happy-dom is faster).

Avoid Enzyme.

## Test Levels

- **Domain tests** — pure modules, no React. The cheapest tests. Cover model methods, schemas, derived state, formatters, predicates.
- **Hook tests** — `renderHook` from RTL. Cover `application/` hooks: query keys, invalidation behavior, optimistic updates, error mapping. Use MSW for API.
- **Component tests** — RTL `render`. Cover presentational components for the props → DOM mapping users care about. Cover containers for the wired behavior (clicking terminate calls the mutation).
- **Page/integration tests** — RTL `render` of a page inside the providers + a memory router. Cover happy path and one or two failure modes per page.

Avoid testing the same behavior at three levels. Pick the cheapest level that captures the behavior.

## File Layout

Two acceptable patterns; pick one and stay consistent:

- **Co-located**: `Component.test.tsx` next to `Component.tsx`. Easier to navigate; the file you are editing is next to its tests.
- **Mirror tree**: `tests/features/Vm/...` mirroring `src/features/Vm/...`. Easier to ignore in IDE searches; clearer for big monorepos.

Default to co-location for application code. A small `tests/integration/` directory is fine for cross-feature flows.

## Test Setup

`tests/setup.ts` (referenced from `vitest.config.ts`):

```ts
import '@testing-library/jest-dom/vitest'
import { afterAll, afterEach, beforeAll } from 'vitest'
import { server } from './msw/server'

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

`tests/msw/server.ts` exports a Node MSW server with default handlers; tests override per case.

## A `renderWithProviders` Helper

Most tests need at least the QueryClient provider. Add Jotai store and the router when needed.

```tsx
export function renderWithProviders(ui: ReactNode, options?: { route?: string }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <Provider store={createStore()}>{ui}</Provider>
    </QueryClientProvider>,
  )
}
```

Create a fresh QueryClient per test to avoid cache leaks. Disable retries in tests.

## Domain Tests

Plain Vitest:

```ts
describe('VmModel', () => {
  it('canTerminate is true for active vms', () => {
    const vm = VmModel.fromApi({ id: '1', status: 'active', name: 'a' })
    expect(vm.canTerminate).toBe(true)
  })

  it('canTerminate is false for terminated vms', () => {
    const vm = VmModel.fromApi({ id: '1', status: 'terminated', name: 'a' })
    expect(vm.canTerminate).toBe(false)
  })
})
```

Schemas:

```ts
expect(createVmSchema.safeParse({ name: '', region: 'us', size: 'small' }).success).toBe(false)
```

## Hook Tests

```ts
import { renderHook, waitFor } from '@testing-library/react'
import { server } from '@/tests/msw/server'
import { http, HttpResponse } from 'msw'

it('useVms returns a list of VmModels', async () => {
  server.use(
    http.get('/vms', () => HttpResponse.json({ items: [{ id: '1', status: 'active', name: 'a' }] })),
  )

  const { result } = renderHook(() => useVms({}), { wrapper: Wrapper })

  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  expect(result.current.data?.[0]).toBeInstanceOf(VmModel)
  expect(result.current.data?.[0].name).toBe('a')
})
```

For mutation hooks: render the hook, call `mutate(input)`, await `isSuccess`, and assert on side effects (toast, navigate, cache state via `queryClient.getQueryData`).

## Component Tests

Use accessible queries. Assert what the user perceives:

```tsx
it('renders an empty state when there are no rows', () => {
  render(<VmTable rows={[]} onTerminate={vi.fn()} />)
  expect(screen.getByText(/no virtual machines/i)).toBeInTheDocument()
})

it('calls onTerminate when the terminate button is clicked', async () => {
  const onTerminate = vi.fn()
  const rows = [VmModel.fromApi({ id: '1', status: 'active', name: 'a' })]
  render(<VmTable rows={rows} onTerminate={onTerminate} />)
  await userEvent.click(screen.getByRole('button', { name: /terminate/i }))
  expect(onTerminate).toHaveBeenCalledWith('1')
})
```

Avoid `getByTestId` unless there is no accessible alternative.

## Page / Integration Tests

A page test renders the page inside providers, asserts the happy path, and one or two failure modes:

```tsx
it('lists VMs and lets the user terminate one', async () => {
  server.use(
    http.get('/vms', () => HttpResponse.json({ items: [{ id: '1', status: 'active', name: 'a' }] })),
    http.delete('/vms/1', () => HttpResponse.json({ ok: true })),
  )

  renderWithProviders(<VmListPage />)

  expect(await screen.findByText('a')).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: /terminate/i }))
  await userEvent.click(screen.getByRole('button', { name: /confirm/i }))
  await waitFor(() => expect(screen.queryByText('a')).not.toBeInTheDocument())
})
```

## Naming And Assertions

Name tests by behavior, not by implementation:

```text
it('shows an error when the form is submitted with an empty name', ...)
```

Assert exact expected values. Avoid weak checks like `toBeTruthy()` when a stronger assertion (`toBe('Created')`, `toHaveAttribute('aria-busy')`) applies.

## Time And Determinism

Use `vi.useFakeTimers()` for tests that depend on debouncing, polling intervals, or `setTimeout`. Always restore real timers in cleanup.

For dates, accept a `now: () => Date` injection in domain functions or use `vi.setSystemTime(new Date('2025-01-01'))`.

## What Not To Mock

- Do not mock the API client module. Use MSW.
- Do not mock React itself or the router primitives. Render with a memory/test router.
- Do not mock domain modules. Use them.

Mock only at the edges of the system you cannot run in tests: third-party SDKs that talk to live services (Sentry, analytics), browser APIs not available in jsdom (`IntersectionObserver`, `matchMedia`), and timing primitives.

## Coverage

Aim for high coverage on `domain/` and `application/` (these are the rules). Lower bar for presentational `components/` (snapshot regression and accessible-query asserts are usually enough). Treat coverage as a smell-detector, not a goal.

## Pitfalls

- Tests that verify implementation details (CSS class names, internal state shape) instead of user-visible behavior.
- Forgetting to disable retries in the test QueryClient — flaky timeouts.
- Sharing a QueryClient across tests — state leak.
- Querying by `getByTestId` when an accessible query exists.
- Asserting on intermediate loading state without `waitFor`.
- Mocking modules instead of intercepting the network with MSW.
- Test setup duplicated across files — promote to a `renderWithProviders` helper.
