import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";

test("engine entries, separate goal lenses and global findings survive the reading UI", async ({ page }) => {
  const packet = JSON.parse(await readFile("engine/tests/fixtures/packets/preview-entries.json", "utf8"));
  const errors: string[] = [];
  page.on("pageerror", e => errors.push(e.message));
  await page.addInitScript(packet => sessionStorage.setItem("tompathy-session", JSON.stringify({ sessionVersion: "1.0", artifact: packet.artifact, packet, scope: "artifact", context: [] })), packet);
  await page.goto("/");
  await expect(page.locator(".preview-banner")).toHaveCount(3);
  await expect(page.locator(".goal-lenses")).toBeVisible();
  await expect(page.locator(".goal-lenses > *")).toHaveCount(2);
  await expect(page.locator(".preview-entries", { hasText: "From the page" }).first()).toBeVisible();
  await expect(page.getByText("Root cue reliability: 0.6 (assumed).", { exact: false })).toBeVisible();
  await page.getByRole("tab", { name: "global", exact: true }).click();
  await expect(page.getByLabel("Public population research")).toContainText("Sounding Line V2");
  await expect(page.getByLabel("Public population research").getByRole("link", { name: "Source and limits" })).toHaveCount(5);
  await page.screenshot({ path: "evidence/engine-packet-wide.png" });
  await page.setViewportSize({ width: 420, height: 960 });
  await expect(page.locator(".goal-lenses")).toBeVisible();
  const bounds = await page.locator(".goal-lenses > *").evaluateAll(nodes => nodes.map(n => { const r = n.getBoundingClientRect(); return { x: r.x, y: r.y, width: r.width, height: r.height }; }));
  expect(bounds.every(b => b.width > 100 && b.height > 100 && b.x >= 0 && b.x + b.width <= 421)).toBe(true);
  expect(bounds[1].x).toBeGreaterThan(bounds[0].x + bounds[0].width);
  const clear = await page.evaluate(() => {
    const process = document.querySelector(".process-region")!.getBoundingClientRect();
    const values = document.querySelector(".values-region")!.getBoundingClientRect();
    return [...document.querySelectorAll(".goal-lenses .spool-area")].every(node => node.getBoundingClientRect().bottom < values.top && node.getBoundingClientRect().bottom <= process.bottom);
  });
  expect(clear).toBe(true);
  await page.screenshot({ path: "evidence/engine-packet-narrow.png" });
  expect(errors).toEqual([]);
});
