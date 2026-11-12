import { defineConfig } from "@playwright/test";
import base from "./playwright.config";

export default defineConfig({ ...base, webServer: undefined,
  testMatch: ["three-views.spec.ts", "week-packet.spec.ts", "safe-example.spec.ts"],
  reporter: [["list"], ["json", { outputFile: "evidence/week-browser-results.json" }]],
});
