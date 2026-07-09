# Feature Anatomy

A feature is one product surface a user interacts with. This document is the concrete recipe for building one.

## When To Make A New Feature

Make a new `features/<Name>/` when:

- the surface has its own pages, its own data, and its own state
- it would still be a coherent area if you renamed it (it has a real name in the product, not "stuff")
- multiple components or hooks belong together but do not fit any existing feature

Do not make a new feature for:

- a single component (put it in `components/` or the closest existing feature)
- a hook with no UI (put it in `hooks/` or a domain)
- a one-off page (start in an existing feature; split out only if the surface earns it)

## Naming

Feature folder: `PascalCase` (`Auth`, `Billing`, `VM`). Internal subfolders: lowercase (`pages`, `containers`, `components`, `application`, `domain`, `infrastructure`).

Files: `PascalCase.tsx` for components and pages, `camelCase.ts` for non-component modules, `useX.ts` for hooks. Match the default export to the file name.

## Reference Anatomy

Below is what a fully-grown feature looks like. A new scaffold ships only the parts it needs today.

```text
features/Vm/
├── pages/
│   └── VmListPage.tsx                # route component target
├── containers/
│   ├── VmTableContainer.tsx          # wires hooks → presentational table
│   └── modals/
│       ├── TerminateVmModal.tsx
│       └── EditVmNameModal.tsx
├── components/
│   ├── VmTable.tsx                   # presentational
│   ├── VmStatusBadge.tsx
│   ├── VmFiltersBar.tsx
│   └── creation/
│       └── VmConfigStep.tsx
├── application/
│   ├── hooks/
│   │   ├── index.ts                  # barrel for the feature's public hooks
│   │   ├── useVms.ts
│   │   ├── useVmDetails.ts
│   │   ├── useCreateVm.ts
│   │   ├── useTerminateVm.ts
│   │   └── useUpdateVmName.ts
│   └── vmKeys.ts                     # query-key factory
├── domain/
│   ├── types.ts                      # value types, enums, schemas
│   ├── VmModel.ts                    # methods over a single VM
│   ├── VmStatuses.ts                 # status helpers, status filter logic
│   └── createVmSchema.ts             # zod schema (shared with form + tests)
└── infrastructure/
    └── store.ts                      # jotai atoms: filters, selection, draft
```

## Step-By-Step Recipe

### 1. Domain First

Define what the feature works with before you build the UI.

`features/Vm/domain/types.ts`:

```ts
import { z } from 'zod'
import type { components } from '@/api/types'

export type VmStatus = 'active' | 'launching' | 'terminated' | 'failed'

export type Vm = components['schemas']['Vm']  // generated API type

export const createVmSchema = z.object({
  name: z.string().min(1).max(64),
  region: z.string(),
  size: z.enum(['small', 'medium', 'large']),
})

export type CreateVmInput = z.infer<typeof createVmSchema>
```

`features/Vm/domain/VmModel.ts`:

```ts
export class VmModel {
  constructor(private readonly raw: Vm) {}

  get id() { return this.raw.id }
  get name() { return this.raw.name }
  get isLive() { return this.raw.status === 'active' || this.raw.status === 'launching' }
  get canTerminate() { return this.isLive }

  static fromApi(raw: Vm) { return new VmModel(raw) }
}
```

A model is worth creating when there is non-trivial derived state or rules (`canTerminate`, `isLive`, formatted price). Plain typed records are fine when the data is just data.

### 2. Query Keys

`features/Vm/application/vmKeys.ts`:

```ts
export const vmKeys = {
  all: ['vms'] as const,
  list: (filters: VmFilters) => [...vmKeys.all, 'list', filters] as const,
  detail: (id: string) => [...vmKeys.all, 'detail', id] as const,
}
```

### 3. Hooks (Use Cases)

`features/Vm/application/hooks/useVms.ts`:

```ts
export function useVms(filters: VmFilters) {
  return useQuery({
    queryKey: vmKeys.list(filters),
    queryFn: async () => {
      const { data, error } = await client.GET('/vms', { params: { query: filters } })
      if (error) throw error
      return (data?.items ?? []).map(VmModel.fromApi)
    },
    staleTime: 30_000,
  })
}
```

