import { test, expect } from "@playwright/test";
import { createExample } from "../src/core/example";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() =>
    localStorage.setItem("tompathy-guide-offered-040", "yes"),
  );
});

test("order uncertainty survives shared siblings with different visual homes", async ({
  page,
}) => {
  const packet = await createExample();
  packet.goalHierarchy!.orderUncertainGroups = [
    {
      ...packet.goalHierarchy!.orderUncertainGroups![0],
      id: "shared-paragraph-order",
      nodes: ["paragraph-3", "paragraph-4"],
    },
  ];
  await page.addInitScript(
    (p) =>
      sessionStorage.setItem(
        "tompathy-session",
        JSON.stringify({
          sessionVersion: "1.0",
          artifact: p.artifact,
          packet: p,
          context: [],
          scope: "artifact",
        }),
      ),
    packet,
  );
  await page.goto("/?panel");
  expect(
    await page.locator('[data-node="paragraph-3"]').getAttribute("data-root"),
  ).not.toBe(
    await page.locator('[data-node="paragraph-4"]').getAttribute("data-root"),
  );
  await expect(
    page.getByRole("button", { name: "Order uncertain", exact: true }),
  ).toHaveCount(1);
  await page
    .getByRole("button", { name: "Order uncertain", exact: true })
    .focus();
  await expect(page.locator(".pyramid-node.chosen")).toHaveAttribute(
    "data-node",
    "story",
  );
  for (const id of ["paragraph-3", "paragraph-4"])
    await expect(page.locator(`[data-node="${id}"]`)).toHaveClass(/descendant/);
});

test("soft inspection persists, replaces freely, aggregates whole branches and leaves deliberate locks intact", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator(".attention-cue")).toHaveText("hover");
  const sentence = page.locator('[data-passage="p4"] [data-sentence="0"]');
  await sentence.hover();
  const initial = await page.getByTestId("goals").textContent();
  await page.mouse.move(2, 2);
  await expect(page.locator('.spool[data-rank="0"]')).toHaveAttribute(
    "data-selected",
    "sentence-3-1",
  );
  await expect(page.getByTestId("goals")).toHaveText(initial!);
  await expect(page.locator(".process-lock")).toHaveCount(0);
  const root = page.locator('[data-node="purpose"] circle');
  await root.hover();
  await expect
    .poll(() => page.locator("[data-goal]:not([aria-hidden])").count())
    .toBeGreaterThan(12);
  const count = await page.locator("[data-goal]:not([aria-hidden])").count();
  await page.mouse.move(2, 2);
  await expect(page.locator("[data-goal]:not([aria-hidden])")).toHaveCount(
    count,
  );
  await expect
    .poll(() =>
      page
        .getByTestId("goals")
        .evaluate(
          (el) =>
            el
              .getAnimations({ subtree: true })
              .filter((a) => a.playState === "running").length,
        ),
    )
    .toBe(0);
  await page.screenshot({ path: "evidence/pass-branch-cloud.png" });
  const overlaps = await page
    .locator("[data-goal]:not([aria-hidden])")
    .evaluateAll((es) => {
      const boxes = es.map((e) => e.getBoundingClientRect());
      return boxes.flatMap((a, i) =>
        boxes
          .slice(i + 1)
          .filter(
            (b) =>
              Math.min(a.right, b.right) - Math.max(a.left, b.left) > 2 &&
              Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 2,
          ),
      ).length;
    });
  expect(overlaps).toBe(0);
  await sentence.hover();
  await expect(page.locator('.spool[data-rank="0"]')).toHaveAttribute(
    "data-selected",
    "sentence-3-1",
  );
  await sentence.click();
  await root.hover();
  await expect(page.locator('.spool[data-rank="0"]')).toHaveAttribute(
    "data-selected",
    "sentence-3-1",
  );
  await page.keyboard.press("Escape");
});

test("one label threshold, fixed anchors, smooth home, uncertain siblings and closed absent reels", async ({
  page,
}) => {
  await page.goto("/?panel");
  await page.setViewportSize({ width: 360, height: 950 });
  const graph = page.locator(".pyramid>svg");
  await page.locator(".order-uncertain").first().focus();
  await expect(page.locator('[data-node="paragraph-1"].chosen')).toHaveCount(1);
  await expect(page.locator('[data-rank="0"].descendant')).toHaveCount(3);
  await page.locator('[data-node="assembly"] circle').hover();
  await expect(page.locator(".aperture-closed")).toHaveCount(3);
  await expect(
    page.locator(".aperture-closed .spool-window").first(),
  ).toHaveCSS("height", "2px");
  await graph.focus();
  const threshold = Number(await graph.getAttribute("data-label-zoom"));
  for (let k = 1; k < threshold * 1.3; k *= 1.35)
    await page.keyboard.press("+");
  await expect(graph).toHaveAttribute("data-label-reveal", "1.000");
  expect(await page.locator(".hierarchy-label").count()).toBe(
    await page.locator(".pyramid-node").count(),
  );
  const anchors = await page
    .locator(".pyramid-node foreignObject")
    .evaluateAll((es) =>
      es.map((e) => e.parentElement!.getAttribute("transform")),
    );
  await page.keyboard.press("ArrowRight");
  await page.waitForTimeout(230);
  expect(
    await page
      .locator(".pyramid-node foreignObject")
      .evaluateAll((es) =>
        es.map((e) => e.parentElement!.getAttribute("transform")),
      ),
  ).toEqual(anchors);
  await page.screenshot({ path: "evidence/pass-graph-labels.png" });
  await page.getByRole("button", { name: "Fit whole hierarchy" }).click();
  await expect(graph).toHaveAttribute("data-zoom", "1.000");
  await graph.focus();
  await page.keyboard.press("ArrowLeft");
  await page.keyboard.press("-");
  await expect(graph.locator(":scope>g")).toHaveAttribute(
    "transform",
    "translate(0,0) scale(1)",
  );
  await page.screenshot({ path: "evidence/pass-graph-fit.png" });
});

