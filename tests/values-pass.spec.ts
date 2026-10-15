import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() =>
    localStorage.setItem("tompathy-guide-offered-040", "yes"),
  );
  await page.goto("/?demo=fieldnotes");
  await expect(page.getByTestId("values")).toBeVisible();
});

test("value trajectories and independent perspectives fit a narrow panel", async ({
  page,
}) => {
  await page.getByRole("tab", { name: "creator", exact: true }).click();
  const creatorNames = await page.locator(".core-value-row").allTextContents();
  await page
    .getByRole("button", { name: "Care for others", exact: true })
    .hover();
  const card = page.getByRole("tooltip");
  await expect(card.locator(".value-confidence-axis")).toContainText("0.22 on 0–1");
  await expect(card.locator(".preference-vector")).toHaveCount(3);
  await expect(card.locator(".preference-observations li")).toHaveCount(3);
  await page.waitForTimeout(220);
  await page.screenshot({ path: "evidence/values-creator.png" });
  await page.getByRole("tab", { name: "global", exact: true }).click();
  const globalNames = await page.locator(".core-value-row").allTextContents();
  expect(globalNames.filter((n) => creatorNames.includes(n))).toHaveLength(4);
  expect(globalNames.filter((n) => !creatorNames.includes(n))).toHaveLength(4);
  await page
    .getByRole("button", { name: "Personal agency", exact: true })
    .hover();
  await expect(card.locator(".value-confidence-axis")).toContainText("0.88 on 0–1");
  await page.waitForTimeout(220);
  await page.screenshot({ path: "evidence/values-global.png" });
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto("/?panel&demo=fieldnotes");
  await page
    .getByRole("button", { name: "Care for others", exact: true })
    .focus();
  await expect(card.locator(".preference-chart")).toBeVisible();
  const box = (await card.boundingBox())!;
  expect(box.x).toBeGreaterThanOrEqual(0);
  expect(box.x + box.width).toBeLessThanOrEqual(360);
  expect(box.y).toBeGreaterThanOrEqual(0);
  expect(box.y + box.height).toBeLessThanOrEqual(800);
  await page.waitForTimeout(220);
  await page.screenshot({ path: "evidence/values-narrow.png" });
  await page
    .getByRole("button", { name: "Care for others", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toContainText("Care for others");
  await expect(
    page.getByRole("dialog").locator(".preference-vector"),
  ).toHaveCount(3);
});

test("ambiguous branch find centers the highlighted group and evidence arrows retain direction", async ({
  page,
}) => {
  await page.locator('[data-node="paragraph-3"] circle').click();
  const find = page.getByRole("button", {
    name: "Find highlighted text in page",
  });
  await expect(find).toBeHidden();
  await expect(page.locator(".spool.ambiguous").first()).toBeVisible();
  await page.waitForTimeout(900);
  const offset = await page
    .locator(".related-passage [data-sentence]")
    .evaluateAll((els) => {
      const rs = els.flatMap((el) => {
        const r = document.createRange();
        r.selectNodeContents(el);
        return [...r.getClientRects()];
      });
      return Math.abs(
        (Math.min(...rs.map((r) => r.top)) +
          Math.max(...rs.map((r) => r.bottom))) /
          2 -
          innerHeight / 2,
      );
    });
  expect(offset).toBeLessThan(3);
  await page.keyboard.press("Escape");
  await page
    .locator('[data-passage="p3"] [data-sentence="0"] .tompathy-ghost')
    .hover();
  const help = page.locator(".tompathy-reading-help");
  await expect(help).toBeVisible();
  await expect(help.locator(".reading-value").last()).toHaveText(
    "84% confident",
  );
  await expect(
    help.getByRole("img", { name: "Less creator involvement", exact: true }),
  ).toBeVisible();
  await expect(
    help.getByRole("img", { name: "More creator involvement", exact: true }),
  ).toBeVisible();
  await expect(help.locator(".reading-value").first()).toHaveCSS(
    "text-align",
    "left",
  );
  await expect(help.locator(".reading-ramp")).toHaveCSS(
    "background-image",
    /linear-gradient/,
  );
  await page.waitForTimeout(220);
  await page.screenshot({ path: "evidence/reading-directional-evidence.png" });
});