`features/Vm/application/hooks/useCreateVm.ts`:

```ts
export function useCreateVm() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const analytics = useAnalytics()

  return useMutation({
    mutationFn: (input: CreateVmInput) => createVm(input),
    onSuccess: (vm, input) => {
      analytics.capture('vm_created', { region: input.region, size: input.size })
      toast.success('VM created')
      navigate({ to: '/vms/$id', params: { id: vm.id } })
    },
    onError: (error: ApiError) => toast.error(formatApiError(error)),
    onSettled: () => queryClient.invalidateQueries({ queryKey: vmKeys.all }),
  })
}
```

Index file (`hooks/index.ts`) re-exports the public hooks so containers import from one path.

### 4. Infrastructure (Optional)

If filters are not in URL state, add atoms:

```ts
// features/Vm/infrastructure/store.ts
import { atom } from 'jotai'
export const vmStatusFilterAtom = atom<VmStatus | 'all'>('all')
export const vmSelectionAtom = atom<Set<string>>(new Set())
```

If filters belong in URL state (recommended for sharable views), skip this and use search params instead.

### 5. Presentational Components

`features/Vm/components/VmTable.tsx`:

```tsx
type Props = {
  rows: VmModel[]
  isLoading?: boolean
  onTerminate: (id: string) => void
}

export function VmTable({ rows, isLoading, onTerminate }: Props) {
  if (isLoading) return <TableSkeleton />
  if (!rows.length) return <EmptyState />
  return (
    <Table>
      {rows.map((vm) => (
        <Row key={vm.id}>
          <Cell>{vm.name}</Cell>
          <Cell><VmStatusBadge status={vm.status} /></Cell>
          <Cell>{vm.canTerminate && <Button onClick={() => onTerminate(vm.id)}>Terminate</Button>}</Cell>
        </Row>
      ))}
    </Table>
  )
}
```

### 6. Container

`features/Vm/containers/VmTableContainer.tsx`:

```tsx
export function VmTableContainer({ filters }: { filters: VmFilters }) {
  const { data, isLoading } = useVms(filters)
  const terminate = useTerminateVm()
  return (
    <VmTable
      rows={data ?? []}
      isLoading={isLoading}
      onTerminate={(id) => terminate.mutate({ id })}
    />
  )
}
```

### 7. Page

`features/Vm/pages/VmListPage.tsx`:

```tsx
export default function VmListPage() {
  const filters = useVmFilters()
  return (
    <PageLayout title="VMs" actions={<NewVmButton />}>
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

### 8. Route

`routes/vms/index.tsx`:

```tsx
import VmListPage from '@/features/Vm/pages/VmListPage'

export const Route = createFileRoute('/vms/')({
  beforeLoad: requireCapability('canListVm'),
  component: () => <VmListPage />,
})
```

### 9. Tests

Plan and write tests at the right levels. See `references/testing.md`. Minimum for a new feature:

- domain unit tests for any model methods or schemas
- one hook test per non-trivial query/mutation, with MSW
- one page-level integration test for the happy path

## Public Surface Of A Feature

Other parts of the app should import from a feature only via:

- its **pages** (route components)
- its **public hooks** (re-exported from `features/<F>/application/hooks/index.ts`)
- its **public domain types/models**, when shared

They should not reach into containers, internal components, or atoms. If another feature needs an internal piece, the piece is probably misplaced — promote it to `domains/`, `components/`, or `hooks/`.

## When A Feature Splits

Signs that one feature is doing too much:

- the folder has 30+ components
- two distinct user mental models live inside (`VM` doing both creation flow and list management)
- different pages use disjoint sets of hooks and components

Split by user-facing surface, not by data model. `Vm` may split into `VmList` + `VmCreation` if the creation flow is large; do not split `Vm` into "frontend Vm" + "backend Vm."

## Pitfalls

- Skipping `domain/` and putting business rules in components.
- Containers that re-implement data fetching instead of calling a hook.
- Hooks that import other features' internals.
- A page that fetches data instead of delegating to containers.
- Atoms holding server data.
- Cross-feature imports — promote shared code to `domains/`, `components/`, or `hooks/`.
- Building a feature folder before there is concrete code in it.
