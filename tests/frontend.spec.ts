import { createExample } from "../src/core/example";
import { test, expect, type Page } from "@playwright/test";
async function tool(page: Page, name: string) {
  await page.getByRole("button", { name: "Reader menu", exact: true }).click();
  await page.getByRole("button", { name, exact: true }).click();
}
test("three panels, stable cloud anchor, sentence spools, branching highlights and lock", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator(".reader-content > .region")).toHaveCount(3);
  await expect(page.locator(".app-header, .app-footer")).toHaveCount(0);
  await page.waitForTimeout(1000);
  const anchor = await page.locator('[data-goal="invite"]').boundingBox();
  const values = await page.getByTestId("values").innerHTML();
  const sentence = page.locator('[data-passage="p4"] [data-sentence="1"]');
  await sentence.hover();
  await expect(page.locator('.spool[data-level="3"]')).toHaveAttribute(
    "data-selected",
    "sentence-3-2",
  );
  await expect(page.locator('.spool[data-level="0"]')).toHaveAttribute(
    "data-selected",
    "purpose",
  );
  await expect(page.getByTestId("goals")).toContainText("Test an assumption");
  expect(await page.getByTestId("values").innerHTML()).toEqual(values);
  await page.waitForTimeout(950);
  const moved = await page.locator('[data-goal="invite"]').boundingBox();
  expect(
    Math.abs(anchor!.x + anchor!.width / 2 - (moved!.x + moved!.width / 2)),
  ).toBeLessThan(2);
  await sentence.click();
  await page.locator('[data-passage="p2"] [data-sentence="0"]').hover();
  await expect(page.locator('.spool[data-level="3"]')).toHaveAttribute(
    "data-selected",
    "sentence-3-2",
  );
  await expect(
    page.getByRole("button", { name: "Unlock selection" }),
  ).toBeVisible();
  await expect(page.locator(".pyramid")).toBeVisible();
  const pyramid = await page.locator(".pyramid").boundingBox();
  const reel = page.locator('.spool[data-level="3"]');
  const reels = await page.getByTestId("odometer").boundingBox();
  expect(reels!.y).toBeGreaterThan(pyramid!.y + pyramid!.height);
  expect(reels!.height).toBeLessThan(70);
  await reel.hover();
  await page.mouse.wheel(0, 100);
  await expect(reel).toHaveAttribute("data-selected", "sentence-3-3");
  await reel.focus();
  await page.keyboard.press("ArrowUp");
  await expect(reel).toHaveAttribute("data-selected", "sentence-3-2");
  await page.keyboard.press("Escape");
  await page.locator(".process-region .section-heading").hover();
  await page.locator('[data-node="paragraph-3"]').hover();
  await expect(page.locator(".pyramid-node.descendant")).toHaveCount(5);
  await expect(page.locator(".pyramid-node.ancestor")).toHaveCount(3);
  await expect(page.locator(".spool.ambiguous")).toHaveCount(1);
  await expect(page.locator('[data-passage="p4"]')).toHaveClass(
    /related-passage/,
  );
  await page.screenshot({ path: "evidence/design-branch.png" });
  await page.getByRole("button", { name: "Reader menu", exact: true }).click();
  await page.getByLabel("Show hypotheses as a list").check();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await expect(page.locator(".pyramid-list")).toBeVisible();
});
test("cloud phrases do not overlap at native width; heading and value explanations work by keyboard", async ({
  page,
}) => {
  await page.setViewportSize({ width: 360, height: 900 });
  await page.goto("/?panel");
  await page.waitForTimeout(1100);
  const boxes = await page
    .locator(".cloud-position button")
    .evaluateAll((buttons) =>
      buttons.map((b) => {
        const r = b.getBoundingClientRect();
        return { left: r.left, right: r.right, top: r.top, bottom: r.bottom };
      }),
    );
  for (let i = 0; i < boxes.length; i++)
    for (let j = i + 1; j < boxes.length; j++) {
      const a = boxes[i],
        b = boxes[j];
      expect(
        a.right <= b.left ||
          b.right <= a.left ||
          a.bottom <= b.top ||
          b.bottom <= a.top,
      ).toBe(true);
    }
  const sizes = await page
    .locator(".cloud-position button")
    .evaluateAll((es) =>
      es.map((e) => parseFloat(getComputedStyle(e).fontSize)),
    );
  expect(Math.max(...sizes) / Math.min(...sizes)).toBeGreaterThan(2.9);
  const headingSize = await page
    .locator("#goals-title")
    .evaluate((e) => parseFloat(getComputedStyle(e).fontSize));
  expect(Math.min(...sizes)).toBeLessThan(headingSize);
  await page.getByRole("button", { name: "Restraint", exact: true }).hover();
  await expect(page.getByRole("tooltip")).toContainText("Restraint");
  await page.getByRole("button", { name: "Curiosity", exact: true }).hover();
  await expect(page.getByRole("tooltip")).toContainText("Curiosity");
  await expect(page.getByRole("tooltip")).not.toContainText("Restraint");
  const tooltip = await page.getByRole("tooltip").evaluate((e) => ({
    scroll: e.scrollHeight > e.clientHeight,
    events: getComputedStyle(e).pointerEvents,
  }));
  expect(tooltip).toEqual({ scroll: false, events: "none" });
  const cells = await page
    .locator(".core-value-row")
    .evaluateAll((es) => es.map((e) => e.getBoundingClientRect().x));
  expect(new Set(cells).size).toBe(2);
  await page.locator(".pyramid").hover({ position: { x: 1, y: 1 } });
  await page.getByRole("button", { name: "About Core values" }).focus();
  await expect(page.getByRole("tooltip")).toContainText("latent preferences");
  await page
    .getByRole("button", { name: "Care for others", exact: true })
    .focus();
  await expect(
    page.getByRole("tooltip").filter({ hasText: "Where this comes from" }),
  ).toContainText("Specific decision");
  await page.keyboard.press("Escape");
  await tool(page, "Reader settings");
  await expect(
    page.getByRole("checkbox", { name: /Word-level goals/ }),
  ).toBeDisabled();
});
test("context changes invalidate scope; explicit revision updates fixed values", async ({
  page,
}) => {
  await page.goto("/");
  await tool(page, "Context");
  await page
    .getByLabel("Excerpt", { exact: true })
    .fill("A pasted notebook with a competing account.");
  await page.getByRole("button", { name: "Add excerpt", exact: true }).click();
  await expect(page.locator(".context-item")).toContainText(
    "competing account",
  );
  await page.getByLabel("Analysis scope").selectOption("context");
  await page.getByRole("button", { name: "Close dialog" }).click();
  await expect(page.getByText("A different evidence scope")).toBeVisible();
  await expect(page.getByTestId("values")).toContainText("No values supplied");
  await tool(page, "Context · 1");
  await page.getByLabel("Analysis scope").selectOption("artifact");
  await page.getByRole("button", { name: "Preview example revision" }).click();
  await expect(page.getByRole("dialog")).toContainText("Work within a brief");
  await page.getByRole("button", { name: "Accept this revision" }).click();
  await expect(page.getByTestId("values")).toContainText("Practical care");
  await page.locator('[data-passage="p5"]').hover();
  await expect(page.getByTestId("process")).toContainText(
    "Explain the constraints",
  );
  await tool(page, "Earlier accounts 1 retained revisions");
  await page
    .getByText("Revision 1 · tompathy-example", { exact: true })
    .click();
  await expect(page.getByRole("dialog")).toContainText("Care for others");
  await expect(page.getByRole("dialog")).toContainText("Design for inclusion");
  await page.getByRole("button", { name: "Close dialog" }).click();
  await expect(page.getByTestId("values")).toContainText("Practical care");
});

