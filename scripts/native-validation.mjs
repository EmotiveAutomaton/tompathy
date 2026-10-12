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
  .find((p) => p.url().includes("/panel.html"));
if (!panel) throw Error("Native panel target did not open");
await expect(panel.getByTestId("values")).toBeVisible();
await expect(panel.getByTestId("values")).toContainText("Care for others");
const values = await panel.getByTestId("values").innerHTML();
await source.locator('[data-passage="p4"]').hover();
await expect(panel.getByTestId("process")).toContainText("Show the iteration");
expect(await panel.getByTestId("values").innerHTML()).toEqual(values);
await source.locator('[data-passage="p4"]').click();
await source.locator('[data-passage="p2"]').hover();
await expect(panel.locator(".sr-only")).toContainText("Locked p4");
await source.keyboard.press("Escape");
await source.locator('[data-passage="p3"]').hover();
await expect(panel.locator(".sr-only")).toContainText("Following p3");
if (!panel.url().includes("qa")) await panel.goto(panel.url() + "?qa");
if (
  await panel.getByRole("button", { name: "Dismiss interaction guide" }).count()
)
  await panel
    .getByRole("button", { name: "Dismiss interaction guide" })
    .click();
await panel
  .getByRole("button", { name: "Development tools", exact: true })
  .click();
await panel
  .getByRole("button", { name: "All supplied hypotheses", exact: true })
  .click();
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
await panel.getByRole("button", { name: "Unlock selection" }).click();
await panel.locator("#process-title button").hover();
await expect(panel.locator(".pyramid")).toBeVisible();
await panel.screenshot({ path: "evidence/native-panel.png", scale: "css" });
await source.screenshot({ path: "evidence/native-source.png", scale: "css" });
const receipt = {
  browser: context.browser()?.version(),
  extensionId: id,
  nativePanel: true,
  goalHierarchy: true,
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
  .find((p) => p.url().includes("/panel.html"));
if (!panel) throw Error("Panel failed to reopen");
await expect(panel.getByTestId("values")).toBeVisible();
receipt.closeCleanupAndReopen = true;
// Stop only this isolated browser's extension worker, then verify local state survives.
const serviceSession = await context.newCDPSession(source);
await serviceSession.send("ServiceWorker.enable");
await serviceSession.send("ServiceWorker.stopAllWorkers");
await source.keyboard.press("Escape");
await source.locator('[data-passage="p4"]').hover();
await expect(panel.getByTestId("process")).toContainText("Show the iteration");
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
await panel
  .getByRole("button", { name: "Recapture page", exact: true })
  .click();
await expect
  .poll(async () =>
    panel.evaluate(
      async () =>
        (await chrome.storage.session.get("reading")).reading.artifact?.regions
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
if (!panel.url().includes("qa")) await panel.goto(panel.url() + "?qa");
await panel
  .getByRole("button", { name: "Development tools", exact: true })
  .click();
await panel.getByRole("button", { name: "Import result", exact: true }).click();
await panel.locator("input[type=file]").setInputFiles({
  name: "long-example.json",
  mimeType: "application/json",
  buffer: Buffer.from(JSON.stringify(longPacket)),
});
await expect(panel.getByTestId("values")).toContainText("Care for others");
await panel.evaluate(() => {
  globalThis.paintTimes = [];
  new MutationObserver(() =>
    requestAnimationFrame(() =>
      globalThis.paintTimes.push(performance.timeOrigin + performance.now()),
    ),
  ).observe(document.querySelector(".sr-only"), {
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
    p.scrollIntoView({ block: "center" });
    const range = document.createRange();
    const textNode = Array.from(p.childNodes).find(
      (n) => n.nodeType === Node.TEXT_NODE && n.textContent.trim().length > 12,
    );
    range.setStart(textNode, 2);
    range.setEnd(textNode, 10);
    const r = range.getClientRects()[0];
    p.dispatchEvent(
      new PointerEvent("pointermove", {
        bubbles: true,
        clientX: r.left + 12,
        clientY: r.top + r.height / 2,
      }),
    );
    if (!p.hasAttribute("data-tompathy-selected"))
      throw Error("No source selection");
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
receipt.shortcutCapture = await panel.locator(".sr-only").innerText();
await source.bringToFront();
// Returning to the source automatically captures it; no manual menu command.
await expect
  .poll(async () =>
    panel.evaluate(
      async () =>
        (await chrome.storage.session.get("reading")).reading.artifact?.regions
          .length,
    ),
  )
  .toBe(1006);
receipt.tabReturnRecapture = true;
// Accept an evidence revision, then actually close and reopen the native panel.
await source.goto(`chrome-extension://${id}/example.html`);
await source.getByRole("button", { name: "Open Maker Reader" }).click();
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
await panel.close();
await source.getByRole("button", { name: "Open Maker Reader" }).click();
const revisionReopen = await chromium.connectOverCDP("http://127.0.0.1:9334");
panel = revisionReopen
  .contexts()[0]
  .pages()
  .find((p) => p.url().includes("/panel.html"));
if (!panel) throw Error("Panel failed to reopen after accepting a revision");
await expect(panel.getByTestId("values")).toContainText("Practical care");
await expect
  .poll(() =>
    panel.evaluate(
      async () =>
        (await chrome.storage.session.get("reading")).reading.history.length,
    ),
  )
  .toBeGreaterThan(0);
receipt.acceptedRevisionSurvivesReopen = true;
console.log(JSON.stringify(receipt, null, 2));
await writeFile(
  "evidence/native-validation.json",
  JSON.stringify(receipt, null, 2),
);
await remote.close();
await reopened.close();
await revisionReopen.close();
await context.close();
