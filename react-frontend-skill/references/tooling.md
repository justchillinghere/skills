# Tooling

The build, type system, and lint setup are part of the architecture. Get these right once and they catch most regressions for you.

## Vite

Vite is the default. Use `@vitejs/plugin-react` for the React plugin and `vite-plugin-svgr` to import SVGs as components.

A useful baseline `vite.config.ts`:

```ts
import path from 'path'
import react from '@vitejs/plugin-react'
import svgr from 'vite-plugin-svgr'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), svgr()],
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') },
  },
  build: {
    sourcemap: true,
    target: 'esnext',
  },
  server: {
    port: 5173,
  },
})
```

When using TanStack Router file-based routes, add `TanStackRouterVite()` to plugins. When the app needs Node-only globals in browser code (rare; usually a sign of a misplaced dependency), add `vite-plugin-node-polyfills` — but prefer to fix the offending import.

Set `define: { __APP_VERSION__: JSON.stringify(version) }` only if features actually read the version (footer, error reporting). Do not pre-populate `define` "in case."

## TypeScript

Use **strict** mode. The minimum:

```jsonc
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "jsx": "react-jsx",
    "lib": ["DOM", "DOM.Iterable", "ES2022"],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "exactOptionalPropertyTypes": true,
    "noFallthroughCasesInSwitch": true,
    "isolatedModules": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "verbatimModuleSyntax": true,
    "paths": { "@/*": ["./src/*"] },
    "baseUrl": "."
  },
  "include": ["src", "tests", "vite.config.ts"]
}
```

`noUncheckedIndexedAccess: true` catches the most common runtime bugs in TypeScript apps (assuming `arr[i]` is defined). It is mildly annoying once and pays back forever.

Use `tsc --noEmit` as a CI gate; Vite does not type-check during build by default.

## Path Aliases

Use one alias: `@` → `src/`. Configure it in three places, all consistent:

- `tsconfig.json` `paths`
- `vite.config.ts` `resolve.alias`
- `vitest.config.ts` (inherits from Vite config when `test` is added there)

Avoid multiple aliases (`@components`, `@hooks`, `@utils`). They feel ergonomic at first and cause grief at refactor time.

## ESLint

Stack:

- `eslint`
- `@typescript-eslint/parser`, `@typescript-eslint/eslint-plugin`
- `eslint-plugin-react`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`
- `eslint-plugin-import`, `eslint-plugin-simple-import-sort`
- `eslint-plugin-jsx-a11y`
- `eslint-config-prettier` (last, to disable formatting rules)

Key rules to enable beyond defaults:

- `react-hooks/exhaustive-deps: error`
- `react-refresh/only-export-components` for fast refresh
- `import/no-cycle: error` (prevents circular imports across layers)
- `simple-import-sort/imports`, `simple-import-sort/exports`
- `@typescript-eslint/consistent-type-imports`
- `@typescript-eslint/no-floating-promises`
- `jsx-a11y` recommended

Custom rule worth adding: a no-restricted-imports rule that forbids feature → feature imports:

```js
{
  rules: {
    'no-restricted-imports': ['error', {
      patterns: [{
        group: ['@/features/*/!(application|pages)*/**'],
        message: 'Import only from a feature\'s pages or application/hooks barrel.',
      }],
    }],
  },
}
```

Tune the pattern to your barrel exports. The rule turns the architecture into a lint error, not a code-review note.

## Prettier

Minimal `.prettierrc`:

```json
{
  "semi": false,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100,
  "arrowParens": "always"
}
```

Match what already exists if the project has Prettier configured.

## Pre-commit

Use **husky** + **lint-staged**:

```jsonc
// package.json
{
  "lint-staged": {
    "*.{ts,tsx}": ["eslint --fix --max-warnings=0"],
    "*.{ts,tsx,json,md,css}": ["prettier --write"]
  }
}
```

Run lint and type-check in CI; do not skip these locally with `--no-verify`. If a hook is wrong, fix the hook.

## Scripts

`package.json` baseline:

```jsonc
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "lint": "eslint . --max-warnings=0",
    "lint:fix": "eslint . --fix",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "format": "prettier --write ."
  }
}
```

Add a `"generate:api"` script if you generate types from OpenAPI. Pin the OpenAPI version in source control or treat the generated file as a build artifact, but do not generate at app start.

## Environment Variables

Vite exposes `import.meta.env.VITE_*` to the client. Read them once in `config/env.ts` and export typed values:

```ts
import { z } from 'zod'

const envSchema = z.object({
  VITE_API_BASE_URL: z.string().url(),
  VITE_SENTRY_DSN: z.string().optional(),
})

export const env = envSchema.parse(import.meta.env)
```

Validation at boot turns missing config into a fast, clear error. Feature code imports `env`, never `import.meta.env`.

## Bundle Awareness

- Use `vite-bundle-visualizer` or `rollup-plugin-visualizer` periodically to spot accidental large imports.
- Watch for date libraries (prefer `date-fns` over `moment`), full-icon-set imports (use tree-shakeable per-icon imports), and CSS-in-JS runtime overhead.
- Pre-bundle dependencies in `optimizeDeps` only when Vite warns; do not anticipate.

## Source Maps

Production source maps are useful for Sentry-style error symbolication. Keep `sourcemap: true` and upload to your error tracker, or strip from public hosting if leaking source is a concern.

## Pitfalls

- Multiple path aliases (`@components`, `@hooks`, ...). Pick one.
- `tsc` not part of `build` — type errors slip through.
- Skipping `noUncheckedIndexedAccess` because it's "annoying."
- ESLint and Prettier rules conflicting because `eslint-config-prettier` is missing.
- Generating API types at build time across CI — flaky and slow. Commit the generated file.
- `import.meta.env` access scattered across feature code.
- Forgetting `react-refresh/only-export-components` — non-component exports break HMR.
- Disabling lint rules in PRs instead of fixing them.
