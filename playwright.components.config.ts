import { defineConfig } from "@playwright/test";
import base from "./playwright.config";

// These fixtures serve the production-bundled components through page routes.
export default defineConfig({ ...base, testMatch: "incremental.spec.ts", webServer: undefined,
  reporter: [["list"], ["json", { outputFile: "evidence/incremental-test-results.json" }]],
});
