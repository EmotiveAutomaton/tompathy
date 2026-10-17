import { test, expect } from "@playwright/test";
import { build } from "esbuild";
import { readFile } from "node:fs/promises";

test("stable early outline, simultaneous pies, completion fade and paused work", async ({ page }) => {
  test.setTimeout(90000);
  const errors: string[] = [];
  page.on("pageerror", e => errors.push(e.message));
  await page.setViewportSize({ width: 360, height: 800 });
  // Exercise the same bundler used by the extension. The dev CSS transformer
  // can stall on this workstation; serve the actual compiled component assets.
  await build({ entryPoints: ["tests/fixtures/incremental.tsx"], bundle: true, format: "esm", outfile: ".local/incremental-fixture.js", jsx: "automatic", loader: { ".woff": "dataurl" } });
  await page.route("**/tests/fixtures/incremental.html", route => route.fulfill({ contentType: "text/html", body: '<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="/.local/incremental-fixture.css"><div id="root"></div><script type="module" src="/.local/incremental-fixture.js"></script>' }));
  await page.route("**/.local/incremental-fixture.js", async route => route.fulfill({ contentType: "application/javascript", body: await readFile(".local/incremental-fixture.js", "utf8") }));
  await page.route("**/.local/incremental-fixture.css", async route => route.fulfill({ contentType: "text/css", body: await readFile(".local/incremental-fixture.css", "utf8") }));
  await page.goto("/tests/fixtures/incremental.html", { waitUntil: "domcontentloaded" });
  const paths = () => page.locator(".pyramid svg").evaluate(el => [...el.querySelectorAll("path")].filter(p => p.getAttribute("d")?.length! > 500).map(p => p.getAttribute("d")));
  await expect(page.getByRole("progressbar", { name: "Attention", exact: true })).toHaveAttribute("aria-valuenow", "0");
  await expect(page.getByRole("progressbar", { name: "Goals", exact: true })).toBeVisible();
  const initial = await paths();
  expect(initial.length).toBeGreaterThan(0);
  await page.getByRole("button", { name: "Advance", exact: true }).click();
  await expect(page.getByRole("progressbar", { name: "Attention", exact: true })).toHaveAttribute("aria-valuenow", "1");
  const first = await paths();
  expect(first).toEqual(expect.arrayContaining(initial));
  const firstDot = await page.locator('[data-node="goal-0"]').first().boundingBox();
  for (let i = 0; i < 6; i++) await page.getByRole("button", { name: "Advance", exact: true }).click();
  const later = await paths();
  expect(later).toEqual(expect.arrayContaining(initial));
  const laterDot = await page.locator('[data-node="goal-0"]').first().boundingBox();
  expect(Math.abs(laterDot!.y - firstDot!.y)).toBeLessThan(2);
  const footer = await page.locator(".values-bottom").boundingBox();
  expect(footer!.x + footer!.width).toBeLessThanOrEqual(360);
  await expect(page.getByRole("button", { name: "Reader menu" })).toBeInViewport();
  const menu = await page.getByRole("button", { name: "Reader menu" }).boundingBox();
  const progress = await page.locator('.reading-progress').boundingBox();
  expect(menu!.x).toBeGreaterThan(progress!.x + progress!.width);
  expect(Math.abs(menu!.y + menu!.height / 2 - progress!.y - progress!.height / 2)).toBeLessThan(15);
  expect(await page.locator('.pyramid-silhouette').first().evaluate(el => getComputedStyle(el).fill)).not.toBe("rgb(0, 0, 0)");
  await page.screenshot({ path: "evidence/incremental-progress.png" });
  await page.getByRole("button", { name: "Pause", exact: true }).click();
  await expect(page.locator(".reading-progress-check")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Continue reading" })).toBeVisible();
  await page.getByRole("button", { name: "Continue reading" }).click();
  await page.getByRole("button", { name: "Finish", exact: true }).click();
  await expect(page.locator(".reading-progress-check")).toHaveCount(2);
  await expect(page.locator(".reading-progress-item")).toHaveCount(0, { timeout: 4500 });
  expect(errors).toEqual([]);
});
