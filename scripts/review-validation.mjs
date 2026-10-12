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
    `Installed · 0.2 development 1 · build ${receipt.build}`,
  );
  await expect(
    guide.getByRole("heading", { name: "Your first five-minute review" }),
  ).toBeVisible();
  await guide.screenshot({
    path: "evidence/review-desk.png",
    fullPage: true,
    scale: "css",
  });
  const [source] = await Promise.all([
    context.waitForEvent("page"),
    guide.getByRole("link", { name: "Open the guided example" }).click(),
  ]);
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
  await expect(panel).toHaveTitle("ToMpathy - What's on the author's mind?");
  await expect(panel.locator(".reader-content > .region")).toHaveCount(3);
  await expect(panel.locator(".app-header, .app-footer")).toHaveCount(0);
  await expect(panel.getByTestId("values")).toContainText("Care for others");
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
    const text = Array.from(el.childNodes).find(
      (n) => n.nodeType === Node.TEXT_NODE && n.textContent.trim().length > 20,
    );
    const range = document.createRange();
    range.setStart(text, 4);
    range.setEnd(text, 12);
    const r = range.getBoundingClientRect();
    return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
  });
  await source.mouse.move(point.x, point.y);
  await expect(panel.locator('.spool[data-level="3"]')).toHaveAttribute(
    "data-selected",
    "sentence-3-1",
  );
  expect(await panel.getByTestId("values").innerHTML()).toBe(values);
  await source.mouse.click(point.x, point.y);
  await expect(
    panel.getByRole("button", { name: "Unlock selection" }),
  ).toBeVisible();
  await expect(source.locator('[aria-label="Unlock selection"]')).toBeVisible();
  await source.screenshot({
    path: "evidence/review-locked-source.png",
    scale: "css",
  });
  await source.locator('[data-passage="p2"]').hover();
  await expect(panel.locator('.spool[data-level="3"]')).toHaveAttribute(
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
  const reel = panel.locator('.spool[data-level="3"]');
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
    .toContain("We counted pauses");
  await panel.locator('[data-node="paragraph-3"] circle').first().click();
  await expect(reel).toHaveClass(/ambiguous/);
  await expect
    .poll(() =>
      source.evaluate(() => CSS.highlights.get("tompathy-active").size),
    )
    .toBe(4);
  await source.getByRole("button", { name: "Unlock selection" }).click();
  await expect(panel.getByTestId("goals")).toHaveText("Hover to see");
  await expect(
    panel.getByRole("button", { name: "Unlock selection" }),
  ).toHaveCount(0);
  await panel.locator('[data-node="sentence-3-2"] circle').first().click();
  await expect(panel.locator('[data-dominant="true"]')).toHaveText(
    "Learning from others",
  );
  await expect(panel.locator('.spool[data-level="1"]')).toHaveAttribute(
    "data-selected",
    "story",
  );
  await expect(panel.locator('.spool[data-level="0"]')).toHaveAttribute(
    "data-selected",
    "purpose",
  );
  await panel.getByRole("button", { name: "Unlock selection" }).click();
  await expect(
    source.getByRole("button", { name: "Unlock selection" }),
  ).toBeHidden();
  await expect(panel.getByTestId("goals")).toHaveText("Hover to see");
  const lowerBranch = panel.locator(
    '[data-root="practical-care"][data-node="paragraph-3"] circle',
  );
  await lowerBranch.click();
  await expect(
    panel.locator(
      '[data-root="purpose"].ancestor, [data-root="purpose"].descendant',
    ),
  ).toHaveCount(0);
  await expect(panel.locator('.spool[data-level="0"]')).toHaveCSS(
    "opacity",
    "0.18",
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
    panel.getByRole("img", { name: /^Order uncertain/ }),
  ).toHaveCount(2);
  receipt.checks.push(
    "Direct node selection stays on its visual branch; shorter paths fade the final reel; double-clicking either page or panel releases both locks; two supplied order-uncertainty marks render",
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
  await panel.getByRole("tab", { name: "global", exact: true }).click();
  await expect(panel.getByRole("tabpanel")).toHaveText(
    "Global view · coming later",
  );
  await panel.getByRole("tab", { name: "author", exact: true }).click();
  await expect(panel.locator(".core-value-row")).toHaveCount(8);
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
    "Eight author values, global placeholder and expandable typing-only search work in the native panel",
  );
  await panel
    .getByRole("button", { name: "Care for others", exact: true })
    .hover();
  await expect(panel.getByRole("tooltip")).toContainText("Specific decision");
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
    "Independent attention, two hierarchy peaks, bidirectional ambiguity, page/panel green unlock controls, sentence hover, single-click locks for sentences and branches, wheel-driven source selection, compact reels below a persistent hierarchy, Escape, fixed values and provenance",
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
  if (!panel.url().includes("qa")) await panel.goto(panel.url() + "?qa");
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
  await restored.bringToFront();
  await expect(panel.getByTestId("values")).toContainText("Practical care");
  receipt.checks.push(
    "An imported reading retains its new revision after switching away and returning",
  );
  await source.bringToFront();
  await expect(panel.getByTestId("values")).toContainText("Care for others");
  if (!panel.url().includes("qa")) await panel.goto(panel.url() + "?qa");
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
  await expect(panel.locator(".sr-only")).toContainText("Awaiting analysis");
  await expect
    .poll(() =>
      panel.evaluate(
        async () =>
          (await chrome.storage.session.get("reading")).reading.artifact.regions
            .length,
      ),
    )
    .toBe(6);
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
    await expect(panel.locator(".sr-only")).toContainText("Awaiting analysis");
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
