# Components

Components have one of three roles. Knowing which role each component plays is the simplest way to keep an app maintainable.

## Three Roles

- **Presentational** — props in, callbacks out. No data fetching, no global state. Lives in `components/` (app-wide) or `features/<F>/components/` (feature-specific).
- **Container (smart)** — calls hooks, passes data and callbacks to presentational children. Lives in `features/<F>/containers/`.
- **Page** — assembles containers and layout for a single route. Lives in `features/<F>/pages/`.

These are roles, not separate technologies. They are all React function components. The distinction is what they import:

| Role            | May import                                                        | May NOT import                              |
| --------------- | ----------------------------------------------------------------- | ------------------------------------------- |
| Presentational  | `react`, sibling components, primitives, types                    | hooks/, application/, api/, atoms          |
| Container       | application hooks, atoms, presentational components               | api/ directly, ORM-shaped data              |
| Page            | containers, layouts, suspense/error boundaries, feature atoms     | low-level inputs, raw API hooks            |

## Presentational Components

Pure functions of props. State is allowed if it is purely visual (hover, focus, disclosure):

```tsx
type ButtonProps = {
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  disabled?: boolean
  onClick?: () => void
  children: ReactNode
}

export function Button({ variant = 'primary', size = 'md', loading, disabled, onClick, children }: ButtonProps) {
  return (
    <button
      type="button"
      data-variant={variant}
      data-size={size}
      aria-busy={loading || undefined}
      disabled={disabled || loading}
      onClick={onClick}
    >
      {loading ? <Spinner /> : children}
    </button>
  )
}
```

Rules of thumb:

- One responsibility per component. A `Button` does not also know how to submit a form.
- Pass children, not configuration, when the parent has structured content.
- Accept `onX` callbacks instead of asking parents to manage controlled state for unrelated things.

## Containers

Containers are the only place where hooks meet UI. A container should be small — usually less than 60 lines:

```tsx
export function VmTableContainer({ filters }: { filters: VmFilters }) {
  const { data, isLoading, error } = useVms(filters)
  const terminate = useTerminateVm()

  if (error) return <ErrorState error={error} />

  return (
    <VmTable
      rows={data ?? []}
      isLoading={isLoading}
      onTerminate={(id) => terminate.mutate({ id })}
    />
  )
}
```

A container is allowed to:

- call application hooks (`useVms`, `useCreateVm`)
- read atoms / search params
- adapt hook results into props the presentational child needs

A container should not:

- contain layout primitives beyond what is needed to host children
- duplicate fetch logic that already exists in a hook
- hold business rules — those live in domain models

## Pages

A page is a route's component. It composes containers and layout, declares Suspense and error boundaries, and reads page-scoped state (e.g. pagination):

```tsx
export default function VmListPage() {
  const filters = useVmFilters() // search params or atoms
  return (
    <PageLayout title="VMs">
      <VmFiltersBar />
      <Suspense fallback={<TableSkeleton />}>
        <ErrorBoundary fallback={<TableErrorState />}>
          <VmTableContainer filters={filters} />
        </ErrorBoundary>
      </Suspense>
    </PageLayout>
  )
}
```

Pages are allowed to know about the layout. Containers and presentational components below them should not.

## Composition Over Configuration

Prefer accepting children to growing prop surfaces.

```tsx
// Worse — explodes as variations grow
<Card title="Foo" subtitle="Bar" actions={<Button />} icon={<Icon />} />

// Better — composition
<Card>
  <Card.Header>
    <Card.Icon><Icon /></Card.Icon>
    <Card.Title>Foo</Card.Title>
    <Card.Subtitle>Bar</Card.Subtitle>
  </Card.Header>
  <Card.Actions><Button /></Card.Actions>
</Card>
```

Compound components (parent + named subcomponents) keep the API discoverable and let consumers reorder/skip parts.

## Headless / Primitive Libraries

Build accessible primitives once, reuse everywhere. Two solid foundations:

- **Radix UI** primitives (Dialog, Popover, DropdownMenu, Tooltip, Toggle, AlertDialog) — unstyled, accessible, composable.
- **React Aria** — lower-level hooks for keyboard, focus, ARIA semantics.

Wrap the primitive in a styled component in `components/` so feature code never imports the library directly. This means swapping the primitive library is one PR, not a sweep.

## Forms

Use **react-hook-form** + **zod**. Define the schema in `domain/`, derive the type, and pass `zodResolver(schema)`.

```tsx
const schema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
})

type Values = z.infer<typeof schema>

export function CreateUserForm({ onSubmit }: { onSubmit: (v: Values) => void }) {
  const form = useForm<Values>({ resolver: zodResolver(schema) })
  return <form onSubmit={form.handleSubmit(onSubmit)}>...</form>
}
```

Wrap inputs in labeled, controlled wrappers (`LabeledInput`, `LabeledSelect`) that integrate with `register`/`Controller` once, so every form benefits.

## Accessibility Baseline

- Every interactive element is reachable by keyboard.
- Buttons are `<button type="button">`, not `<div onClick>`.
- Form fields have associated labels (`<label for>` or `aria-labelledby`).
- Modal dialogs trap focus and restore it on close (Radix Dialog handles this).
- Color is never the only signal for state; pair with icon or text.
- Live regions (`aria-live`) for async status messages where appropriate.

This is the floor. A11y is not a separate work stream you do "later."

## Error Boundaries And Suspense

Place boundaries at route level by default, with finer-grained boundaries around independent subtrees that should fail or load separately.

```tsx
<Suspense fallback={<RouteSkeleton />}>
  <ErrorBoundary fallback={<RouteError />}>
    <Page />
  </ErrorBoundary>
</Suspense>
```

A single error boundary at the root only is too coarse — one bug blanks the app. A boundary per component is too fine — boilerplate for nothing.

## Modals

Centralize modal mounting at the app root via a small modal-stack atom (or framework like Radix `<Dialog>` with portal):

```tsx
const activeModalAtom = atom<ModalRequest | null>(null)
```

Containers/pages call `openModal(request)` and read `useAtomValue(activeModalAtom)` is rendered once at the root. This avoids stacking-context bugs and ensures only one modal is mounted at a time.

For multiple stacked modals, keep a small stack array.

## Performance

- Default to no memoization. Add `useMemo`/`useCallback`/`React.memo` only after measuring or when the prop is a stable reference required by an effect.
- Virtualize long lists (`@tanstack/react-virtual`). 200+ rows is the rough threshold.
- Code-split heavy, route-specific dependencies (rich-text editors, charts) when they are not on the critical path.
- Prefer `Suspense` boundaries to manual `if (loading)` ladders for cleaner render trees.

## Storybook

Optional but recommended for a component library — `components/` and feature-specific presentational components benefit. Containers and pages do not, since they need wired hooks.

Co-locate `*.stories.tsx` next to the component.

## Pitfalls

- Components that fetch their own data instead of accepting it as props.
- Container logic leaking into presentational components ("just one query, it's fine").
- Importing Radix/React Aria primitives directly in feature code instead of through a wrapper.
- Wrapping every interactive element in `useCallback` "for performance" without measurement.
- Modal state scattered across component trees instead of a single source.
- Logic in JSX (`{user && user.subscription && user.subscription.status === 'active' && ...}`) that should be a derived value or domain method.
- Forms that bypass react-hook-form and manage their own value/onChange wiring.
