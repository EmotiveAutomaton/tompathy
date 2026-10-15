import { expect } from "@playwright/test";
import { mkdir, mkdtemp, writeFile, readFile } from "node:fs/promises";
import { createServer } from "node:http";
import path from "node:path";
import { openReview } from "./chrome-review.mjs";

await mkdir(".local", { recursive: true });
await mkdir("evidence", { recursive: true });
const profile = await mkdtemp(path.resolve(".local/review-check-"));
let current;
const connections = [];
let fixtureServer;
let originalProcess;
const receipt = {
  verifiedAt: new Date().toISOString(),
  profile: "isolated ordinary Google Chrome",
  checks: [],
};
try {
  current = await openReview({ profile });
  originalProcess = current.launchedProcess;
  connections.push(current.browser);
  receipt.browser = current.receipt.chromeVersion;
  receipt.build = current.receipt.build;
  expect(current.receipt.action).toBe("Installed extension");
  receipt.checks.push("Fresh ordinary Chrome installation is enabled");
  const context = current.browser.contexts()[0];
  const guide = context
    .pages()
    .find((p) => p.url() === current.receipt.reviewUrl);
  const errors = [];
  guide.on("pageerror", (error) => errors.push(error.message));
  await expect(guide.locator("#build")).toContainText(
    `Installed · ${JSON.parse(await readFile("dist/manifest.json", "utf8")).version_name} · build ${receipt.build}`,
  );
  await expect(
    guide.getByRole("heading", { name: "A place to look closer." }),
  ).toBeVisible();
  await guide.screenshot({
    path: "evidence/review-desk.png",
    fullPage: true,
    scale: "css",
  });
  await expect(guide.locator(".destination")).toHaveCount(3);
  await expect(
    guide.getByRole("link", { name: /Open the live essay/ }),
  ).toHaveAttribute("href", "https://abrahamhaskins.org/art/");
  await expect(
    guide.getByRole("link", { name: /Open the live homepage/ }),
  ).toHaveAttribute("href", "https://abrahamhaskins.org/");
  await guide.getByRole("link", { name: /Icon prompts/ }).click();
  await expect(guide.locator("#prompts .prompt-card")).toHaveCount(12);
  await expect(guide.locator(".logo-study")).toHaveCount(4);
  await guide.locator(".prompt-card button").first().click();
  await expect(guide.getByRole("status")).toContainText(
    /Copied|Prompt selected/,
  );
  await guide.screenshot({
    path: "evidence/icon-prompts-native.png",
    scale: "css",
  });
  await guide.getByRole("link", { name: "← Review desk" }).click();
  receipt.checks.push(
    "Three-entry dashboard, four generated logo studies and twelve copyable prompts open in ordinary Chrome",
  );
  // Deterministic native regression uses the offline fixture. The separate
  // website-validation command exercises the real public website.
  const source = await context.newPage();
  await source.goto(new URL("example.html", current.receipt.reviewUrl).href);
  await source.waitForLoadState();
  const widthBefore = await source.evaluate(() => innerWidth);
  await source.getByRole("button", { name: "Open Maker Reader" }).click();
  current = await openReview({ profile, showGuide: false });
  connections.push(current.browser);
  expect(current.receipt.action).toBe("Resumed existing installation");
  let panel = current.browser
    .contexts()[0]
    .pages()
    .find((p) => p.url().includes("/panel.html"));
  if (!panel)
    throw Error(
      "The actual native side panel did not open from the guided example",
    );
  panel.on("pageerror", (error) => errors.push(error.message));
  await expect
    .poll(
      async () =>
        (
          await panel.evaluate(
            async () => (await chrome.storage.session.get("reading")).reading,
          )
        )?.artifact?.regions?.length ?? 0,
    )
    .toBeGreaterThan(0);
  await expect(panel).toHaveTitle("ToMpathy - What's on the creator's mind?");
  await expect(panel.locator(".reader-content > .region")).toHaveCount(3);
  await expect(panel.locator(".app-header, .app-footer")).toHaveCount(0);
  await expect(panel.getByTestId("values")).toContainText("Care for others");
  await expect(
    panel.getByRole("tab", { name: "current work only", exact: true }),
  ).toHaveAttribute("aria-selected", "true");
  await panel.getByRole("tab", { name: "creator", exact: true }).click();
  await expect(panel.locator(".creator-brain")).toHaveJSProperty(
    "naturalWidth",
    128,
  );
  expect(
    await panel
      .locator(".heading-help")
      .evaluateAll((els) => els.map((el) => getComputedStyle(el).fontSize)),
  ).toEqual(["11px", "11px", "11px"]);
  if (
    await panel
      .getByRole("button", { name: "Dismiss interaction guide" })
      .count()
  )
    await panel
      .getByRole("button", { name: "Dismiss interaction guide" })
      .click();
  await expect
    .poll(() => source.evaluate(() => innerWidth))
    .toBeLessThan(widthBefore);
  const widthAfter = await source.evaluate(() => innerWidth);
  const values = await panel.getByTestId("values").innerHTML();
  // Aim at text, not a paragraph's empty rectangular padding.
  const point = await source.locator('[data-passage="p4"]').evaluate((el) => {
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    let text;
    while ((text = walker.nextNode()))
      if (
        !text.parentElement.closest("[data-tompathy-ui],[aria-hidden]") &&
        text.textContent.trim().length > 20
      )
        break;
    const range = document.createRange();
    range.setStart(text, 4);
    range.setEnd(text, 12);
    const r = range.getBoundingClientRect();
    return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
  });
  await source.mouse.move(point.x, point.y);
  await expect(panel.locator('.spool[data-rank="0"]')).toHaveAttribute(
    "data-selected",
    "sentence-3-1",
  );
  await source.mouse.move(1, 1);
  await expect(panel.locator('.spool[data-rank="0"]')).toHaveAttribute(
    "data-selected",
    "sentence-3-1",
  );
  await expect(panel.locator(".process-lock")).toHaveCount(0);
  expect(await panel.getByTestId("values").innerHTML()).toBe(values);
  await source.mouse.click(point.x, point.y);
  await expect(
    panel.getByRole("button", { name: "Unlock selection" }),
  ).toBeVisible();
  await expect(source.locator('[aria-label="Unlock selection"]')).toBeVisible();
  // Native panel → document reminder, with no unlock or selection change.
  const blockedNodes = await panel
    .locator('[data-node^="sentence-1-"] circle')
    .evaluateAll((es) =>
      es.map((el) => {
        const b = el.getBoundingClientRect();
        return { x: b.x + b.width / 2, y: b.y + b.height / 2 };
      }),
    );
  for (let i = 0; i < 12; i++) {
    const target = blockedNodes[i % blockedNodes.length];
    await panel.mouse.move(target.x, target.y);
    await panel.waitForTimeout(45);
  }
  await expect(panel.locator('[data-lock-reminder="active"]')).toHaveCount(1);
  await expect(source.locator('[data-lock-reminder="active"]')).toHaveCount(1);
  await source.getByRole("button", { name: "Unlock selection" }).click();
  await expect(panel.locator('[data-lock-reminder="active"]')).toHaveCount(0);
  await panel
    .locator('[data-root="purpose"][data-node="sentence-3-1"] circle')
    .click();
  // Document → native panel reminder, using six transitions, each worth two points.
  await source.locator('[data-passage="p3"]').scrollIntoViewIfNeeded();
  const blockedPoints = await source
    .locator('[data-passage="p3"]')
    .evaluate((el) => {
      return [
        ...el.querySelectorAll('[data-tompathy-reading][tabindex="0"]'),
      ].map((span) => {
        const text = document
          .createTreeWalker(span, NodeFilter.SHOW_TEXT)
          .nextNode();
        const range = document.createRange();
        range.setStart(text, 4);
        range.setEnd(text, 8);
        const r = range.getBoundingClientRect();
        return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
      });
    });
  for (let i = 0; i < 6; i++) {
    const p = blockedPoints[i % blockedPoints.length];
    await source.mouse.move(p.x, p.y);
    await source.waitForTimeout(75);
  }
  await expect(source.locator('[data-lock-reminder="active"]')).toHaveCount(1);
  await expect(panel.locator('[data-lock-reminder="active"]')).toHaveCount(1);
  await expect(panel.locator('.spool[data-rank="0"]')).toHaveAttribute(
    "data-selected",
    "sentence-3-1",
  );
  receipt.checks.push(
    "Blocked focus reminders pulse both native locks in either direction; unlock cancels them",
  );
  await expect(panel.locator('[data-lock-reminder="active"]')).toHaveCount(0);
  await source.screenshot({
    path: "evidence/review-locked-source.png",
    scale: "css",
  });
  await source.locator('[data-passage="p2"]').hover();
  await expect(panel.locator('.spool[data-rank="0"]')).toHaveAttribute(
    "data-selected",
    "sentence-3-1",
  );
  await panel.waitForTimeout(1000);
  await panel.screenshot({
    path: "evidence/review-odometer.png",
    scale: "css",
  });
  await expect(panel.locator(".pyramid")).toBeVisible();
  const pyramidBounds = await panel.locator(".pyramid").boundingBox();
  const reelBounds = await panel.getByTestId("odometer").boundingBox();
  expect(reelBounds.y).toBeGreaterThan(pyramidBounds.y + pyramidBounds.height);
  expect(reelBounds.height).toBeLessThan(50);
  const reel = panel.locator('.spool[data-rank="0"]');
  await reel.hover();
  await panel.mouse.wheel(0, 100);
  await expect(reel).toHaveAttribute("data-selected", "sentence-3-2");
  await expect
    .poll(() =>
      source.evaluate(() =>
        [...CSS.highlights.get("tompathy-active")]
          .map((r) => r.toString())
          .join(" "),
      ),
    )
    .toContain("A tester pointed out");
  await panel.locator('[data-node="paragraph-3"] circle').first().click();
  await expect(reel).toHaveClass(/ambiguous/);
  await expect
    .poll(() =>
      source.evaluate(() => CSS.highlights.get("tompathy-active").size),
    )
    .toBe(4);
  await source.getByRole("button", { name: "Unlock selection" }).click();
  await expect(panel.getByTestId("goals")).toHaveText("hover");
  await expect(
    panel.getByRole("button", { name: "Unlock selection" }),
  ).toHaveCount(0);
  await panel.locator('[data-node="sentence-3-2"] circle').first().click();
  await expect(panel.locator('[data-dominant="true"]')).toHaveText(
    "Learning together",
  );
  await expect(panel.locator('.spool[data-rank="2"]')).toHaveAttribute(
    "data-candidates",
    "story,practical-care",
  );
  await expect(panel.locator('.spool[data-level="0"]')).toHaveAttribute(
    "data-candidates",
    "purpose,end",
  );
  await panel.getByRole("button", { name: "Unlock selection" }).click();
  await expect(
    source.getByRole("button", { name: "Unlock selection" }),
  ).toBeHidden();
  await expect(panel.getByTestId("goals")).toHaveText("hover");
  const lowerBranch = panel.locator('[data-node="practical-care"] circle');
  await lowerBranch.click();
  await expect(panel.locator('[data-node="purpose"].ancestor')).toHaveCount(0);
  await expect(panel.locator('.spool[data-level="0"] .spool-window')).toHaveCSS(
    "height",
    "2px",
  );
  await source.locator("h1").dblclick();
  await expect(
    panel.getByRole("button", { name: "Unlock selection" }),
  ).toHaveCount(0);
  await lowerBranch.click();
  await panel.locator("#process-title").dblclick();
  await expect(
    source.getByRole("button", { name: "Unlock selection" }),
  ).toBeHidden();
  await expect(
    panel.getByRole("button", { name: /^Order uncertain/ }),
  ).toHaveCount(2);
  receipt.checks.push(
    "Each node has one visual home while selection retains every supplied parent; shorter paths close the final reel; double-clicking either page or panel releases both locks; two supplied order-uncertainty marks render",
  );
  await panel.locator("#values-title button").hover();
  await expect(panel.getByRole("tooltip")).toContainText("homeostatic");
  const theoryBounds = await panel.getByRole("tooltip").boundingBox();
  expect(theoryBounds.height).toBeLessThan(
    await panel.evaluate(() => innerHeight - 20),
  );
  await panel.locator("#process-title button").hover();
  await panel.locator('[data-node="paragraph-3"] circle').first().hover();
  expect(
    await panel
      .locator(".pyramid-node.descendant")
      .evaluateAll(
        (es) => new Set(es.map((e) => e.getAttribute("data-node"))).size,
      ),
  ).toBe(5);
  await expect(source.locator('[data-passage="p4"]')).toHaveAttribute(
    "data-tompathy-related",
    "",
  );
  await panel.waitForTimeout(1000);
  await panel.screenshot({ path: "evidence/review-branch.png", scale: "css" });
  await panel.locator('[data-node="purpose"] circle').hover();
  await expect
    .poll(async () =>
      Number(await panel.getByTestId("goals").getAttribute("data-total")),
    )
    .toBeGreaterThan(12);
  await expect
    .poll(() => panel.locator("[data-goal]:not([aria-hidden])").count())
    .toBeGreaterThan(0);
  const visibleFocuses = await panel
    .locator("[data-goal]:not([aria-hidden])")
    .count();
  await panel.mouse.move(1, 1);
  await expect(panel.locator("[data-goal]:not([aria-hidden])")).toHaveCount(
    visibleFocuses,
  );
  await expect
    .poll(() =>
      panel
        .getByTestId("goals")
        .evaluate(
          (el) =>
            el
              .getAnimations({ subtree: true })
              .filter((a) => a.playState === "running").length,
        ),
    )
    .toBe(0)
    .catch(async (error) => {
      console.error(
        await panel.getByTestId("goals").evaluate((el) => ({
          visibility: document.visibilityState,
          goals: el.textContent,
          animations: el
            .getAnimations({ subtree: true })
            .filter((a) => a.playState === "running")
            .map((a) => ({
              target: a.effect.target?.outerHTML?.slice(0, 300),
              time: a.currentTime,
              start: a.startTime,
              timing: a.effect.getComputedTiming(),
              property: a.transitionProperty,
              name: a.animationName,
            })),
        })),
      );
      throw error;
    });
  const cloudBounds = await panel.getByTestId("goals").evaluate((el) => {
    const box = el.getBoundingClientRect();
    return [
      ...el.querySelectorAll("[data-goal]:not([aria-hidden]) button"),
    ].every((word) => {
      const r = word.getBoundingClientRect();
      return (
        r.left >= box.left &&
        r.right <= box.right &&
        r.top >= box.top &&
        r.bottom <= box.bottom
      );
    });
  });
  expect(cloudBounds).toBe(true);
  await panel.screenshot({
    path: "evidence/attention-native-combined.png",
    scale: "css",
  });
  await panel
    .getByRole("button", { name: "Order uncertain", exact: true })
    .first()
    .focus();
  await expect(panel.locator('[data-node="paragraph-1"].chosen')).toHaveCount(
    1,
  );
  await expect(panel.locator('[data-rank="0"].descendant')).toHaveCount(3);
  receipt.checks.push(
    "Soft hover holds across gaps without a lock; broader nodes combine all supplied attention items; uncertainty marks inspect their common parent and subordinate choices",
  );
  // The real native panel and the source page must agree on navigation state.
  await source.keyboard.press("Escape");
  const lateSentence = source
    .locator('[data-passage="p9"] [data-tompathy-reading]')
    .first();
  await lateSentence.focus();
  await source.keyboard.press("Enter");
  const findButton = panel.getByRole("button", {
    name: "Find highlighted text in page",
  });
  await expect(findButton).toBeVisible();
  await source.evaluate(() => window.scrollTo(0, 0));
  await findButton.click();
  await expect(findButton).toBeHidden();
  await expect
    .poll(() => source.evaluate(() => CSS.highlights.has("tompathy-found")), {
      intervals: [100],
      timeout: 10000,
    })
    .toBe(true);
  expect(await source.evaluate(() => scrollY)).toBeGreaterThan(100);
  await source.evaluate(() => window.scrollBy(0, -80));
  await expect(findButton).toBeVisible();
  const graph = panel.locator(".pyramid > svg");
  const anchor = await panel
    .locator('[data-node="sentence-3-1"][data-root="purpose"]')
    .evaluate((el) => {
      const svg = el.closest("svg"),
        p = new DOMPoint(
          Number(el.getAttribute("data-label-x")),
          Number(el.getAttribute("data-label-y")),
        ).matrixTransform(svg.getScreenCTM());
      return { x: p.x, y: p.y };
    });
  await panel.mouse.move(anchor.x, anchor.y);
  const threshold = Number(await graph.getAttribute("data-label-zoom"));
  await panel.mouse.wheel(0, -Math.log2(threshold * 1.3) / 0.002);
  await expect(graph).toHaveAttribute("data-label-reveal", "1.000");
  await expect(
    panel.getByRole("button", { name: "Fit whole hierarchy" }),
  ).toBeVisible();
  expect(await panel.locator(".hierarchy-label").count()).toBe(
    await panel.locator(".pyramid-node").count(),
  );
  await expect(
    panel.locator(
      '[data-node="sentence-3-1"][data-root="purpose"] .hierarchy-label',
    ),
  ).toBeInViewport();
  await panel.screenshot({
    path: "evidence/navigation-native-zoom.png",
    scale: "css",
  });
  const rectangle = await graph.boundingBox();
  const transformBefore = await graph
    .locator(":scope > g")
    .getAttribute("transform");
  await panel.mouse.move(
    rectangle.x + rectangle.width / 2,
    rectangle.y + rectangle.height / 2,
  );
  await panel.mouse.down();
  await panel.mouse.move(
    rectangle.x + rectangle.width * 0.7,
    rectangle.y + rectangle.height * 0.6,
    { steps: 8 },
  );
  await panel.mouse.up();
  await expect(graph.locator(":scope > g")).not.toHaveAttribute(
    "transform",
    transformBefore,
  );
  await expect(
    panel.locator('.spool[data-selected="sentence-8-1"]'),
  ).toHaveCount(1);
  await panel.getByRole("button", { name: "Fit whole hierarchy" }).click();
  await expect(graph).toHaveAttribute("data-zoom", "1.000");
  await panel.mouse.move(1, 1);
  await panel.screenshot({
    path: "evidence/navigation-native-fit.png",
    scale: "css",
  });
  await graph.click({
    position: { x: rectangle.width - 3, y: rectangle.height - 3 },
  });
  await expect(panel.locator(".process-lock")).toHaveCount(0);
  await source
    .locator('[data-passage="p5"] [data-tompathy-reading]')
    .first()
    .focus();
  await expect(source.locator(".tompathy-reading-help")).toBeVisible();
  const sourceCDP = await source.context().newCDPSession(source);
  // Focusing can scroll the sentence into view and briefly dismiss the card.
  // Check the restored, exposed content rather than sampling a stale AX tree.
  const evidenceText = async () =>
    (await sourceCDP.send("Accessibility.getFullAXTree")).nodes
      .filter((n) => !n.ignored)
      .map((n) => n.name?.value ?? "")
      .join(" ")
      .replace(/\s+/g, " ");
  await expect.poll(evidenceText).toContain("Less · confidence · More");
  await expect
    .poll(evidenceText)
    .toContain("Less · creator involvement · More");
  expect(await evidenceText()).not.toContain("Ink represents involvement");
  await sourceCDP.detach();
  await source.screenshot({
    path: "evidence/navigation-native-evidence.png",
    scale: "css",
  });
  await source.keyboard.press("Escape");
  await source.locator('[data-ghost-kind="ghost"]').focus();
  await expect(source.locator(".tompathy-reading-help")).toBeVisible();
  const ghostInspector = await source.context().newCDPSession(source);
  await expect
    .poll(async () => {
      const ghostAX = await ghostInspector.send("Accessibility.getFullAXTree");
      return ghostAX.nodes
        .filter((n) => !n.ignored)
        .map((n) => n.name?.value ?? "")
        .join(" ");
    })
    .toContain("Estimated generation prompt");
  expect(await source.locator("article").textContent()).not.toContain(
    "Generation prompt:",
  );
  // Focus can scroll the article; capture the restored, settled card.
  await source.waitForTimeout(250);
  await expect(source.locator(".tompathy-reading-help")).toBeVisible();
  await source.screenshot({
    path: "evidence/ghost-tooltip-native.png",
    scale: "css",
  });
  await ghostInspector.detach();
  await source.keyboard.press("Escape");
  await expect(panel.getByLabel("Creator selection")).toBeVisible();
  await expect(panel.locator(".creator-brain")).toBeVisible();
  await expect(
    panel
      .locator(".values-bottom")
      .getByRole("button", { name: "Reader menu" }),
  ).toBeVisible();
  receipt.checks.push(
    "Creator selection is above attention, Options is in Core values, and the estimated ghost prompt appears only inside the private evidence tooltip",
  );
  receipt.checks.push(
    "All thirty sentences represented; native zoom, readable labels, drag without changing the lock, fit, blank-space unlock, exact-sentence find, hidden Find acknowledgement and scroll rearming; private visual evidence card exposed accessibly",
  );
  await panel.keyboard.press("Escape");
  await panel.locator('[data-node="sentence-3-1"] circle').click();
  await panel.keyboard.press("ArrowDown");
  await expect(panel.locator(".pyramid-node.chosen")).toHaveAttribute(
    "data-node",
    "sentence-3-2",
  );
  await expect
    .poll(() =>
      source.evaluate(() =>
        [...CSS.highlights.get("tompathy-active")]
          .map((r) => r.toString())
          .join(" "),
      ),
    )
    .toContain("A tester pointed out");
  await panel.keyboard.press("ArrowRight");
  await expect(panel.locator(".pyramid-node.chosen")).toHaveAttribute(
    "data-node",
    "paragraph-3",
  );
  receipt.checks.push(
    "Arrow keys navigate cells and hierarchy levels in the native side panel and update the actual source highlight",
  );
  await expect(panel.locator(".spool.ambiguous").first()).toBeVisible();
  await expect(panel.locator(".process-find")).toBeHidden();
  await expect
    .poll(() => source.evaluate(() => CSS.highlights.has("tompathy-found")), {
      intervals: [100],
      timeout: 10000,
    })
    .toBe(true);
  const groupCenterError = await source.evaluate(() => {
    const rs = [...CSS.highlights.get("tompathy-active")].flatMap((r) => [
      ...r.getClientRects(),
    ]);
    return Math.abs(
      (Math.min(...rs.map((r) => r.top)) +
        Math.max(...rs.map((r) => r.bottom))) /
        2 -
        innerHeight / 2,
    );
  });
  expect(groupCenterError).toBeLessThan(3);
  receipt.checks.push(
    "Ambiguous branch Find centers the full highlighted text group in the native source page",
  );
  await panel.getByRole("tab", { name: "global", exact: true }).click();
  await expect(panel.locator(".core-value-row")).toHaveCount(8);
  await expect(panel.getByRole("tabpanel")).toContainText("Personal agency");
  await panel
    .getByRole("button", { name: "Personal agency", exact: true })
    .hover();
  await expect(
    panel.getByRole("tooltip").locator(".value-confidence-axis"),
  ).toContainText("88%");
  await expect(
    panel.getByRole("tooltip").locator(".preference-observations li"),
  ).toHaveCount(3);
  await panel.waitForTimeout(250);
  await panel.screenshot({
    path: "evidence/review-global-values.png",
    scale: "css",
  });
  await panel.getByRole("tab", { name: "creator", exact: true }).click();
  await expect(panel.locator(".core-value-row")).toHaveCount(9);
  await panel.getByRole("button", { name: "Open search preview" }).click();
  await panel
    .getByRole("textbox", { name: "Search preview" })
    .fill("curiosity");
  await panel.getByRole("textbox", { name: "Search preview" }).press("Enter");
  await expect(
    panel.getByRole("status").filter({ hasText: "No query was sent" }),
  ).toBeVisible();
  await panel.getByRole("button", { name: "Close search" }).click();
  receipt.checks.push(
    "Nine creator values with a partial-row scroll cue, eight higher-confidence Global demo values and expandable typing-only search work in the native panel",
  );
  await panel
    .getByRole("button", { name: "Care for others", exact: true })
    .hover();
  await expect(panel.getByRole("tooltip")).toContainText("persistent latch");
  await panel.getByRole("button", { name: "Restraint", exact: true }).hover();
  await panel.getByRole("button", { name: "Curiosity", exact: true }).hover();
  await expect(panel.getByRole("tooltip")).toContainText("Curiosity");
  await expect(panel.getByRole("tooltip")).not.toContainText("Restraint");
  await panel
    .getByRole("button", { name: "Care for others", exact: true })
    .hover();
  await panel.waitForTimeout(300);
  await panel.screenshot({
    path: "evidence/review-value-detail.png",
    scale: "css",
  });
  await panel.locator("#process-title button").hover();
  await expect(panel.getByRole("tooltip")).toContainText(
    "lossy, compressed record",
  );
  await expect(panel.getByRole("tooltip").getByRole("img")).toBeVisible();
  const helpBounds = await panel.getByRole("tooltip").boundingBox();
  expect(helpBounds.y).toBeGreaterThanOrEqual(0);
  expect(helpBounds.y + helpBounds.height).toBeLessThanOrEqual(
    await panel.evaluate(() => innerHeight),
  );
  await panel.waitForTimeout(250);
  await panel.screenshot({
    path: "evidence/review-expertise-help.png",
    scale: "css",
  });
  await panel.locator(".value-tabs").hover();
  await panel.waitForTimeout(1000);
  await panel.screenshot({
    path: "evidence/review-chrome-panel.png",
    scale: "css",
  });
  receipt.nativePanel = {
    sourceWidthBefore: widthBefore,
    sourceWidthAfter: widthAfter,
    panelWidth: await panel.evaluate(() => innerWidth),
  };
  receipt.checks.push(
    "Guide opens a native panel beside its bundled source without a server",
    "Independent attention, four hierarchy peaks, bidirectional ambiguity, page/panel green unlock controls, sentence hover, single-click locks for sentences and branches, wheel-driven source selection, compact reels below a persistent hierarchy, Escape, fixed values and provenance",
  );
  receipt.localAI = await panel.evaluate(async () => {
    const inspect = async (name) => {
      const api = globalThis[name];
      if (!api) return "API absent";
      try {
        return await api.availability({
          expectedInputs: [{ type: "text", languages: ["en"] }],
          expectedOutputs: [{ type: "text", languages: ["en"] }],
        });
      } catch (e) {
        return `Unavailable: ${e.message}`;
      }
    };
    return {
      prompt: await inspect("LanguageModel"),
      summarizer: await inspect("Summarizer"),
      downloadRequested: false,
    };
  });
  await panel.getByRole("button", { name: "Reader menu", exact: true }).click();
  await expect(panel.getByRole("dialog")).toHaveAccessibleName("Options");
  await panel.screenshot({ path: "evidence/review-options.png", scale: "css" });
  const [savedDownload] = await Promise.all([
    panel.waitForEvent("download"),
    panel.getByRole("button", { name: "Export", exact: true }).click(),
  ]);
  await panel
    .getByLabel("Import reading")
    .setInputFiles(await savedDownload.path());
  await expect
    .poll(() =>
      panel
        .context()
        .pages()
        .some((p) => p.url().includes("/snapshot.html?")),
    )
    .toBe(true);
  const restored = panel
    .context()
    .pages()
    .find((p) => p.url().includes("/snapshot.html?"));
  await restored
    .getByRole("button", { name: "Open ToMpathy", exact: true })
    .waitFor();
  await expect(panel.getByTestId("values")).toContainText("Care for others");
  await expect(
    panel.getByRole("tab", { name: "creator", exact: true }),
  ).toHaveAttribute("aria-selected", "true");
  await panel.getByRole("tab", { name: "creator", exact: true }).click();
  await restored
    .locator('[data-snapshot-region="p4"]')
    .click({ position: { x: 30, y: 18 } });
  await expect(panel.locator(".process-lock")).toBeVisible();
  await panel.locator(".process-lock").click();
  await expect(
    restored.locator('[aria-label="Unlock selection"]'),
  ).not.toBeVisible();
  await restored.screenshot({
    path: "evidence/review-saved-page.png",
    scale: "css",
  });
  receipt.checks.push(
    "Options export saves a portable readable page with analysis; import opens it in Chrome and restores two-way sentence locking",
  );
  if (!panel.url().includes("qa"))
    await panel.goto(
      panel.url() + (panel.url().includes("?") ? "&" : "?") + "qa",
    );
  await panel
    .getByRole("button", { name: "Development tools", exact: true })
    .click();
  await panel.getByRole("button", { name: "Context", exact: true }).click();
  await panel.getByRole("button", { name: "Preview example revision" }).click();
  await panel.getByRole("button", { name: "Accept this revision" }).click();
  await expect(panel.getByTestId("values")).toContainText("Practical care");
  await expect
    .poll(() =>
      panel.evaluate(async () => {
        const reading = (await chrome.storage.session.get("reading")).reading;
        return (
          await chrome.storage.session.get(`snapshot:${reading.savedPageId}`)
        )[`snapshot:${reading.savedPageId}`]?.packet?.revision;
      }),
    )
    .toBe(2);
  await source.bringToFront();
  await expect(panel.getByTestId("values")).toContainText("Care for others");
  await expect(
    panel.getByRole("tab", { name: "current work only", exact: true }),
  ).toHaveAttribute("aria-selected", "true");
  await panel.getByRole("tab", { name: "creator", exact: true }).click();
  await restored.bringToFront();
  await expect(panel.getByTestId("values")).toContainText("Practical care");
  receipt.checks.push(
    "An imported reading retains its new revision after switching away and returning",
  );
  await source.bringToFront();
  await expect(panel.getByTestId("values")).toContainText("Care for others");
  await expect(
    panel.getByRole("tab", { name: "creator", exact: true }),
  ).toHaveAttribute("aria-selected", "true");
  await panel.getByRole("tab", { name: "creator", exact: true }).click();
  if (!panel.url().includes("qa"))
    await panel.goto(
      panel.url() + (panel.url().includes("?") ? "&" : "?") + "qa",
    );
  await panel
    .getByRole("button", { name: "Development tools", exact: true })
    .click();
  await panel.getByRole("button", { name: "Context", exact: true }).click();
  await panel.getByRole("button", { name: "Preview example revision" }).click();
  await panel.getByRole("button", { name: "Accept this revision" }).click();
  await expect(panel.getByTestId("values")).toContainText("Practical care");
  await expect
    .poll(() =>
      panel.evaluate(
        async () =>
          (await chrome.storage.session.get("reading")).reading.packet.revision,
      ),
    )
    .toBe(2);
  const resumed = await openReview({ profile });
  connections.push(resumed.browser);
  expect(resumed.receipt.action).toBe("Resumed existing installation");
  expect(resumed.receipt.readingLeftOpen).toBe(true);
  const stored = await panel.evaluate(() =>
    chrome.storage.session.get("reading"),
  );
  expect(stored.reading.packet.revision).toBe(2);
  receipt.checks.push(
    "Re-running the unchanged launcher preserves the accepted reading",
  );
  expect(errors).toEqual([]);
  // The toolbar action must grant activeTab on a normal HTTP page using the
  // delivered manifest. No test-only host permissions are added to this build.
  await panel.close();
  const fixture = await readFile("public/testbed.html");
  fixtureServer = createServer((_request, response) => {
    response.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    response.end(fixture);
  });
  await new Promise((resolve) => fixtureServer.listen(0, "127.0.0.1", resolve));
  const fixtureUrl = `http://127.0.0.1:${fixtureServer.address().port}/testbed.html`;
  const ordinary = await context.newPage();
  await ordinary.goto(fixtureUrl);
  await ordinary.bringToFront();
  const targets = await resumed.cdp.send("Target.getTargets", {
    filter: [{ type: "tab" }],
  });
  const tab = targets.targetInfos.find((target) => target.url === fixtureUrl);
  if (!tab)
    throw Error("The ordinary test page did not expose a Chrome tab target");
  await resumed.cdp.send("Extensions.triggerAction", {
    id: resumed.receipt.extensionId,
    targetId: tab.targetId,
  });
  const actionConnection = await openReview({ profile, showGuide: false });
  connections.push(actionConnection.browser);
  panel = actionConnection.browser
    .contexts()[0]
    .pages()
    .find((p) => p.url().includes("/panel.html"));
  if (!panel)
    throw Error(
      "The extension action did not open the native panel on an ordinary page",
    );
  await expect(panel.locator('.sr-only[role="status"]')).toContainText(
    "Awaiting analysis",
  );
  await expect
    .poll(() =>
      panel.evaluate(
        async () =>
          (await chrome.storage.session.get("reading")).reading.artifact.regions
            .length,
      ),
    )
    .toBe(
      JSON.parse(await readFile("public/testbed-result.json", "utf8")).artifact
        .regions.length,
    );
  receipt.checks.push(
    "Chrome extension action grants activeTab and captures a normal HTTP article with the delivered manifest",
  );
  if (process.argv.includes("--public")) {
    const publicUrl = "https://simonwillison.net/2022/May/4/datasette-lite/";
    await panel.close();
    await ordinary.goto(publicUrl);
    await ordinary.bringToFront();
    const publicTargets = await resumed.cdp.send("Target.getTargets", {
      filter: [{ type: "tab" }],
    });
    const publicTab = publicTargets.targetInfos.find(
      (target) => target.url === publicUrl,
    );
    if (!publicTab)
      throw Error("The selected public article did not expose a tab target");
    await resumed.cdp.send("Extensions.triggerAction", {
      id: resumed.receipt.extensionId,
      targetId: publicTab.targetId,
    });
    const publicConnection = await openReview({ profile, showGuide: false });
    connections.push(publicConnection.browser);
    panel = publicConnection.browser
      .contexts()[0]
      .pages()
      .find((page) => page.url().includes("/panel.html"));
    if (!panel) throw Error("The panel did not open on the public article");
    await expect(panel.locator('.sr-only[role="status"]')).toContainText(
      "Awaiting analysis",
    );
    const captured = await panel.evaluate(
      async () =>
        (await chrome.storage.session.get("reading")).reading.artifact,
    );
    expect(captured.authors).toContainEqual({
      label: "Simon Willison",
      basis: "page-metadata",
    });
    expect(captured.regions.length).toBeGreaterThan(50);
    receipt.publicArticle = {
      url: publicUrl,
      author: "Simon Willison",
      passages: captured.regions.length,
      inferenceRequested: false,
    };
    await panel.waitForTimeout(1000);
    await panel.screenshot({
      path: "evidence/review-public-panel.png",
      scale: "css",
    });
    receipt.checks.push(
      "Real Simon Willison article captures through the extension action and correctly awaits backend analysis",
    );
  }
  await panel.evaluate(() =>
    chrome.storage.local.set({ reviewRestartProbe: "retained" }),
  );
  // Chrome intentionally removes CDP-installed extensions on restart. The
  // supported launcher restores the same ID; do not patch browser preferences.
  await resumed.cdp.send("Browser.close");
  await expect
    .poll(() => originalProcess.exitCode, { timeout: 15000 })
    .not.toBeNull();
  current = await openReview({ profile });
  connections.push(current.browser);
  expect(current.receipt.reusedBrowser).toBe(false);
  expect(current.receipt.action).toBe("Restored installation");
  expect(current.receipt.enabled).toBe(true);
  const restoredGuide = current.browser
    .contexts()[0]
    .pages()
    .find((p) => p.url() === current.receipt.reviewUrl);
  expect(
    await restoredGuide.evaluate(
      async () =>
        (await chrome.storage.local.get("reviewRestartProbe"))
          .reviewRestartProbe,
    ),
  ).toBe("retained");
  expect(current.receipt.extensionId).toBe(resumed.receipt.extensionId);
  receipt.checks.push(
    "Launcher restores the same extension ID after a full Chrome restart; local preferences survive",
  );
  receipt.extensionId = current.receipt.extensionId;
  receipt.errors = errors;
  await writeFile(
    "evidence/review-validation.json",
    JSON.stringify(receipt, null, 2),
  );
  console.log(JSON.stringify(receipt, null, 2));
} finally {
  if (current) await current.cdp.send("Browser.close").catch(() => {});
  for (const browser of connections) await browser.close().catch(() => {});
  fixtureServer?.close();
}
