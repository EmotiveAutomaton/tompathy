import { test, expect } from "@playwright/test";
import { pathToFileURL } from "node:url";
import path from "node:path";
import { readFile } from "node:fs/promises";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

test.beforeAll(async () => {
  await promisify(execFile)(process.execPath, ["scripts/export-essay-handoff.mjs"]);
});

test("website handoff runs independently with all original images and diagrams", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", e => errors.push(e.message));
  const content = JSON.parse(await readFile("docs/website-essay-handoff/content.json", "utf8"));
  await page.goto(pathToFileURL(path.resolve("docs/website-essay-handoff/preview.html")).href);
  for (const [kind, title] of [["goals", "Current attention"], ["process", "Expertise (Previous attention)"], ["values", "Core values"]]) {
    await page.getByRole("button", { name: `About ${title}`, exact: true }).click();
    const dialog = page.locator(".essay-dialog");
    await expect(dialog.locator("[data-essay-paragraph]")).toHaveCount(content.essays[kind].paragraphs.length);
    for (const image of await dialog.locator(".essay-images img").all()) {
      await image.scrollIntoViewIfNeeded();
      await expect.poll(() => image.evaluate((img: HTMLImageElement) => img.complete && img.naturalWidth > 0)).toBe(true);
    }
    if (kind === "values") {
      await expect(dialog.locator(".essay-channel")).toHaveCount(7);
      await expect(dialog.locator(".essay-preference svg")).toHaveCount(1);
      await dialog.locator(".essay-preference").scrollIntoViewIfNeeded();
      await page.screenshot({ path: "evidence/website-handoff-reference.png" });
    }
    await page.getByRole("button", { name: "Close essay", exact: true }).click();
  }
  await page.getByRole("button", { name: "Bibliography", exact: true }).click();
  await expect(page.locator(".essay-bibliography li")).toHaveCount(content.bibliography.length);
  expect(errors).toEqual([]);
});
