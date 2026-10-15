import { test, expect } from "@playwright/test";

test("capture access guidance remains distinct from unexpected adapter failures", async () => {
  const globals = globalThis as typeof globalThis & { chrome: unknown };
  const original = globals.chrome;
  let response: unknown;
  let failure = "Cannot access contents of the page. Missing host permission.";
  Object.assign(globals, {
    chrome: {
      runtime: { id: "capture-test", sendMessage: async () => response },
      tabs: { query: async () => [{ id: 123 }] },
      scripting: {
        executeScript: async () => {
          throw Error(failure);
        },
      },
    },
  });
  try {
    const { capturePage, PageCaptureUnavailable } =
      await import("../src/browser");
    await expect(capturePage()).rejects.toBeInstanceOf(PageCaptureUnavailable);
    failure = "Cannot access a chrome:// URL";
    await expect(capturePage()).rejects.toBeInstanceOf(PageCaptureUnavailable);
    response = { error: "No readable page text was found" };
    await expect(capturePage()).rejects.toBeInstanceOf(PageCaptureUnavailable);
    response = { error: "Unexpected adapter data failure" };
    const error = await capturePage().catch((e: Error) => e);
    expect(error).not.toBeInstanceOf(PageCaptureUnavailable);
    expect(error).toBeInstanceOf(Error);
    expect((error as Error).message).toContain(
      "Unexpected adapter data failure",
    );
  } finally {
    Object.assign(globals, { chrome: original });
  }
});

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() =>
    localStorage.setItem("tompathy-guide-offered-040", "yes"),
  );
});

test("contour categories and compact channel cards fit small panels in both themes", async ({
  page,
}) => {
  test.setTimeout(60000);
  await page.setViewportSize({ width: 360, height: 900 });
  await page.goto("/?panel");
  await expect(page.locator(".core-values .current-drive")).toHaveCount(7);
  await expect(page.locator(".core-values .current-constructed")).toHaveCount(
    3,
  );
  for (const width of [360, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await page
      .getByRole("button", { name: "Drive SEEKING", exact: true })
      .hover();
    const card = page.getByRole("tooltip");
    await expect(card.locator(".drive-brain")).toBeVisible();
    await expect(card.locator("figcaption")).toHaveCount(0);
    await expect(card.locator(".value-confidence-legend")).toHaveCSS(
      "font-size",
      "12px",
    );
    const body = (await card.locator(".value-introduction p").boundingBox())!,
      brain = (await card.locator(".drive-brain").boundingBox())!,
      title = (await card.locator(".value-card-title > span").boundingBox())!,
      axis = (await card.locator(".value-confidence-axis").boundingBox())!,
      legend = (await card.locator(".value-confidence-legend").boundingBox())!;
    expect(body.x + body.width).toBeLessThan(brain.x);
    expect(brain.width).toBeLessThanOrEqual(80);
    expect(brain.height).toBeLessThanOrEqual(72);
    expect(
      title.x + title.width <= axis.x + 1 ||
        title.y + title.height <= axis.y + 1,
    ).toBe(true);
    const cardBounds = (await card.boundingBox())!;
    expect(axis.x + axis.width).toBeLessThan(cardBounds.x + cardBounds.width);
    expect(legend.width).toBeLessThanOrEqual(axis.width);
    expect(
      await card
        .locator(".brain-anatomy")
        .evaluate((el) => Number(getComputedStyle(el).opacity)),
    ).toBeLessThan(0.5);
    expect(
      await card
        .locator(".brain-network")
        .evaluate((el) => Number(getComputedStyle(el).opacity)),
    ).toBe(1);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.screenshot({
      path: `evidence/contour-drive-${width}.png`,
      animations: "disabled",
    });
    await page
      .getByRole("button", {
        name: "Constructed value Intellectual humility",
        exact: true,
      })
      .hover();
    await expect(card.locator(".drive-brain")).toHaveCount(0);
    const constructedAxis = (await card
        .locator(".value-confidence-axis")
        .boundingBox())!,
      constructedBounds = (await card.boundingBox())!;
    expect(constructedAxis.x + constructedAxis.width).toBeLessThan(
      constructedBounds.x + constructedBounds.width,
    );
    const text = (await card.locator(".value-introduction p").boundingBox())!;
    expect(text.x).toBeCloseTo(body.x, 0);
    await page.screenshot({
      path: `evidence/contour-value-${width}.png`,
      animations: "disabled",
    });
  }
  await page.setViewportSize({ width: 360, height: 900 });
  await page.emulateMedia({ colorScheme: "dark" });
  await page.getByRole("button", { name: "Drive CARE", exact: true }).hover();
  await page.screenshot({
    path: "evidence/contour-drive-dark.png",
    animations: "disabled",
  });
});

test("wheel over a resolved reel advances and locks from a soft hover, including beside expanded lists", async ({
  page,
}) => {
  await page.goto("/?demo=fieldnotes");
  await page.locator('[data-passage="p2"] [data-sentence="0"]').hover();
  const reel = page.locator('.spool[data-rank="0"]');
  await expect(reel).toHaveAttribute("data-selected", "sentence-1-1");
  await expect(page.locator(".process-lock")).toHaveCount(0);
  await reel.locator(".spool-window").hover();
  await page.mouse.wheel(0, 100);
  await expect(reel).toHaveAttribute("data-selected", "sentence-1-2");
  await expect(page.locator(".process-lock")).toBeVisible();
  await expect(page.locator(".pyramid-node.chosen")).toHaveAttribute(
    "data-node",
    "sentence-1-2",
  );
  await page.waitForTimeout(160);
  await page.mouse.wheel(0, -100);
  await expect(reel).toHaveAttribute("data-selected", "sentence-1-1");
  await page.locator('[data-node="paragraph-3"]').click();
  const higher = page.locator('.spool[data-rank="1"]');
  await higher.locator(".spool-window").hover();
  await expect(page.locator(".spool.is-expanded")).not.toHaveCount(0);
  await expect(higher).toHaveAttribute("data-selected", "paragraph-3");
  await page.mouse.wheel(0, 100);
  await expect(higher).not.toHaveAttribute("data-selected", "paragraph-3");
  const next = await higher.getAttribute("data-selected");
  expect(next).toBeTruthy();
  await expect(page.locator(".pyramid-node.chosen")).toHaveAttribute(
    "data-node",
    next!,
  );
  await expect(page.locator(".process-lock")).toBeVisible();
});
