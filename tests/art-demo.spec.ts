import { test, expect } from "@playwright/test";
import { createArtExample, artSnapshot } from "../src/core/art-example";
import { sentences } from "../src/core/sentences";
import { goalGraph, hierarchyLayout } from "../src/core/hierarchy";

test("commissioned essay demo covers every sentence once with explicit invented confidence", async () => {
  const packet = await createArtExample();
  const count = packet.artifact.regions.reduce(
    (n, r) => n + sentences(r.anchor.exact).length,
    0,
  );
  expect(packet.currentAttention).toHaveLength(count);
  expect(packet.goalHierarchy!.nodes.filter((n) => n.span)).toHaveLength(count);
  expect(
    new Set(
      packet
        .goalHierarchy!.nodes.filter((n) => n.span)
        .map((n) => JSON.stringify(n.span)),
    ).size,
  ).toBe(count);
  expect(packet.ghostReadings).toHaveLength(count);
  expect(packet.ghostReadings!.every((g) => g.confidence !== null)).toBe(true);
  expect(packet.provider.method).toContain(
    "997 authored sentence interpretations; 0 provisional",
  );
  expect(packet.provider.method).toContain("Invented");
  expect(
    packet.hypotheses.filter((h) => h.valueCategory === "drive"),
  ).toHaveLength(7);
  expect(
    packet.hypotheses
      .filter((h) => h.kind === "value")
      .every((h) => h.preferenceTrace),
  ).toBe(true);
  expect(packet.makers[0].label).toBe("Abraham Haskins");
  expect(
    packet.artifact.regions.some((r) =>
      r.anchor.exact.includes("Appreciation (\\Psi)"),
    ),
  ).toBe(true);
  const layout = hierarchyLayout(goalGraph(packet.goalHierarchy!.nodes));
  expect(layout.dense).toBe(false);
  expect(layout.tiles).toHaveLength(packet.goalHierarchy!.nodes.length);
  expect(
    new Set(goalGraph(packet.goalHierarchy!.nodes).roots.map((n) => n.rank))
      .size,
  ).toBeGreaterThan(1);
  expect(layout.usefulTier).toBe(2);
  expect(layout.edges[3] - layout.edges[2]).toBeGreaterThan(layout.edges[1]);
});

test("extra-parent endpoints stay subtle while zooming and do not add Tab stops", async ({
  page,
}) => {
  await page.addInitScript(() =>
    localStorage.setItem("tompathy-guide-offered-040", "yes"),
  );
  await page.goto("/?panel&demo=fieldnotes");
  await page.setViewportSize({ width: 360, height: 900 });
  const root = page.locator('[data-node="purpose"]');
  await root.focus();
  await root.press("Enter");
  // Two extra relationships are inside this root. The third belongs to the
  // independent practical-care root and correctly stays outside this selection.
  await expect(page.locator(".hierarchy-crosslink")).toHaveCount(2);
  const dots = page.locator(".hierarchy-link-end");
  await expect(dots).toHaveCount(4);
  const diameter = () =>
    dots.evaluateAll((es) => es.map((e) => e.getBoundingClientRect().width));
  const before = await diameter();
  for (const width of before) expect(width).toBeCloseTo(2.6, 1);
  await root.press("+");
  await page.waitForTimeout(230);
  for (const width of await diameter()) expect(width).toBeCloseTo(2.6, 1);
  await expect(page.locator('.pyramid-node[tabindex="0"]')).toHaveCount(1);
  await root.press("Home");
  await page.screenshot({ path: "evidence/connector-endpoints.png" });
});

test("essay is the default; one graph Tab entry, arrow navigation, real variable font and fit", async ({
  page,
}) => {
  test.setTimeout(60000);
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.addInitScript(() =>
    localStorage.setItem("tompathy-guide-offered-040", "yes"),
  );
  await page.goto("/");
  await expect(page.locator("h1")).toContainText("Art: A Unifying Model");
  await expect(page.locator(".creator-control")).toContainText(
    "Abraham Haskins",
  );
  await expect(page.locator(".pyramid-node")).toHaveCount(
    (await createArtExample()).goalHierarchy!.nodes.length,
  );
  await expect(page.locator("[data-passage]")).toHaveCount(
    artSnapshot.blocks.length,
  );
  const entry = page.locator('.pyramid-node[tabindex="0"]');
  await expect(entry).toHaveCount(1);
  await page.locator(".process-region .section-question").focus();
  await page.keyboard.press("Tab");
  await expect(entry).toBeFocused();
  await page.keyboard.press("ArrowDown");
  await expect(page.locator(".pyramid-node.chosen")).toBeFocused();
  await page.keyboard.press("ArrowRight");
  await expect(page.locator(".pyramid-node.chosen")).toHaveAttribute(
    "data-node",
    /art-passage-/,
  );
  await page.keyboard.press("+");
  await expect(page.locator(".hierarchy-fit")).toBeVisible();
  await page.keyboard.press("Home");
  await expect(page.locator(".hierarchy-fit")).toBeHidden();
  await page.keyboard.press("Tab");
  await expect(entry).not.toBeFocused();
  await page.keyboard.press("Escape");
  const first = page.locator('[data-passage="p3"] [data-sentence="0"]');
  await first.hover();
  await expect(page.locator(".cloud-position")).not.toHaveCount(0);
  await page.evaluate(() => document.fonts.ready);
  const ink = await page.evaluate(async () => {
    const weights = [337, 355, 399];
    await Promise.all(
      weights.map((weight) =>
        document.fonts.load(`${weight} 30px "ToMpathy Confidence"`),
      ),
    );
    const element = document.createElement("canvas");
    element.width = 700;
    element.height = 70;
    const canvas = element.getContext("2d")!;
    return weights.map((weight) => {
      canvas.clearRect(0, 0, 700, 70);
      canvas.font = `${weight} 30px "ToMpathy Confidence"`;
      canvas.fillText("Understanding other minds", 5, 45);
      const pixels = canvas.getImageData(0, 0, 700, 70).data;
      let coverage = 0;
      for (let i = 3; i < pixels.length; i += 4) coverage += pixels[i];
      return coverage;
    });
  });
  // Stroke weight must change continuously; advance widths may stay constant.
  expect(new Set(ink).size).toBe(3);
  expect(ink[0]).toBeLessThan(ink[1]);
  expect(ink[1]).toBeLessThan(ink[2]);
  await expect(page.locator(".cloud-position").first()).toHaveCSS(
    "font-family",
    /ToMpathy Confidence/,
  );
  const last = page
    .locator(`[data-passage="p${artSnapshot.blocks.length}"] [data-sentence]`)
    .last();
  await last.click();
  await expect(page.locator(".pyramid-node.chosen")).toHaveAttribute(
    "data-node",
    new RegExp(`art-sentence-${artSnapshot.blocks.length - 1}-`),
  );
  await page.keyboard.press("Escape");
  await first.click();
  await page.screenshot({ path: "evidence/art-preview.png" });
  expect(errors).toEqual([]);
});
