import { createExample } from "../src/core/example";
import { test, expect, type Page } from "@playwright/test";
test.beforeEach(async ({ page }) => {
  await page.addInitScript(() =>
    localStorage.setItem("tompathy-guide-offered-040", "yes"),
  );
});
async function tool(page: Page, name: string) {
  await page
    .getByRole("button", {
      name: name === "How ToMpathy works" ? "Reader menu" : "Development tools",
      exact: true,
    })
    .click();
  await page.getByRole("button", { name, exact: true }).click();
}
test("independent attention, two peaks, bidirectional ambiguity and matching locks", async ({
  page,
}) => {
  await page.goto("/?qa&demo=fieldnotes");
  await expect(page.locator(".reader-content > .region")).toHaveCount(3);
  await expect(
    page.locator(".app-header, .app-footer, .node-explanation"),
  ).toHaveCount(0);
  await expect(page.getByTestId("goals")).toHaveText("hover");
  const values = await page.getByTestId("values").innerHTML();
  const first = page.locator('[data-passage="p2"] [data-sentence="0"]');
  await first.hover();
  await expect(page.locator('[data-dominant="true"]')).toHaveText(
    "Noticing hesitation",
  );
  // Check continuity for a displayed phrase: lower-ranked phrases can now be
  // omitted when the creator cutout leaves insufficient cloud space.
  const shared = await page.locator('[data-goal="focus-0"]').elementHandle();
  await page.locator('[data-passage="p2"] [data-sentence="1"]').hover();
  await expect(page.locator('.spool[data-rank="0"]')).toHaveAttribute(
    "data-selected",
    "sentence-1-2",
  );
  expect(await shared!.evaluate((el) => el.isConnected)).toBe(true);
  const sentence = page.locator('[data-passage="p4"] [data-sentence="1"]');
  await sentence.hover();
  await expect(page.locator('[data-dominant="true"]')).toHaveText(
    "Learning together",
  );
  await expect(page.locator('.spool[data-rank="0"]')).toHaveAttribute(
    "data-selected",
    "sentence-3-2",
  );
  await expect(page.locator('.spool[data-rank="2"]')).toHaveAttribute(
    "data-candidates",
    "story,practical-care",
  );
  await expect(page.locator('.spool[data-level="0"]')).toHaveAttribute(
    "data-candidates",
    "purpose,end",
  );
  expect(await page.getByTestId("values").innerHTML()).toEqual(values);
  await sentence.click();
  await first.hover();
  await expect(page.locator('[data-dominant="true"]')).toHaveText(
    "Learning together",
  );
  await expect(
    page.getByRole("button", { name: "Unlock selection" }),
  ).toHaveCount(2);
  await expect(page.locator(".pyramid svg")).toHaveAttribute("data-peaks", "4");
  const pyramid = await page.locator(".pyramid").boundingBox();
  const reels = await page.getByTestId("odometer").boundingBox();
  expect(reels!.y).toBeGreaterThanOrEqual(pyramid!.y + pyramid!.height);
  expect(reels!.height).toBeLessThan(50);
  await page.locator('[data-node="paragraph-3"] circle').first().hover();
  await expect(page.locator('.spool[data-rank="1"]')).toHaveClass(
    /spool-emphasis/,
  );
  await expect(page.locator('.spool[data-rank="0"]')).toHaveAttribute(
    "data-selected",
    "sentence-3-2",
  );
  await expect(page.locator('[data-dominant="true"]')).toHaveText(
    "Learning together",
  );
  const reel = page.locator('.spool[data-rank="0"]');
  await reel.hover();
  await page.mouse.wheel(0, 100);
  await expect(reel).toHaveAttribute("data-selected", "sentence-3-3");
  await reel.focus();
  await page.keyboard.press("ArrowUp");
  await expect(reel).toHaveAttribute("data-selected", "sentence-3-2");
  await page.locator(".process-lock").click();
  await expect(page.getByTestId("goals")).toHaveText("hover");
  await expect(
    page.getByRole("button", { name: "Unlock selection" }),
  ).toHaveCount(0);
  await sentence.click();
  await page.locator(".inline-lock").click();
  await expect(page.getByTestId("goals")).toHaveText("hover");
  await page.locator('[data-node="paragraph-3"] circle').first().hover();
  expect(
    await page
      .locator(".pyramid-node.descendant")
      .evaluateAll(
        (es) => new Set(es.map((e) => e.getAttribute("data-node"))).size,
      ),
  ).toBe(5);
  expect(
    await page
      .locator(".pyramid-node.ancestor")
      .evaluateAll(
        (es) => new Set(es.map((e) => e.getAttribute("data-node"))).size,
      ),
  ).toBe(4);
  await expect(page.locator(".spool.ambiguous")).toHaveCount(3);
  await expect(
    page.locator('[data-node="practical-care"].ancestor'),
  ).toHaveCount(1);
  await expect(
    page.locator(
      '.hierarchy-crosslink[data-child="paragraph-3"][data-parent="practical-care"]',
    ),
  ).toHaveCount(1);
  await expect(page.getByTestId("goals")).toHaveAttribute("data-total", "13");
  // The aggregate retains all constituent focuses; only those that fit render.
  await expect
    .poll(() => page.locator("[data-goal]:not([aria-hidden])").count())
    .toBeGreaterThan(0);
  await expect(page.locator('[data-passage="p4"]')).toHaveClass(
    /related-passage/,
  );
  await page.screenshot({ path: "evidence/design-branch.png" });
  await page.locator('[data-node="sentence-3-2"] circle').first().click();
  await expect(page.locator('[data-dominant="true"]')).toHaveText(
    "Learning together",
  );
  await expect(page.locator('.spool[data-rank="2"]')).toHaveAttribute(
    "data-candidates",
    "story,practical-care",
  );
  await sentence.click();
  await expect(page.locator('.spool[data-rank="2"]')).toHaveAttribute(
    "data-candidates",
    "story,practical-care",
  );
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Reader menu", exact: true }).click();
  await expect(page.getByLabel("Show hypotheses as a list")).toHaveCount(0);
  await expect(page.getByRole("dialog")).toHaveAccessibleName("Options");
  await expect(
    page.getByRole("dialog").getByLabel("Creator selection"),
  ).toHaveCount(0);
});
test("cloud phrases do not overlap at native width; heading and value explanations work by keyboard", async ({
  page,
}) => {
  await page.setViewportSize({ width: 360, height: 900 });
  await page.goto("/?panel&qa&demo=fieldnotes");
  await page.locator('[data-node="sentence-1-1"] circle').first().click();
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
    page.getByRole("tooltip").filter({ hasText: "Everyday comfort" }),
  ).toContainText("persistent latch");
  await page.keyboard.press("Escape");
  await tool(page, "Reader settings");
  await expect(
    page.getByRole("checkbox", { name: /Word-level goals/ }),
  ).toBeDisabled();
});
test("context changes invalidate scope; explicit revision updates fixed values", async ({
  page,
}) => {
  await page.goto("/?qa&demo=fieldnotes");
  await tool(page, "Context");
  await page
    .getByLabel("Excerpt", { exact: true })
    .fill("A pasted notebook with a competing account.");
  await page.getByRole("button", { name: "Add excerpt", exact: true }).click();
  await expect(
    page.locator(".context-item").filter({ hasText: "Pasted excerpt" }),
  ).toContainText("competing account");
  await page.getByLabel("Analysis scope").selectOption("context");
  await page.getByRole("button", { name: "Close dialog" }).click();
  await expect(page.getByText("A different evidence scope")).toBeVisible();
  await expect(page.getByTestId("values")).toContainText("No values supplied");
  await tool(page, "Context");
  await page.getByLabel("Analysis scope").selectOption("artifact");
  await page.getByRole("button", { name: "Preview example revision" }).click();
  await expect(page.getByRole("dialog")).toContainText("Work within a brief");
  await page.getByRole("button", { name: "Accept this revision" }).click();
  await expect(page.getByTestId("values")).toContainText("Practical care");
  await page.locator('[data-passage="p5"]').hover();
  await expect(page.getByTestId("process")).toContainText(
    "Explain the constraints",
  );
  await tool(page, "Earlier accounts");
  await page
    .getByText("Revision 1 · tompathy-example", { exact: true })
    .click();
  await expect(page.getByRole("dialog")).toContainText("Care for others");
  await expect(page.getByRole("dialog")).toContainText("Design for inclusion");
  await page.getByRole("button", { name: "Close dialog" }).click();
  await expect(page.getByTestId("values")).toContainText("Practical care");
});

