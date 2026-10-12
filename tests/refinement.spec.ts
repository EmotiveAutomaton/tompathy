import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() =>
    localStorage.setItem("tompathy-guide-offered-040", "yes"),
  );
});

test("every expanded option inspects one leaf, in either direction, without changing the lock", async ({
  page,
}) => {
  await page.setViewportSize({ width: 360, height: 900 });
  await page.goto("/?panel");
  // Simulate a platform font that makes the corner label wider.
  await page.addStyleTag({
    content: ".process-region .heading-help { font-family: monospace; }",
  });
  await page
    .locator('[data-root="purpose"][data-node="paragraph-3"] circle')
    .click();
  await page.locator(".spool").nth(1).hover();
  const labels = [
    "Show sustained attention",
    "Make observation concrete",
    "Admit a failed attempt",
    "Show willingness to revise",
  ];
  for (const i of [3, 2, 1, 0, 2, 3]) {
    await page.getByRole("button", { name: labels[i], exact: true }).hover();
    const lit = page.locator('.pyramid-node[data-rank="0"].descendant');
    await expect(lit).toHaveCount(1);
    await expect(lit).toHaveAttribute("data-node", `sentence-3-${i + 1}`);
    await expect(
      page.locator('.pyramid-node[aria-pressed="true"]'),
    ).toHaveCount(1);
    await expect(
      page.locator('.pyramid-node[aria-pressed="true"]'),
    ).toHaveAttribute("data-node", "paragraph-3");
  }
  const first = page.getByRole("button", { name: labels[0], exact: true });
  await first.focus();
  await page.keyboard.press("ArrowDown");
  await expect(
    page.getByRole("button", { name: labels[1], exact: true }),
  ).toBeFocused();
  await expect(
    page.locator('.pyramid-node[aria-pressed="true"]'),
  ).toHaveAttribute("data-node", "paragraph-3");
  await page.screenshot({ path: "evidence/refined-reels.png" });
  const expandedLock = await page.locator(".process-lock").boundingBox();
  const firstBox = await page.locator(".spool-window").first().boundingBox();
  expect(
    Math.abs(expandedLock!.y + expandedLock!.height / 2 - firstBox!.y),
  ).toBeLessThan(4);
  await page.keyboard.press("Escape");
  await expect(page.locator(".spool.is-expanded")).toHaveCount(0);
  await expect(page.locator(".process-lock")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.locator(".process-lock")).toHaveCount(0);
  await page
    .locator('[data-root="purpose"][data-node="paragraph-3"] circle')
    .click();
  await page.locator(".spool").nth(1).hover();
  await page.locator(".process-lock").click();
  await expect(page.locator(".process-lock")).toHaveCount(0);
});

test("corner heading leaves top dots reachable with wider platform fonts and zoom", async ({
  page,
}) => {
  await page.goto("/?panel");
  await page.addStyleTag({
    content: ".process-region .heading-help { font-family: monospace; }",
  });
  for (const [width, zoom] of [
    [360, 1],
    [320, 1],
    [640, 2],
  ]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.evaluate((zoom) => {
      document.documentElement.style.zoom = String(zoom);
    }, zoom);
    const dot = page.locator(
      '[data-root="purpose"][data-node="sentence-1-1"] circle',
    );
    await dot.hover();
    await expect(page.locator('[data-dominant="true"]')).toHaveText(
      "Noticing pauses",
    );
    const heading = await page
      .locator(".process-region .section-heading h2")
      .boundingBox();
    const point = await dot.boundingBox();
    expect(
      point!.x + point!.width < heading!.x ||
        point!.y > heading!.y + heading!.height,
    ).toBe(true);
  }
});