test("evidence card shows two visual scales and at most three bullets, no explanatory prose", async ({
  page,
}) => {
  await page.goto("/");
  await page.locator('[data-passage="p5"] [data-sentence="0"]').focus();
  const tooltip = page.locator(".tompathy-reading-help");
  await expect(tooltip).toBeVisible();
  await expect(tooltip.locator(".reading-axis")).toHaveCount(2);
  await expect(tooltip).toContainText("Less · creator involvement · More");
  await expect(tooltip).toContainText("Less · confidence · More");
  await expect(tooltip.locator("li")).toHaveCount(2);
  await expect(tooltip.locator("p,h3,small")).toHaveCount(0);
  const axes = await tooltip.locator(".reading-axis").evaluateAll((rows) =>
    rows.map((row) => {
      const scale = row
        .querySelector(".reading-scale")!
        .getBoundingClientRect();
      const value = row
        .querySelector(".reading-value")!
        .getBoundingClientRect();
      return {
        right: scale.right,
        below: scale.top >= value.bottom - 2,
        leftAligned: Math.abs(value.left - scale.left) < 1,
      };
    }),
  );
  expect(axes.every((a) => a.below && a.leftAligned)).toBe(true);
  expect(axes[0].right).toBeCloseTo(axes[1].right, 1);
  await page.screenshot({ path: "evidence/pass-tooltip.png" });
});

test("review desk offers twelve distinct prompts, copy and a portable download", async ({
  page,
  context,
}) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto("/review.html");
  await expect(page.locator(".destination")).toHaveCount(3);
  await expect(
    page.getByRole("button", { name: /Live creator/ }),
  ).toBeDisabled();
  await page.getByRole("link", { name: /Icon prompts/ }).click();
  await expect(page.locator("#prompts .prompt-card")).toHaveCount(12);
  const prompts = await page
    .locator("#prompts .prompt-card textarea")
    .evaluateAll((es) => es.map((e) => (e as HTMLTextAreaElement).value));
  expect(new Set(prompts).size).toBe(12);
  expect(prompts.every((p) => p.split(/\s+/).length > 65)).toBe(true);
  await page.locator("#prompts .prompt-card button").first().click();
  await expect(page.getByRole("status")).toContainText("Copied");
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(
    prompts[0],
  );
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: "Download all 12 prompts" }).click(),
  ]);
  expect(download.suggestedFilename()).toBe("tompathy-icon-prompts.txt");
  const stream = await download.createReadStream();
  const chunks = [];
  for await (const chunk of stream!) chunks.push(chunk);
  const text = Buffer.concat(chunks).toString("utf8");
  for (const prompt of prompts) expect(text).toContain(prompt);
  await page.screenshot({ path: "evidence/icon-prompts-preview.png" });
  await page.setViewportSize({ width: 360, height: 900 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.locator("#prompts .prompt-card textarea").first().focus();
  await page.keyboard.press("Tab");
  await expect(page.locator("#prompts .prompt-card button").first()).toBeFocused();
  await expect(page.locator("#prompts .prompt-card button").first()).toHaveCSS(
    "outline-style",
    "solid",
  );
  await page.screenshot({ path: "evidence/icon-prompts-narrow.png" });
});

test("creator switch lives above attention, clears another creator's account, and Options lives in values", async ({
  page,
}) => {
  const packet = await createExample();
  packet.makers.push({
    ...packet.makers[0],
    id: "maker-2",
    label: "Editorial collaborator",
  });
  await page.addInitScript(
    (p) =>
      sessionStorage.setItem(
        "tompathy-session",
        JSON.stringify({
          sessionVersion: "1.0",
          artifact: p.artifact,
          packet: p,
          context: [],
          scope: "artifact",
        }),
      ),
    packet,
  );
  await page.goto("/");
  const picker = page.getByLabel("Creator selection");
  await expect(picker).toBeVisible();
  const nameArrow = await page.locator(".creator-current").evaluate((el) => {
    const name = el.querySelector("span")!.getBoundingClientRect(),
      arrow = el.querySelector("svg")!.getBoundingClientRect();
    return arrow.left - name.right;
  });
  expect(nameArrow).toBeGreaterThanOrEqual(2);
  expect(nameArrow).toBeLessThanOrEqual(4);
  const pickerBox = (await picker.boundingBox())!;
  const visibleName = (await page.locator(".creator-current").boundingBox())!;
  expect(pickerBox.width).toBeCloseTo(visibleName.width, 1);

  await expect(page.locator(".creator-brain")).toBeVisible();
  await expect(
    page.locator(".values-bottom").getByRole("button", { name: "Reader menu" }),
  ).toBeVisible();
  await page.locator('[data-passage="p4"] [data-sentence="0"]').click();
  await picker.selectOption("maker-2");
  await expect(page.locator(".process-lock")).toHaveCount(0);
  await expect(page.locator("[data-goal]:not([aria-hidden])")).toHaveCount(0);
  await expect(page.locator("[data-ghost-kind]")).toHaveCount(0);
  await picker.selectOption("maker-1");
  await page.locator('[data-passage="p3"] [data-sentence="0"]').hover();
  await expect(page.locator('[data-dominant="true"]')).toHaveText(
    "An invitation to connect",
  );
  await expect
    .poll(() => page.locator('[data-dominant="true"] .cloud-line').count())
    .toBe(2);
  await page.mouse.move(1, 1);
  await page.waitForTimeout(2600);
  await page.screenshot({ path: "evidence/creator-cloud-preview.png" });
});
