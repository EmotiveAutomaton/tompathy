import { test, expect } from "@playwright/test";

test("attention settles while held and responds again to a new sentence", async ({
  page,
}) => {
  await page.addInitScript(() =>
    localStorage.setItem("tompathy-guide-offered-040", "yes"),
  );
  await page.goto("/?panel&demo=fieldnotes");
  const first = page.locator(
    '[data-root="purpose"][data-node="sentence-1-1"] circle',
  );
  await first.click();
  await expect(page.locator(".process-lock")).toBeVisible();
  await expect(page.locator('[data-dominant="true"]')).toHaveText(
    "Noticing hesitation",
  );
  await page.mouse.move(1, 1);
  const running = () =>
    page
      .getByTestId("goals")
      .evaluate(
        (el) =>
          el
            .getAnimations({ subtree: true })
            .filter((a) => a.playState === "running").length,
      );
  await expect.poll(running).toBe(0);
  const position = () => page.locator('[data-dominant="true"]').boundingBox();
  const resting = await position();
  await page.waitForTimeout(250);
  expect(await position()).toEqual(resting);
  await page.keyboard.press("Escape");
  await expect(page.getByTestId("goals")).toHaveText("hover");
  await first.hover();
  await expect(page.locator('[data-dominant="true"]')).toHaveText(
    "Noticing hesitation",
  );
  await expect.poll(running).toBeGreaterThan(0);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect.poll(running).toBe(0);
});
