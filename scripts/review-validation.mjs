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
    `Installed · ${current.receipt.version} · build ${receipt.build}`,
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
    .find((p) => p.url().endsWith("/panel.html"));
  if (!panel)
    throw Error(
      "The actual native side panel did not open from the guided example",
    );
  panel.on("pageerror", (error) => errors.push(error.message));
  await expect(panel).toHaveTitle("ToMpathy - What's on the author's mind?");
  await expect(panel.locator(".reader-content > .region")).toHaveCount(3);
  await expect(panel.locator(".app-header, .app-footer")).toHaveCount(0);
  await expect(panel.getByTestId("values")).toContainText("Care for others");
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
  await expect(
    source.locator('[aria-label="Selection locked; press Escape to unlock"]'),
  ).toBeVisible();
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
  expect(reelBounds.height).toBeLessThan(70);
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
  await panel.locator('[data-node="paragraph-3"]').click();
  await expect(reel).toHaveClass(/ambiguous/);
  await expect
    .poll(() =>
      source.evaluate(() => CSS.highlights.get("tompathy-active").size),
    )
    .toBe(4);
  await source.keyboard.press("Escape");
  await panel.locator(".process-region .section-heading").hover();
  await panel.locator('[data-node="paragraph-3"]').hover();
  await expect(panel.locator(".pyramid-node.descendant")).toHaveCount(5);
  await expect(source.locator('[data-passage="p4"]')).toHaveAttribute(
    "data-tompathy-related",
    "",
  );
  await panel.waitForTimeout(1000);
  await panel.screenshot({ path: "evidence/review-branch.png", scale: "css" });
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
  await panel
    .locator(".values-region .section-heading")
    .hover({ position: { x: 260, y: 8 } });
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
    "Sentence hover, single-click locks for sentences and branches, wheel-driven source selection, compact reels below a persistent hierarchy, Escape, fixed values and provenance",
  );
  await panel.getByRole("button", { name: "Reader menu", exact: true }).click();
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
    .find((p) => p.url().endsWith("/panel.html"));
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
      .find((page) => page.url().endsWith("/panel.html"));
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
