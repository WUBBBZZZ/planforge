/**
 * Generate TypeScript types from the backend OpenAPI schema.
 *
 * Prerequisites:
 * - Backend running at http://127.0.0.1:8000
 * - openapi.json available at /openapi.json
 *
 * Usage (PowerShell):
 *   npm run generate:api-types
 */

import { execFileSync } from "node:child_process";
import { mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outputDir = path.resolve(__dirname, "../src/api");
const outputFile = path.join(outputDir, "schema.d.ts");
const schemaUrl = "http://127.0.0.1:8000/openapi.json";

mkdirSync(outputDir, { recursive: true });

execFileSync("npx", ["openapi-typescript", schemaUrl, "-o", outputFile], {
  stdio: "inherit",
  shell: true,
});

console.log(`Generated API types at ${outputFile}`);