test("compact author header and source export preserve the selected author and context boundary", async ({
  page,
}) => {
  await page.goto("/?panel");
  await expect(page.locator(".app-header")).toHaveCount(0);
  await tool(page, "Source text");
  await page
    .getByLabel("Author to inspect")
    .fill("A different requested author");
  const promise = page.waitForEvent("download");
  await page
    .getByRole("button", {
      name: "Export analysis request with selected context",
    })
    .click();
  const file = await (await promise).path();
  const { readFile } = await import("node:fs/promises");
  const request = JSON.parse(await readFile(file!, "utf8"));
  expect(request.author).toBe("A different requested author");
  expect(request.context).toEqual([]);
  await page.getByRole("button", { name: "Close dialog" }).click();
  // A new requested subject never relabels an existing account.
  await tool(page, "Source text");
  await expect(page.getByRole("dialog")).toContainText(
    "Analysis subject: The garden designer",
  );
});
test("malformed packet, pasted text and session clear expose honest empty state", async ({
  page,
}) => {
  await page.goto("/");
  await tool(page, "Import result");
  await page.getByText("Or paste JSON").click();
  await page.getByLabel("Result JSON").fill("{broken");
  await page.getByRole("button", { name: "Validate & import" }).click();
  await expect(page.getByRole("dialog").getByRole("alert")).toBeVisible();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await tool(page, "Source text");
  await page
    .getByLabel("Paste a different text")
    .fill("This is a new text, written only for this browser test.");
  await page.getByRole("button", { name: "Use pasted text" }).click();
  await expect(
    page.getByText("Maker estimates are awaiting an analysis source.", {
      exact: false,
    }),
  ).toBeVisible();
  await tool(page, "Reader settings");
  await page.getByRole("button", { name: "Clear session" }).click();
  await expect(page.getByText("Start with a piece of writing")).toBeVisible();
});
test("narrow dark panel, reduced motion and keyboard dialog focus", async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 900 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/?panel");
  await tool(page, "Reader settings");
  await page.getByRole("button", { name: "dark", exact: true }).click();
  await page.keyboard.press("Escape");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await expect(page.getByTestId("values")).toBeInViewport();
  await page.getByTestId("process").evaluate((el) => {
    el.scrollTop = el.scrollHeight;
  });
  await expect(
    page.getByRole("heading", { name: "About Current attention", exact: true }),
  ).toBeInViewport();
  await expect(
    page.getByRole("heading", { name: "About Core values", exact: true }),
  ).toBeInViewport();
  await page.getByTestId("process").evaluate((el) => {
    el.scrollTop = 0;
  });
  await page.screenshot({ path: "evidence/panel-dark-320.png" });
  await tool(page, "How ToMpathy works");
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: "Reader menu" })).toBeFocused();
});
test("session save/load, file context and explicit imported-context selection", async ({
  page,
}) => {
  await page.goto("/");
  await tool(page, "Context");
  await page.locator("input[type=file]").setInputFiles({
    name: "notes.md",
    mimeType: "text/markdown",
    buffer: Buffer.from("A note from a synthetic source."),
  });
  await page.locator(".context-item input[type=checkbox]").check();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await tool(page, "Reader settings");
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Save session", exact: true }).click();
  const saved = await downloadPromise;
  const file = await saved.path();
  await page.getByRole("button", { name: "Clear session" }).click();
  await tool(page, "Reader settings");
  await page.locator("input[type=file]").setInputFiles(file!);
  await expect(
    page.getByText("Session loaded as a detached snapshot.", { exact: false }),
  ).toBeVisible();
  await tool(page, "Context · 1");
  await expect(page.locator(".context-item input")).not.toBeChecked();
  await page.getByRole("button", { name: "Remove notes.md" }).click();
  await expect(page.locator(".context-item")).toHaveCount(0);
});
test("collection cancellation and 200% zoom preserve usable controls", async ({
  page,
}) => {
  await page.goto("/");
  await tool(page, "Context");
  await page.getByText("Retrieve public sources", { exact: true }).click();
  await page.route("https://example.com/slow", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 2000));
    await route
      .fulfill({
        status: 200,
        body: "An excerpt that arrived too late.",
        contentType: "text/plain",
      })
      .catch(() => {});
  });
  await page.getByLabel("URLs, one per line").fill("https://example.com/slow");
  await page.getByRole("button", { name: "Collect selected sources" }).click();
  await page.getByRole("button", { name: "Cancel collection" }).click();
  await expect(page.getByRole("dialog")).toContainText("Collection cancelled");
  await expect(page.locator(".context-item")).toHaveCount(0);
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.setViewportSize({ width: 640, height: 1000 });
  await page.evaluate(() => {
    document.documentElement.style.zoom = "2";
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await tool(page, "Reader settings");
  await expect(
    page.getByRole("button", { name: "Close dialog" }),
  ).toBeInViewport();
  const bounds = await page.getByRole("dialog").boundingBox();
  expect(bounds!.y).toBeGreaterThanOrEqual(0);
  expect(bounds!.y + bounds!.height).toBeLessThanOrEqual(1000);
  await page.screenshot({ path: "evidence/zoom-200.png" });
});

