import { chromium, expect } from "@playwright/test";
import path from "node:path";
import { writeFile, mkdir } from "node:fs/promises";
const ext = path.resolve("dist");
await mkdir("evidence", { recursive: true });
const context = await chromium.launchPersistentContext(
  path.resolve(".local/validation-profile"),
  {
    channel: "chromium",
    headless: false,
    viewport: null,
    args: [
      `--disable-extensions-except=${ext}`,
      `--load-extension=${ext}`,
      "--remote-debugging-port=9334",
      "--window-size=1450,1100",
    ],
  },
);
const sw =
  context.serviceWorkers()[0] ?? (await context.waitForEvent("serviceworker"));
const id = sw.url().split("/")[2];
const source = await context.newPage();
await source.goto(`chrome-extension://${id}/example.html`);
const initialWidth = await source.evaluate(() => innerWidth);
await source.getByRole("button", { name: "Open Maker Reader" }).click();
const remote = await chromium.connectOverCDP("http://127.0.0.1:9334");
let panel = remote
  .contexts()[0]
  .pages()
  .find((p) => p.url().endsWith("/panel.html"));
if (!panel) throw Error("Native panel target did not open");
await expect(panel.locator(".identity-note")).toBeVisible();
const values = await panel.getByTestId("values").innerHTML();
await source.locator('[data-passage="p4"]').hover();
await expect(panel.getByTestId("process")).toContainText("Test & refine");
expect(await panel.getByTestId("values").innerHTML()).toEqual(values);
await source.locator('[data-passage="p4"]').click();
await source.locator('[data-passage="p2"]').hover();
await expect(panel.locator(".passage-strip")).toContainText("Pinned passage 4");
await source.keyboard.press("Escape");
await source.locator('[data-passage="p3"]').hover();
await expect(panel.locator(".passage-strip")).toContainText(
  "Following passage 3",
);
await panel
  .getByRole("button", { name: "Reframe the problem", exact: false })
  .click();
await expect(
  panel.getByRole("region", { name: "Hypothesis evidence" }),
).toBeVisible();
await panel.getByRole("button", { name: "Passage 2", exact: true }).click();
expect(
  await source
    .locator('[data-passage="p2"]')
    .getAttribute("data-tompathy-selected"),
).toBe("");
await panel.locator(".reader-content").evaluate((el) => (el.scrollTop = 0));
await panel
  .getByRole("button", { name: "Expand process into word cloud" })
  .click();
await expect(panel.locator(".process-map.cloud")).toBeVisible();
await panel.getByRole("button", { name: "Collapse to process tree" }).click();
await expect(panel.locator(".process-tree")).toBeVisible();
await panel.screenshot({ path: "evidence/native-panel.png", scale: "css" });
await source.screenshot({ path: "evidence/native-source.png", scale: "css" });
const receipt = {
  browser: context.browser()?.version(),
  extensionId: id,
  nativePanel: true,
  treeCloudSwitch: true,
  initialSourceWidth: initialWidth,
  sourceWidthWithPanel: await source.evaluate(() => innerWidth),
  panelWidth: await panel.evaluate(() => innerWidth),
  linkedHover: true,
  stableValues: true,
  pinRelease: true,
  hypothesisToSource: true,
};
await panel.close();
await expect(source.locator("[data-tompathy-selected]")).toHaveCount(0);
await source.getByRole("button", { name: "Open Maker Reader" }).click();
const reopened = await chromium.connectOverCDP("http://127.0.0.1:9334");
panel = reopened
  .contexts()[0]
  .pages()
  .find((p) => p.url().endsWith("/panel.html"));
if (!panel) throw Error("Panel failed to reopen");
await expect(panel.locator(".identity-note")).toBeVisible();
receipt.closeCleanupAndReopen = true;
// Stop only this isolated browser's extension worker, then verify local state survives.
const serviceSession = await context.newCDPSession(source);
await serviceSession.send("ServiceWorker.enable");
await serviceSession.send("ServiceWorker.stopAllWorkers");
await source.keyboard.press("Escape");
await source.locator('[data-passage="p4"]').hover();
await expect(panel.getByTestId("process")).toContainText("Test & refine");
receipt.workerStopRecovery = true;

