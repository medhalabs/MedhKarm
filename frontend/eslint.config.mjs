import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";
import prettier from "eslint-config-prettier/flat";

// Feature boundaries (see docs/05-architecture-and-conventions.md):
// - other code imports a feature only through its index.ts ("@/features/<name>")
// - shared/ never imports from features/
// A feature's other public entry is "client": browser-safe exports for client components
// (index.ts may export server-only code that reads the session cookie).
const noDeepFeatureImports = {
  group: ["@/features/*/*", "!@/features/*/client"],
  message:
    'Import a feature only through its public index ("@/features/<name>"), or its browser-safe "@/features/<name>/client".',
};

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  prettier,
  {
    files: ["src/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-imports": ["error", { patterns: [noDeepFeatureImports] }],
    },
  },
  {
    files: ["src/shared/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@/features", "@/features/*"],
              message: "shared/ must not depend on features/.",
            },
          ],
        },
      ],
    },
  },
  globalIgnores([".next/**", "out/**", "build/**", "next-env.d.ts", "src/shared/api/generated/**"]),
]);

export default eslintConfig;