test("unnamed eight-level hierarchy and top nine values fit a narrow panel", async ({
  page,
}) => {
  await page.setViewportSize({ width: 360, height: 900 });
  await page.goto("/?panel");
  const packet = await createExample();
  packet.schemaVersion = "1.3";
  packet.revisionOf = packet.id;
  packet.id = "deep-review-fixture";
  packet.revision = 2;
  const nodes = packet.goalHierarchy!.nodes;
  for (const node of nodes)
    if (node.parentId === "purpose") node.parentId = "extra-3";
  for (let i = 0; i < 4; i++)
    nodes.push({
      ...nodes[0],
      id: `extra-${i}`,
      parentId: i ? `extra-${i - 1}` : "purpose",
      label: `Intermediate goal ${i + 1}`,
      level: undefined,
    });
  const value = packet.hypotheses.find((h) => h.kind === "value")!;
  for (let i = 0; i < 10; i++)
    packet.hypotheses.push({
      ...value,
      id: `extra-value-${i}`,
      label: `Fixture preference ${i + 1}`,
      support: { ...value.support!, value: 0.95 - i * 0.02 },
    });
  await tool(page, "Import result");
  await page.getByText("Or paste JSON").click();
  await page.getByLabel("Result JSON").fill(JSON.stringify(packet));
  await page.getByRole("button", { name: "Validate & import" }).click();
  await page.getByRole("button", { name: "Accept this revision" }).click();
  await expect(page.locator(".core-value-row")).toHaveCount(9);
  await expect(page.locator(".core-value-row").first()).toHaveText(
    "Fixture preference 1",
  );
  await expect(page.locator(".core-value-row").last()).toHaveText(
    "Fixture preference 9",
  );
  await expect(page.locator(".core-value-row").last()).toBeInViewport();
  await page.locator('[data-node="sentence-3-2"]').click();
  await expect(page.locator(".spool")).toHaveCount(8);
  await expect(page.locator(".spool small")).toHaveCount(0);
  const broadest = page.locator('.spool[data-level="0"]');
  await broadest.focus();
  await expect(broadest).toBeInViewport();
  await expect(broadest).toHaveAttribute("data-selected", "purpose");
  await expect(page.locator(".pyramid")).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});