// Exercise the real native panel on a longer synthetic text, using an imported fixture.
const longPacket = await panel.evaluate(
  async () => (await chrome.storage.session.get("reading")).reading.packet,
);
await source.evaluate(() => {
  const article = document.querySelector("article");
  for (let i = 0; i < 1000; i++) {
    const p = document.createElement("p");
    p.textContent = `Synthetic long-page passage ${i}: we observed a pause, considered a familiar pattern, and revised one small decision.`;
    article.append(p);
  }
});
await expect(panel.getByText("The source text changed")).toBeVisible();
await panel.getByRole("button", { name: "Reader menu", exact: true }).click();
await panel
  .getByRole("button", { name: "Capture current page", exact: true })
  .click();
await expect
  .poll(async () =>
    panel.evaluate(
      async () =>
        (await chrome.storage.session.get("reading")).reading.artifact.regions
          .length,
    ),
  )
  .toBe(1006);
const capture = await panel.evaluate(
  async () => (await chrome.storage.session.get("reading")).reading.artifact,
);
longPacket.id = "bench-long-fixture";
longPacket.artifact = capture;
longPacket.revision = 2;
for (const h of longPacket.hypotheses) {
  if (h.kind !== "value") {
    const original = h.regions;
    h.regions = capture.regions
      .filter((r, i) => original.includes(`p${(i % 6) + 1}`))
      .map((r) => r.id);
  }
}
await panel.getByRole("button", { name: "Reader menu", exact: true }).click();
await panel.getByRole("button", { name: "Import result", exact: true }).click();
await panel.locator("input[type=file]").setInputFiles({
  name: "long-example.json",
  mimeType: "application/json",
  buffer: Buffer.from(JSON.stringify(longPacket)),
});
await panel.getByRole("button", { name: "Accept this revision" }).click();
await panel.evaluate(() => {
  globalThis.paintTimes = [];
  new MutationObserver(() =>
    requestAnimationFrame(() =>
      globalThis.paintTimes.push(performance.timeOrigin + performance.now()),
    ),
  ).observe(document.querySelector(".passage-strip"), {
    subtree: true,
    childList: true,
    characterData: true,
  });
});
const latencies = [];
for (let i = 0; i < 12; i++) {
  const start = await source.evaluate((i) => {
    const p = document.querySelectorAll("article>p")[i % 5];
    const t = performance.timeOrigin + performance.now();
    p.dispatchEvent(new PointerEvent("pointerover", { bubbles: true }));
    return t;
  }, i);
  await panel.waitForFunction(
    (start) => globalThis.paintTimes.some((t) => t >= start),
    start,
  );
  latencies.push(
    await panel.evaluate(
      (start) => globalThis.paintTimes.find((t) => t >= start) - start,
      start,
    ),
  );
}
const intervals = await panel.evaluate(async () => {
  const times = [];
  let previous = performance.now();
  for (let i = 0; i < 60; i++) {
    await new Promise(requestAnimationFrame);
    const now = performance.now();
    times.push(now - previous);
    previous = now;
  }
  return times;
});
receipt.nativeLongPage = {
  passages: capture.regions.length,
  hoverToPanelAnimationFrameMs: latencies,
  frameIntervalsMs: intervals,
};
const ordinary = await context.newPage();
await ordinary.goto("http://127.0.0.1:5173/fixture.html");
await ordinary.keyboard.press("Alt+Shift+Y");
await ordinary.waitForTimeout(1000);
receipt.shortcutCapture = await panel.locator(".artifact-title").innerText();
await source.bringToFront();
await panel.getByRole("button", { name: "Reader menu", exact: true }).click();
await panel
  .getByRole("button", { name: "Capture current page", exact: true })
  .click();
await expect
  .poll(async () =>
    panel.evaluate(
      async () =>
        (await chrome.storage.session.get("reading")).reading.artifact.regions
          .length,
    ),
  )
  .toBe(1006);
receipt.tabReturnRecapture = true;
console.log(JSON.stringify(receipt, null, 2));
await writeFile(
  "evidence/native-validation.json",
  JSON.stringify(receipt, null, 2),
);
await remote.close();
await reopened.close();
await context.close();
