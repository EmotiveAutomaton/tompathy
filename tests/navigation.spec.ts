import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() =>
    localStorage.setItem("tompathy-guide-offered-040", "yes"),
  );
  await page.goto("/");
  await expect(page.getByTestId("values")).toContainText("Care for others");
});

test("complete story: zoom, readable cells, drag without selecting, fit and clear", async ({
  page,
}) => {
  const graph = page.locator(".pyramid > svg");
  await expect(graph).toHaveAttribute("data-zoom", "1.000");
  const ids = await page
    .locator(".pyramid-node[data-node^='sentence-']")
    .evaluateAll((es) => [
      ...new Set(es.map((e) => e.getAttribute("data-node"))),
    ]);
  expect(ids).toHaveLength(30);
  await expect(page.locator('.pyramid-node[data-rank="0"]')).toHaveCount(30);
  expect(ids).toContain("sentence-9-3");
  await expect(page.locator('[data-node="editing"]')).toHaveCount(1);
  await page.locator('[data-passage="p10"] [data-sentence="2"]').click();
  await expect(
    page.locator('.spool[data-selected="sentence-9-3"]'),
  ).toHaveCount(1);
  await graph.focus();
  await page.keyboard.press("+");
  await page.keyboard.press("+");
  await expect(
    page.getByRole("button", { name: "Fit whole hierarchy" }),
  ).toBeVisible();
  const box = (await graph.boundingBox())!;
  await page.mouse.move(box.x + box.width * 0.3, box.y + box.height * 0.4);
  await page.mouse.wheel(0, -700);
  await expect
    .poll(async () => Number(await graph.getAttribute("data-zoom")))
    .toBeGreaterThan(2);
  await graph.focus();
  const threshold = Number(await graph.getAttribute("data-label-zoom"));
  while (Number(await graph.getAttribute("data-zoom")) < threshold * 1.3) {
    await page.keyboard.press("+");
    await page.waitForTimeout(220);
  }
  await expect
    .poll(async () => page.locator(".hierarchy-label").count())
    .toBeGreaterThan(0);
  await page.screenshot({ path: "evidence/navigation-zoom.png" });
  const before = await graph.locator(":scope > g").getAttribute("transform");
  await page.mouse.move(box.x + box.width * 0.5, box.y + box.height * 0.6);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width * 0.6, box.y + box.height * 0.7, {
    steps: 8,
  });
  await page.mouse.up();
  await expect(graph.locator(":scope > g")).not.toHaveAttribute(
    "transform",
    before!,
  );
  await expect(
    page.locator('.spool[data-selected="sentence-9-3"]'),
  ).toHaveCount(1);
  await page.getByRole("button", { name: "Fit whole hierarchy" }).click();
  await expect(graph).toHaveAttribute("data-zoom", "1.000");
  await graph.click({ position: { x: box.width - 4, y: box.height - 4 } });
  await expect(page.locator(".process-lock")).toHaveCount(0);
  await expect(graph).toHaveCSS("outline-style", "none");
  await graph.focus();
  await page.keyboard.press("Home");
  await expect(graph).toHaveCSS("outline-style", "solid");
  await page.screenshot({ path: "evidence/navigation-fit.png" });
});

test("find holds the sentence, settles grey, rearms on article scroll; tooltip separates axes", async ({
  page,
}) => {
  await page.locator('[data-passage="p9"] [data-sentence="0"]').click();
  const find = page.getByRole("button", {
    name: "Find highlighted text in page",
  });
  await expect(find).toBeVisible();
  const lockBox = (await page.locator(".process-lock").boundingBox())!;
  const findBox = (await find.boundingBox())!;
  expect(findBox.width).toBe(lockBox.width);
  expect(findBox.height).toBe(lockBox.height);
  expect(findBox.y).toBeGreaterThan(lockBox.y + lockBox.height);
  await page.evaluate(() => window.scrollTo(0, 0));
  await find.click();
  await expect(find).toBeHidden();
  await page.waitForTimeout(900);
  await expect(
    page.locator('.spool[data-selected="sentence-8-1"]'),
  ).toHaveCount(1);
  const scrollBefore = await page.evaluate(() => scrollY);
  await page.evaluate(() => window.scrollBy(0, -80));
  await expect
    .poll(() => page.evaluate(() => scrollY))
    .toBeLessThan(scrollBefore);
  await expect(find).toBeVisible();
  await page.keyboard.press("Escape");
  await page
    .locator('[data-passage="p5"] [data-sentence="0"] .tompathy-ghost')
    .hover({ position: { x: 12, y: 8 } });
  const tooltip = page.locator(".tompathy-reading-help");
  await expect(tooltip).toBeVisible();
  await expect(tooltip.locator(".reading-sample")).toHaveText("Aa");
  await expect(tooltip).toContainText("Less · creator involvement · More");
  await expect(tooltip).toContainText("Less · confidence · More");
  await expect(tooltip.locator("li")).toHaveCount(2);
  await page.screenshot({ path: "evidence/reading-evidence-card.png" });
});

test("all thirty article sentences resolve to exactly one matching graph cell and back", async ({
  page,
}) => {
  // Each passage's source offset must select the same cell as that cell itself.
  const source = page.locator("[data-passage] [data-sentence]");
  await expect(source).toHaveCount(30);
  for (let i = 0; i < 30; i++) {
    const item = source.nth(i);
    const passage = await item.evaluate((el) =>
      el.closest("[data-passage]")!.getAttribute("data-passage"),
    );
    const index = Number(await item.getAttribute("data-sentence"));
    const id = `sentence-${Number(passage!.slice(1)) - 1}-${index + 1}`;
    await item.focus();
    await expect(page.locator(".pyramid-node.chosen")).toHaveCount(1);
    await expect(page.locator(".pyramid-node.chosen")).toHaveAttribute(
      "data-node",
      id,
    );
    await page.locator(`[data-node="${id}"] circle`).click();
    await expect(page.locator('.spool[data-rank="0"]')).toHaveAttribute(
      "data-selected",
      id,
    );
    await expect(item).toHaveClass(/active-sentence/);
    await expect(
      item.getByRole("button", { name: "Unlock selection" }),
    ).toBeVisible();
    await page.keyboard.press("Escape");
  }
});
