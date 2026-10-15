import { test, expect } from "@playwright/test";
import { writeFile } from "node:fs/promises";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() =>
    localStorage.setItem("tompathy-guide-offered-040", "yes"),
  );
});

test("review heading and help geometry at narrow and short sizes", async ({
  page,
}) => {
  const results = [];
  for (const [width, height] of [
    [320, 900],
    [360, 600],
    [320, 450],
  ]) {
    await page.setViewportSize({ width, height });
    await page.goto("/?panel&demo=fieldnotes");
    await expect(page.locator(".core-value-row")).toHaveCount(9);
    const heading = await page.locator("#values-title").boundingBox();
    const second = await page
      .locator(".core-value-row > span")
      .nth(1)
      .boundingBox();
    const panel = await page.locator(".values-region").boundingBox();
    expect(
      second!.x + second!.width <= heading!.x ||
        second!.y >= heading!.y + heading!.height,
    ).toBe(true);
    expect(panel!.height).toBeGreaterThan(230);
    await page
      .getByRole("button", { name: "About Core values", exact: true })
      .focus();
    const help = page.getByRole("tooltip");
    await expect(help).toBeVisible();
    await page.waitForTimeout(200);
    const card = await help.boundingBox();
    expect(card!.y).toBeGreaterThanOrEqual(0);
    expect(card!.y + card!.height).toBeLessThanOrEqual(height);
    results.push({ width, height, heading, second, panel, card });
    await page.screenshot({ path: `evidence/polish-help-${height}.png` });
    await page
      .getByRole("button", { name: "About Core values", exact: true })
      .click();
    const dialog = page.getByRole("dialog");
    await expect(dialog.locator("#help-values")).toBeInViewport();
    const target = await dialog.locator("#help-values").boundingBox();
    const dialogHeader = await dialog.locator("header").boundingBox();
    expect(target!.y).toBeGreaterThanOrEqual(
      dialogHeader!.y + dialogHeader!.height,
    );
    await expect(dialog).toContainText("latent preferences");
    await page.screenshot({
      path: `evidence/polish-help-dialog-${height}.png`,
    });
    await page.keyboard.press("Escape");
    await expect(dialog).toHaveCount(0);
    await expect(
      page.getByRole("button", { name: "About Core values", exact: true }),
    ).toBeFocused();
    const title = page.getByRole("button", {
      name: "About Core values",
      exact: true,
    });
    await title.click();
    await title.press("Escape");
    await page.waitForTimeout(550);
    await expect(dialog).toHaveCount(0);
  }
  await writeFile(
    "evidence/polish-geometry.json",
    JSON.stringify(results, null, 2),
  );
});

test("uniform headings, supplied icon, confidence weights and a reachable half row", async ({
  page,
}) => {
  test.setTimeout(60000);
  for (const width of [400, 360, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/?panel&demo=fieldnotes");
    const headings = page.locator(".heading-help");
    await expect(headings).toHaveCount(3);
    const sizes = await headings.evaluateAll((els) =>
      els.map((el) => getComputedStyle(el).fontSize),
    );
    expect(sizes).toEqual(["11px", "11px", "11px"]);
    await expect(page.locator(".creator-brain")).toHaveAttribute(
      "src",
      "./icon128.png",
    );
    await expect(page.locator(".creator-brain")).toHaveJSProperty(
      "naturalWidth",
      128,
    );
    await page.getByRole("tab", { name: "creator", exact: true }).click();
    const valueRows = page.locator(".core-value-row");
    await expect(valueRows).toHaveCount(9);
    const values = await page.locator("#values-view").boundingBox();
    const ninth = await valueRows.last().boundingBox();
    const shown = (values!.y + values!.height - ninth!.y) / ninth!.height;
    expect(shown).toBeCloseTo(0.5, 1);
    const weights = await valueRows.evaluateAll((els) =>
      els.map((el) => Number(getComputedStyle(el).fontWeight)),
    );
    expect(weights).toEqual([...weights].sort((a, b) => b - a));
    expect(weights[0]).toBeGreaterThan(weights.at(-1)!);
    await page.keyboard.press("Tab");
    await valueRows.last().focus();
    await expect(valueRows.last()).toBeFocused();
    const scrolled = await page
      .locator("#values-view")
      .evaluate((el) => el.scrollTop);
    expect(scrolled).toBeGreaterThan(0);
    await expect(page.getByRole("tooltip")).toContainText("Player agency");
    await valueRows.last().press("Escape");
    await page.locator("#values-view").evaluate((el) => (el.scrollTop = 0));
    await page.locator('[data-node="sentence-1-1"] circle').click();
    await expect(page.locator('[data-dominant="true"]')).toContainText(
      "Noticing hesitation",
    );
    await page.waitForTimeout(1300);
    const cloud = await page
      .locator(".cloud-position:not(.cloud-leaving)")
      .evaluateAll((els) =>
        els.map((el) => ({
          size: parseFloat(getComputedStyle(el).fontSize),
          weight: Number(getComputedStyle(el).fontWeight),
        })),
      );
    const largest = [...cloud].sort((a, b) => b.size - a.size)[0];
    expect(largest.weight).toBe(Math.max(...cloud.map((w) => w.weight)));
    await page.mouse.move(1, 1);
    await page.screenshot({ path: `evidence/polish-${width}.png` });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  }
  await page.getByRole("tab", { name: "global", exact: true }).click();
  const globalWeight = await page
    .locator(".core-value-row")
    .first()
    .evaluate((el) => Number(getComputedStyle(el).fontWeight));
  expect(globalWeight).toBeGreaterThan(650);
  await page.evaluate(() => localStorage.setItem("tompathy-theme", "dark"));
  await page.reload();
  await page.locator('[data-node="paragraph-3"] circle').click();
  await page.mouse.move(1, 1);
  await page.waitForTimeout(1300);
  await page.screenshot({ path: "evidence/polish-dark.png" });
});
