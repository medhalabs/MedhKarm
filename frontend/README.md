# Frontend

Next.js app for MedhKarm. Setup and commands: [docs/technical/local-setup.md](../docs/technical/local-setup.md). Structure and rules: [docs/05-architecture-and-conventions.md](../docs/05-architecture-and-conventions.md).

```
src/
├── app/         thin Next.js route files that render feature components
├── features/    one folder per feature (components/, hooks/, api/, types.ts, index.ts)
└── shared/      ui/, api/ (backend client), hooks/, lib/ — never imports features
```

| Command             | What it does                             |
| ------------------- | ---------------------------------------- |
| `npm run dev`       | Dev server on http://localhost:3000      |
| `npm run lint`      | ESLint, including feature boundary rules |
| `npm run typecheck` | TypeScript strict check                  |
| `npm test`          | Vitest unit tests                        |
| `npm run format`    | Prettier                                 |
