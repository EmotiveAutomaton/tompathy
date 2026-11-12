import { test as base, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";
import path from "node:path";

/** Exercise the actual distributable without Vite's unrelated cold transform cost. */
export const test = base.extend({
  page: async ({ page }, use) => {
    await page.route("http://127.0.0.1:5173/**", async route => {
      const name = new URL(route.request().url()).pathname.slice(1) || "panel.html";
      if (name !== path.basename(name)) return route.fulfill({ status: 404 });
      try {
        const body = await readFile(path.join("dist", name));
        const contentType = name.endsWith(".js") ? "application/javascript" : name.endsWith(".css") ? "text/css" : name.endsWith(".html") ? "text/html" : name.endsWith(".woff") ? "font/woff" : undefined;
        await route.fulfill({ body, contentType });
      } catch { await route.fulfill({ status: 404 }); }
    });
    await use(page);
  },
});
export { expect };