test("compact creator header and source export preserve the selected creator and context boundary", async ({
  page,
}) => {
  await page.goto("/?panel&qa&demo=fieldnotes");
  await expect(page.locator(".app-header")).toHaveCount(0);
  await tool(page, "Source text");
  await page
    .getByLabel("Creator to inspect")
    .fill("A different requested creator");
  const promise = page.waitForEvent("download");
  await page
    .getByRole("button", {
      name: "Export analysis request with selected context",
    })
    .click();
  const file = await (await promise).path();
  const { readFile } = await import("node:fs/promises");
  const request = JSON.parse(await readFile(file!, "utf8"));
  expect(request.author).toBe("A different requested creator");
  expect(request.context).toEqual([]);
  await page.getByRole("button", { name: "Close dialog" }).click();
  // A new requested subject never relabels an existing account.
  await tool(page, "Source text");
  await expect(page.getByRole("dialog")).toContainText(
    "Analysis subject: Mara Vale",
  );
});
test("malformed packet, pasted text and session clear expose honest empty state", async ({
  page,
}) => {
  await page.goto("/?qa&demo=fieldnotes");
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
  await page.goto("/?panel&qa&demo=fieldnotes");
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
  await page.goto("/?qa&demo=fieldnotes");
  await tool(page, "Context");
  await page.locator("input[type=file]").setInputFiles({
    name: "notes.md",
    mimeType: "text/markdown",
    buffer: Buffer.from("A note from a synthetic source."),
  });
  await page.getByRole("checkbox", { name: "notes.md", exact: true }).check();
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
  await tool(page, "Context");
  for (const input of await page.locator(".context-item input").all())
    await expect(input).not.toBeChecked();
  await page.getByRole("button", { name: "Remove notes.md" }).click();
  await expect(page.locator(".context-item")).toHaveCount(1);
  await expect(page.locator(".context-item")).toContainText(
    "Fictional studio notebook",
  );
});
test("collection cancellation and 200% zoom preserve usable controls", async ({
  page,
}) => {
  await page.goto("/?qa&demo=fieldnotes");
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
  await expect(page.locator(".context-item")).toHaveCount(1);
  await expect(page.locator(".context-item")).toContainText(
    "Fictional studio notebook",
  );
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

test("unnamed nine-level hierarchy and all supplied values remain reachable in a narrow panel", async ({
  page,
}) => {
  await page.setViewportSize({ width: 360, height: 900 });
  await page.goto("/?panel&qa&demo=fieldnotes");
  const packet = await createExample();
  packet.schemaVersion = "1.6";
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
  await page.getByRole("tab", { name: "creator", exact: true }).click();
  await expect(page.locator(".core-value-row")).toHaveCount(19);
  await expect(page.locator(".core-value-row").first()).toHaveText(
    "Fixture preference 1",
  );
  expect(
    new Set(await page.locator(".core-value-row").allTextContents()),
  ).toEqual(
    new Set(
      packet.hypotheses.filter((h) => h.kind === "value").map((h) => h.label),
    ),
  );
  await page.locator(".core-value-row").last().focus();
  await expect(page.locator(".core-value-row").last()).toBeInViewport();
  expect(
    await page.locator("#values-view").evaluate((el) => el.scrollTop),
  ).toBeGreaterThan(0);
  await page.locator('[data-node="sentence-1-1"] circle').first().click();
  await expect(page.locator(".spool")).toHaveCount(9);
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

test("corner headings, compact attention, four and a half value rows and prototype tabs", async ({
  page,
}) => {
  await page.setViewportSize({ width: 360, height: 900 });
  await page.goto("/?panel&qa&demo=fieldnotes");
  const cloud = await page.locator(".goals-region").boundingBox();
  expect(cloud!.height).toBeLessThanOrEqual(190);
  const valuesView = (await page.locator("#values-view").boundingBox())!;
  const ninth = (await page.locator(".core-value-row").nth(8).boundingBox())!;
  expect(
    (valuesView.y + valuesView.height - ninth.y) / ninth.height,
  ).toBeCloseTo(0.5, 1);
  for (const selector of [
    ".goals-region",
    ".process-region",
    ".values-region",
  ]) {
    const region = await page.locator(selector).boundingBox();
    const title = await page
      .locator(selector + " > .section-heading > h2")
      .boundingBox();
    expect(Math.abs(title!.y - region!.y)).toBeLessThan(2);
    expect(
      Math.abs(title!.x + title!.width - region!.x - region!.width),
    ).toBeLessThan(2);
  }
  await expect(page.locator(".core-value-row")).toHaveCount(9);
  const rows = await page.locator(".core-value-row").evaluateAll((es) =>
    es.map((e) => {
      const r = e.getBoundingClientRect();
      return r.y + r.height / 2;
    }),
  );
  for (let i = 0; i + 1 < rows.length; i += 2)
    expect(Math.abs(rows[i] - rows[i + 1])).toBeLessThan(1);
  const menu = await page
    .getByRole("button", { name: "Reader menu", exact: true })
    .boundingBox();
  expect(menu!.x - cloud!.x).toBeGreaterThanOrEqual(8);
  expect(menu!.y - cloud!.y).toBeGreaterThanOrEqual(6);
  await page.getByRole("tab", { name: "global", exact: true }).click();
  await expect(page.locator(".core-value-row")).toHaveCount(8);
  await expect(page.getByRole("tabpanel")).toContainText("Personal agency");
  await page.getByRole("tab", { name: "creator", exact: true }).click();
  await expect(page.locator(".core-value-row")).toHaveCount(9);
  const world = await page
    .getByRole("tab", { name: "global", exact: true })
    .boundingBox();
  const toggle = page.getByRole("button", { name: "Open search preview" });
  const searchBefore = await toggle.boundingBox();
  expect(searchBefore!.x - world!.x - world!.width).toBeGreaterThanOrEqual(0);
  expect(searchBefore!.x - world!.x - world!.width).toBeLessThan(9);
  await page.getByRole("button", { name: "Open search preview" }).click();
  const search = page.getByRole("textbox", { name: "Search preview" });
  const searchAfter = await toggle.boundingBox();
  expect(searchAfter!.x).toBe(searchBefore!.x);
  const searchBox = (await search.boundingBox())!;
  expect(
    searchBox.x > searchAfter!.x + searchAfter!.width ||
      searchBox.y >= searchAfter!.y + searchAfter!.height,
  ).toBe(true);
  await expect(search).toBeFocused();
  await search.fill("curiosity");
  const requests: string[] = [];
  page.on("request", (r) => requests.push(r.url()));
  await search.press("Enter");
  await expect(
    page.getByRole("status").filter({ hasText: "No query was sent" }),
  ).toBeVisible();
  expect(requests).toEqual([]);
  await search.press("Escape");
  await expect(
    page.getByRole("button", { name: "Open search preview" }),
  ).toBeFocused();
  await page.getByRole("button", { name: "Open search preview" }).click();
  await expect(search).toHaveValue("curiosity");
  await page.screenshot({ path: "evidence/search.png" });
});

test("attention can change within a sentence and lock the pointed frame", async ({
  page,
}) => {
  await page.goto("/?qa&demo=fieldnotes");
  const packet = await createExample();
  packet.revisionOf = packet.id;
  packet.id = "attention-offset-fixture";
  packet.revision = 2;
  const frame = packet.currentAttention!.find((f) => f.span.region === "p4")!;
  const next = structuredClone(frame);
  frame.span.end = 20;
  next.span.start = 20;
  next.items = [next.items[1]];
  packet.currentAttention!.push(next);
  await tool(page, "Import result");
  await page.getByText("Or paste JSON").click();
  await page.getByLabel("Result JSON").fill(JSON.stringify(packet));
  await page.getByRole("button", { name: "Validate & import" }).click();
  await page.getByRole("button", { name: "Accept this revision" }).click();
  const sentence = page.locator('[data-passage="p4"] [data-sentence="0"]');
  await sentence.scrollIntoViewIfNeeded();
  const points = await sentence.evaluate((el) =>
    [5, 35].map((offset) => {
      const range = document.createRange();
      const text = document
        .createTreeWalker(el, NodeFilter.SHOW_TEXT)
        .nextNode()!;
      range.setStart(text, offset);
      range.setEnd(text, offset + 2);
      const r = range.getBoundingClientRect();
      return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
    }),
  );
  await page.mouse.move(points[0].x, points[0].y);
  await expect(page.locator('[data-dominant="true"]')).toHaveText(
    "Watching the players",
  );
  await page.mouse.move(points[1].x, points[1].y);
  await expect(page.locator('[data-dominant="true"]')).toHaveText(
    "Small discoveries",
  );
  await page.mouse.click(points[1].x, points[1].y);
  await page.mouse.move(points[0].x, points[0].y);
  await expect(page.locator('[data-dominant="true"]')).toHaveText(
    "Small discoveries",
  );
  await page.locator(".process-lock").click();
  await expect(page.getByTestId("goals")).toHaveText("hover");
});
