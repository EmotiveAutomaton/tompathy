import { test, expect } from "@playwright/test";

test("graph click centers source; keys navigate cells; Find appears only after scrolling; Escape clears focus artifact", async ({
  page,
}) => {
  await page.addInitScript(() =>
    localStorage.setItem("tompathy-guide-offered-040", "yes"),
  );
  await page.goto("/");
  const cell = page.locator('[data-node="sentence-3-1"]');
  await cell.locator("circle").click();
  const find = page.getByRole("button", {
    name: "Find highlighted text in page",
  });
  await expect(find).toBeHidden();
  const centerError = () =>
    page.locator(".active-sentence").evaluate((el) => {
      const r = document.createRange();
      r.selectNodeContents(el);
      const b = r.getBoundingClientRect();
      return Math.abs(b.top + b.height / 2 - innerHeight / 2);
    });
  await expect.poll(centerError).toBeLessThan(4);
  await page.waitForTimeout(220);
  await page.keyboard.press("ArrowDown");
  await expect(page.locator(".pyramid-node.chosen")).toHaveAttribute(
    "data-node",
    "sentence-3-2",
  );
  await expect.poll(centerError).toBeLessThan(4);
  await page.keyboard.press("ArrowUp");
  await expect(page.locator(".pyramid-node.chosen")).toHaveAttribute(
    "data-node",
    "sentence-3-1",
  );
  await page.keyboard.press("ArrowRight");
  await expect(page.locator(".pyramid-node.chosen")).toHaveAttribute(
    "data-node",
    "paragraph-3",
  );
  await page.keyboard.press("ArrowLeft");
  await expect(page.locator(".pyramid-node.chosen")).toHaveAttribute(
    "data-rank",
    "0",
  );
  await expect.poll(centerError).toBeLessThan(4);
  await page.waitForTimeout(250);
  await expect(find).toBeHidden();
  await page.evaluate(() => window.scrollBy(0, -180));
  await expect(find).toBeVisible();
  await find.click();
  await expect(find).toBeHidden();
  await expect.poll(centerError).toBeLessThan(4);
  await page.keyboard.press("Escape");
  const text = page.locator('[data-passage="p4"] [data-sentence="0"]');
  await text.click();
  await page.keyboard.press("Escape");
  await expect(page.locator(".process-lock")).toHaveCount(0);
  await expect(text).not.toBeFocused();
  await expect(text).toHaveCSS("outline-style", "none");
  await page.screenshot({ path: "evidence/graph-keyboard-navigation.png" });
});
