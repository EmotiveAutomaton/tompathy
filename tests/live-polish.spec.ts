import { test, expect } from "@playwright/test";
import { makeArtifact } from "../src/core/artifact";
import { createWebsiteDemo } from "../src/core/website-demo";
import { regionSentences } from "../src/core/sentences";
import { demoWorkValues, demoGlobalValues } from "../src/core/example-values";

test("grouped page text is one bounded reading unit with distinct demo perspectives", async () => {
  const artifact = await makeArtifact(
    ["References & Assets. Download the CV. Browse project sources."],
    "https://abrahamhaskins.org/",
    "Home",
  );
  artifact.regions[0].pageHint = { unit: "group", section: "A".repeat(300) };
  const packet = createWebsiteDemo(artifact);
  expect(regionSentences(artifact.regions[0])).toHaveLength(1);
  expect(packet.ghostReadings).toHaveLength(1);
  expect(packet.goalHierarchy!.nodes.every((n) => n.label.length <= 250)).toBe(
    true,
  );
  const values = packet.hypotheses.filter((h) => h.kind === "value"),
    work = demoWorkValues(packet, values),
    global = demoGlobalValues(packet, values);
  expect(work).toHaveLength(10);
  expect(global).toHaveLength(25);
  expect(work.some((h) => h.label === "Belonging")).toBe(true);
  expect(work.some((h) => h.label === "PANIC/GRIEF")).toBe(false);
  expect(work[0].support!.value).not.toBe(values[0].support!.value);
  expect(work[0].preferenceTrace!.observations).not.toEqual(
    values[0].preferenceTrace!.observations,
  );
});

test("capped cloud clears the creator cutout; work cards and keyboard tabs fit narrow panels", async ({
  page,
}) => {
  test.setTimeout(60000);
  await page.addInitScript(() =>
    localStorage.setItem("tompathy-guide-offered-040", "yes"),
  );
  await page.setViewportSize({ width: 360, height: 900 });
  await page.goto("/?panel");
  await expect(
    page.getByRole("tab", { name: "current work only", exact: true }),
  ).toHaveAttribute("aria-selected", "true");
  await expect(page.locator(".pyramid-node")).not.toHaveCount(0);
  const largest = await page
    .locator(".pyramid-node")
    .evaluateAll((es) =>
      es
        .find((e) =>
          e
            .getAttribute("aria-label")
            ?.includes("Explain art through intention"),
        )
        ?.getAttribute("data-node"),
    );
  expect(largest).toBeTruthy();
  const branch = page.locator(`.pyramid-node[data-node="${largest}"]`);
  await branch.focus();
  await branch.press("Enter");
  await expect
    .poll(() => page.getByTestId("goals").getAttribute("data-total"))
    .not.toBe("0");
  await page.waitForTimeout(650);
  await expect(
    page.getByRole("button", { name: "Reload reading" }),
  ).toHaveCount(0);
  const headingBox = (await page.locator("#goals-title").boundingBox())!,
    panelBox = (await page.locator(".goals-region").boundingBox())!;
  expect(
    Math.abs(headingBox.x + headingBox.width - panelBox.x - panelBox.width),
  ).toBeLessThan(2);
  const words = page.locator(".cloud-position");
  const count = await words.count();
  expect(count).toBeGreaterThan(2);
  expect(count).toBeLessThanOrEqual(18);
  expect(
    Number(await page.getByTestId("goals").getAttribute("data-total")),
  ).toBeGreaterThan(count);
  const boxes = await words.evaluateAll((es) =>
    es.map((e) => {
      const r = e.getBoundingClientRect();
      return { x: r.x, y: r.y, w: r.width, h: r.height };
    }),
  );
  const creator = (await page.locator(".creator-control").boundingBox())!;
  for (let i = 0; i < boxes.length; i++) {
    const a = boxes[i];
    expect(
      a.x >= creator.x + creator.width + 6 ||
        a.y >= creator.y + creator.height + 6,
    ).toBe(true);
    for (const b of boxes.slice(i + 1))
      expect(
        a.x + a.w <= b.x + 1 ||
          b.x + b.w <= a.x + 1 ||
          a.y + a.h <= b.y + 1 ||
          b.y + b.h <= a.y + 1,
      ).toBe(true);
  }
  const portrait = (await page.locator(".creator-brain").boundingBox())!,
    name = (await page.locator(".creator-current > span").boundingBox())!;
  expect(
    Math.abs(portrait.x + portrait.width / 2 - name.x - name.width / 2),
  ).toBeLessThan(3);
  await page
    .getByRole("button", { name: "Drive SEEKING", exact: true })
    .hover();
  const card = page.getByRole("tooltip");
  await expect(card.locator(".drive-brain")).toBeVisible();
  await expect(card.locator(".support-wheel")).toHaveCount(0);
  expect(
    await card
      .locator(".brain-cortex")
      .evaluate((el) => getComputedStyle(el).fill),
  ).not.toBe("rgb(0, 0, 0)");
  await expect(card.locator(".value-confidence-number")).toHaveText("0.91 on 0–1");
  await expect(card.locator(".preference-chart")).toContainText(
    "Earlier life → Present",
  );
  // The axis reflects the supplied lifetime range; observed event phases remain
  // in the separate evidence list introduced by trajectory inspection.
  await expect(card.locator(".preference-chart")).not.toContainText("Draft");
  await expect(card.locator(".preference-observations")).toContainText("Draft");
  const chart = (await card.locator(".preference-chart").boundingBox())!,
    cardBox = (await card.boundingBox())!;
  expect(chart.width / cardBox.width).toBeGreaterThan(0.85);
  await page.screenshot({ path: "evidence/value-work-card.png" });
  await page
    .getByRole("tab", { name: "current work only", exact: true })
    .focus();
  await page.keyboard.press("ArrowRight");
  await expect(
    page.getByRole("tab", { name: "creator", exact: true }),
  ).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press("ArrowRight");
  await expect(
    page.getByRole("tab", { name: "global", exact: true }),
  ).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press("Home");
  await page
    .getByRole("button", { name: "Open search preview", exact: true })
    .click();
  await page
    .getByRole("textbox", { name: "Search preview", exact: true })
    .fill("belonging");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({ path: "evidence/values-work-tabs.png" });
  await page.getByRole("button", { name: "Close search", exact: true }).click();
  await page.emulateMedia({ colorScheme: "dark" });
  await page
    .getByRole("button", { name: "Drive SEEKING", exact: true })
    .hover();
  expect(
    await page
      .locator(".hover-card .brain-cortex")
      .evaluate((el) => getComputedStyle(el).fill),
  ).not.toBe("rgb(0, 0, 0)");
  await page.screenshot({ path: "evidence/value-work-card-dark.png" });
});
