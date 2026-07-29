/**
 * Generate TypeScript types from the committed OpenAPI schema.
 *
 * Usage (PowerShell):
 *   npm run generate:api-types
 *
 * Regenerate the schema first from the backend:
 *   cd backend
 *   .\.venv\Scripts\python.exe scripts\export_openapi.py
 */

import { execFileSync } from "node:child_process";
import { mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outputDir = path.resolve(__dirname, "../src/api");
const outputFile = path.join(outputDir, "schema.d.ts");
const schemaFile = path.resolve(__dirname, "../openapi/openapi.json");

mkdirSync(outputDir, { recursive: true });

execFileSync("npx", ["openapi-typescript", schemaFile, "-o", outputFile], {
  stdio: "inherit",
  shell: true,
});

console.log(`Generated API types at ${outputFile}`);
