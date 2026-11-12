import { test, expect } from "./built-page";
import { readFile } from "node:fs/promises";

test("clearing a reading keeps the empty values message centered", async ({
  page,
}) => {
  await page.goto("/?qa&demo=fieldnotes");
  await page
    .getByRole("button", { name: "Development tools", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Reader settings", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Clear session", exact: true })
    .click();
  await expect(
    page.getByText("Start with a piece of writing", { exact: true }),
  ).toBeVisible();
  const empty = page.locator("#values-view .quiet-empty");
  await expect(empty).toHaveText("No values supplied");
  const message = (await empty.boundingBox())!;
  const region = (await page.locator("#values-view").boundingBox())!;
  expect(
    Math.abs(message.x + message.width / 2 - region.x - region.width / 2),
  ).toBeLessThan(3);
  expect(
    Math.abs(message.y + message.height / 2 - region.y - region.height / 2),
  ).toBeLessThan(4);
  await page.screenshot({ path: "evidence/three-views-empty.png" });
});

test("core values is a scrollable hierarchy table with traced branches and full details", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", e => errors.push(e.message));
  await page.goto("/?demo=fieldnotes");
  const table = page.getByRole("table", { name: "Core values hierarchy" });
  await expect(table).toBeVisible();
  const scroll = page.locator(".values-table-scroll");
  expect(await scroll.evaluate(e => e.scrollWidth > e.clientWidth && e.scrollHeight > e.clientHeight)).toBe(true);
  const value = table.locator('[data-cell="value:work-care"]');
  await value.scrollIntoViewIfNeeded();
  await value.hover();
  expect(await table.locator(".values-table-links path").count()).toBeGreaterThan(0);
  const edges = await table.locator(".values-table-links path").evaluateAll(paths => paths.map(p => ({ from: p.getAttribute("data-from"), to: p.getAttribute("data-to"), width: p.getAttribute("stroke-width") })));
  expect(new Set(edges.map(e => e.width)).size).toBeGreaterThan(1);
  await value.focus();
  await value.press("ArrowDown");
  await expect(table.locator('[data-cell="goal:sentence-4-3"]')).toBeFocused();
  await page.keyboard.press("Control+End");
  expect(await scroll.evaluate(e => e.scrollTop)).toBeGreaterThan(0);
  await page.keyboard.press("Control+Home");
  expect(await scroll.evaluate(e => e.scrollTop)).toBeLessThan(12);
  const care = table.getByRole("button", { name: "Drive CARE", exact: true });
  await care.focus();
  await expect(page.locator(".hover-card")).toHaveCount(0);
  await care.press("Enter");
  await expect(page.locator(".modal")).toBeVisible();
  await expect(page.locator(".modal .preference-vector")).toHaveCount(3);
  await page.keyboard.press("Escape");
  await page.getByRole("tab", { name: "author", exact: true }).click();
  await expect(table).toBeVisible();
  await expect(page.locator("[data-work]")).toHaveCount(0);
  await page.setViewportSize({ width: 420, height: 960 });
  await table.locator('[data-cell="value:care"]').scrollIntoViewIfNeeded();
  await table.locator('[data-cell="value:care"]').hover();
  await page.screenshot({ path: "evidence/values-table-narrow.png" });
  await page.emulateMedia({ colorScheme: "dark" });
  await page.screenshot({ path: "evidence/values-table-dark.png" });
  expect(errors).toEqual([]);
});

for (const history of [false, true])
  test(`${history ? "History" : "Final text"} remains gated with no fictional author`, async ({
    page,
  }) => {
    const packet = JSON.parse(
      await readFile(
        `engine/tests/fixtures/packets/value-view-${history ? "history" : "t0"}.json`,
        "utf8",
      ),
    );
    await page.addInitScript(
      (packet) =>
        sessionStorage.setItem(
          "tompathy-session",
          JSON.stringify({
            sessionVersion: "1.0",
            artifact: packet.artifact,
            packet,
            scope: "artifact",
            context: [],
          }),
        ),
      packet,
    );
    await page.goto("/");
    const landscape = page.locator(".values-landscape");
    await expect(landscape).toHaveAttribute("data-illustration", "false");
    await expect(landscape).toContainText(
      history ? "No admitted comparison fit" : "Final text only",
    );
    if (!history)
      await expect(landscape.locator(".landscape-cell")).toHaveCount(0);
    await expect(landscape.locator(".value-leader")).toHaveCount(0);
    await page.getByRole("tab", { name: "author", exact: true }).click();
    await expect(landscape).toContainText("awaits in-scope works");
    await expect(landscape.locator("[data-work]")).toHaveCount(0);
    await page.getByRole("tab", { name: "global", exact: true }).click();
    await expect(landscape).toContainText("No admitted population model");
  });