test("blocked focus changes pulse both locks, ignore jitter, cool down and respect reduced motion", async ({
  page,
}) => {
  await page.goto("/");
  await page.locator('[data-passage="p4"] [data-sentence="0"]').click();
  const nodes = page.locator(
    '[data-root="purpose"][data-node^="sentence-1-"] circle',
  );
  for (let i = 0; i < 8; i++) await nodes.first().hover();
  await expect(page.locator('[data-lock-reminder="active"]')).toHaveCount(0);
  for (let i = 0; i < 4; i++) {
    await nodes.nth(i % 3).hover();
    await page.waitForTimeout(75);
  }
  await expect(page.locator('[data-lock-reminder="active"]')).toHaveCount(2);
  const pulse = await page
    .locator(".process-lock")
    .evaluate((el) => el.getAnimations()[0].effect!.getTiming());
  expect(pulse.iterations).toBe(2);
  const lock = await page.locator(".process-lock").boundingBox();
  const reel = await page.getByTestId("odometer").boundingBox();
  expect(lock!.x).toBeLessThan(reel!.x);
  expect(lock!.y).toBeLessThan(reel!.y);
  await expect(page.locator('[data-lock-reminder="active"]')).toHaveCount(0);
  for (let i = 0; i < 5; i++) {
    await nodes.nth(i % 3).hover();
    await page.waitForTimeout(75);
  }
  await expect(page.locator('[data-lock-reminder="active"]')).toHaveCount(0);
  await page.locator(".process-lock").click();
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.locator('[data-passage="p4"] [data-sentence="0"]').click();
  for (let i = 0; i < 4; i++) {
    await nodes.nth(i % 3).hover();
    await page.waitForTimeout(75);
  }
  await expect(page.locator('[data-lock-reminder="active"]')).toHaveCount(2);
  expect(
    await page
      .locator(".process-lock")
      .evaluate((el) => el.getAnimations()[0].effect!.getTiming().iterations),
  ).toBe(1);
  await page.locator(".process-lock").click();
  await expect(page.locator('[data-lock-reminder="active"]')).toHaveCount(0);
  await expect(page.getByTestId("goals")).toHaveText("<- hover");
});

test("dots fit their bricks; cue contrast and layout hold in light, dark and system dark", async ({
  page,
}) => {
  await page.goto("/?panel");
  for (const height of [660, 900, 1250]) {
    await page.setViewportSize({ width: 360, height });
    await page.waitForTimeout(100);
    const clipped = await page.locator(".pyramid-node").evaluateAll((nodes) =>
      nodes.flatMap((el) => {
        const circle = el.querySelector("circle")!;
        const path = el.querySelector("path")!;
        const x = +circle.getAttribute("cx")!,
          y = +circle.getAttribute("cy")!,
          r = +circle.getAttribute("r")!;
        return Array.from({ length: 24 }, (_, i) => {
          const a = (i * Math.PI) / 12;
          return path.isPointInFill(
            new DOMPoint(
              x + Math.cos(a) * (r + 0.5),
              y + Math.sin(a) * (r + 0.5),
            ),
          );
        }).every(Boolean)
          ? []
          : [el.getAttribute("data-instance")];
      }),
    );
    expect(clipped).toEqual([]);
  }
  await expect(page.locator(".order-uncertain title")).toHaveText([
    "Order uncertain",
    "Order uncertain",
  ]);
  await page.setViewportSize({ width: 360, height: 900 });
  for (const theme of ["light", "dark", "system"]) {
    await page.emulateMedia({ colorScheme: "dark" });
    await page
      .getByRole("button", { name: "Reader menu", exact: true })
      .click();
    await page.getByRole("button", { name: theme, exact: true }).click();
    await page.getByRole("button", { name: "Close dialog" }).click();
    const contrast = await page.locator(".attention-cue").evaluate((el) => {
      const css = getComputedStyle(el),
        bg = getComputedStyle(el.closest(".region")!).backgroundColor;
      const rgb = (value: string) =>
        value
          .match(/[\d.]+/g)!
          .slice(0, 3)
          .map(Number);
      const background = rgb(bg),
        foreground = rgb(css.color).map(
          (c, i) => c * +css.opacity + background[i] * (1 - +css.opacity),
        );
      const luminance = (c: number[]) =>
        c
          .map((v) => v / 255)
          .map((v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4))
          .reduce((s, v, i) => s + v * [0.2126, 0.7152, 0.0722][i], 0);
      const a = luminance(background),
        b = luminance(foreground);
      return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    });
    expect(contrast).toBeGreaterThanOrEqual(4.5);
    await page.screenshot({ path: `evidence/refined-${theme}.png` });
  }
  const creator = page.getByRole("tab", { name: "creator", exact: true });
  await creator.focus();
  await page.keyboard.press("ArrowRight");
  await expect(
    page.getByRole("tab", { name: "global", exact: true }),
  ).toBeFocused();
  await page.keyboard.press("Home");
  await expect(creator).toBeFocused();
  await expect(page.getByTestId("values")).toBeVisible();
});
