// Verify the owner's cached-demo path on the real essay. --prepare runs the
// engine first, using the previously prepared exact reader scores.
import { expect } from "@playwright/test";
import { mkdir, mkdtemp, writeFile } from "node:fs/promises";
import path from "node:path";
import { startPractice } from "./practice-session.mjs";
import { openReview } from "./chrome-review.mjs";

await mkdir("evidence", { recursive: true });
const receipt = { checkedAt: new Date().toISOString(), scope: "Real cached full essay in the native panel; no scientific admission" };
const clef = process.argv.includes("--clef");
const prefix = clef ? "preview-clef" : "preview-curator";
receipt.clef = clef;
const connections = [];
let session, panel;
try {
  const profile = await mkdtemp(path.resolve(".local/preview-cache-check-"));
  session = await startPractice({ profile, clef, preparationBudget: process.argv.includes("--prepare") ? 600 : 165 });
  connections.push(session.review.browser);
  const context = session.review.browser.contexts()[0];
  context.on("request", request => {
    if (request.url().endsWith("/v1/analyze") && request.method() === "POST")
      void writeFile(".local/preview-cache-ui-request.json", request.postData() ?? "null");
  });
  context.setDefaultTimeout(15000);
  const settings = await context.newPage();
  await settings.goto("chrome://extensions/");
  await settings.evaluate(async id => {
    for (const host of ["http://127.0.0.1/*", "https://abrahamhaskins.org/*"])
      await chrome.developerPrivate.addHostPermission(id, host);
  }, session.review.receipt.extensionId);
  await settings.close();
  await session.page.locator("#connect").click();
  await expect(session.page.locator("#connection")).toContainText("Connected to engine");
  const source = await context.newPage();
  await source.goto("https://abrahamhaskins.org/art/", { waitUntil: "domcontentloaded", timeout: 45000 });
  await source.bringToFront();
  const targets = await session.review.cdp.send("Target.getTargets", { filter: [{ type: "tab" }] });
  await session.review.cdp.send("Extensions.triggerAction", { id: session.review.receipt.extensionId, targetId: targets.targetInfos.find(t => t.url === source.url()).targetId });
  const attached = await openReview({ profile, showGuide: false });
  connections.push(attached.browser);
  panel = attached.browser.contexts()[0].pages().find(p => p.url().includes("/panel.html"));
  if (!panel) throw Error("Native panel did not open");
  const reading = () => panel.evaluate(async () => (await chrome.storage.session.get("reading")).reading);
  await expect.poll(async () => (await reading())?.artifact?.source, { timeout: 20000 }).toBe("https://abrahamhaskins.org/art/");
  expect((await reading()).packet?.provider.id ?? "").not.toMatch(/tompathy-(art|website)-demo/);
  expect((await reading()).artifact.regions.some(r => r.anchor.exact === "Loading equation…")).toBe(false);
  await writeFile(".local/preview-cache-session.json", JSON.stringify(await reading()));
  if (process.argv.includes("--prepare")) {
    const setup = await session.page.evaluate(async () => (await chrome.storage.session.get("tompathy-practice-setup"))["tompathy-practice-setup"]);
    const artifact = (await reading()).artifact;
    const started = performance.now();
    const response = await fetch(setup.url + "/v1/analyze", {
      method: "POST", headers: { Authorization: `Bearer ${setup.token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ requestId: crypto.randomUUID(), artifact, scope: "artifact", mode: "preview" }),
      signal: AbortSignal.timeout(615000),
    });
    if (!response.ok) throw Error(`Preparation failed: HTTP ${response.status}: ${await response.text()}`);
    const packet = await response.json();
    await writeFile(`.local/${prefix}-native-packet.json`, JSON.stringify(packet));
    receipt.preparation = { budgetSeconds: 600, seconds: (performance.now() - started) / 1000, revision: packet.artifact.revision,
      modules: packet.preview.modules, payoff: packet.preview.payoff };
    expect(packet.preview.agreement).toBeTruthy();
    console.log(JSON.stringify({ preparation: receipt.preparation }));
  }
  await panel.getByRole("button", { name: "Reader menu", exact: true }).click();
  await expect(panel.getByRole("checkbox", { name: "Research preview", exact: true })).toBeChecked();
  const start = performance.now();
  await panel.getByRole("button", { name: "Load cached real preview", exact: true }).click();
  // A new capture is adopted directly; an existing reading needs review.
  const acceptance = panel.getByRole("button", { name: "Accept this revision", exact: true });
  await expect.poll(async () => Boolean((await reading())?.packet?.preview?.cachedAt) || await acceptance.isVisible()).toBe(true);
  if (await acceptance.isVisible()) await acceptance.click();
  await expect.poll(async () => panel.evaluate(async () => (await chrome.storage.session.get("reading")).reading?.packet?.preview?.cachedAt)).toBeTruthy();
  const saved = await panel.evaluate(async () => (await chrome.storage.session.get("reading")).reading);
  expect(saved.packet.provider.mode).toBe("preview");
  expect(saved.packet.preview.cachedAt).toBeTruthy();
  expect(saved.packet.preview.agreement).toBeTruthy();
  Object.assign(receipt, { seconds: (performance.now() - start) / 1000, cachedAt: saved.packet.preview.cachedAt,
    revision: saved.packet.artifact.revision, agreement: saved.packet.preview.agreement, build: session.review.receipt.build, browser: session.review.receipt.chromeVersion });
  const layout = await panel.evaluate(() => {
    const bounds = selector => document.querySelector(selector)?.getBoundingClientRect();
    const attention = bounds(".goals-region"), cloud = bounds(".living-cloud"), process = bounds(".process-region"), records = bounds(".process-region > .recorded-process");
    const status = bounds(".process-region > .preview-modules");
    return { cloudContained: !cloud || cloud.bottom <= attention.bottom,
      sectionsSeparate: attention.bottom <= process.top, recordsBelowStatus: !records || records.top >= status.bottom };
  });
  receipt.layout = layout;
  expect(Object.values(layout).every(Boolean)).toBe(true);
  await panel.screenshot({ path: `evidence/${prefix}-native.png` });
  await panel.locator(".goals-region .preview-modules > summary").filter({ hasText: /^Research preview/ }).click();
  const comparison = panel.getByText(/^With more context, these readers' top-departure overlap/);
  await comparison.scrollIntoViewIfNeeded();
  await expect(comparison).toBeVisible();
  await panel.screenshot({ path: `evidence/${prefix}-agreement.png` });
  await panel.locator(".preview-region-group > summary").first().click();
  await panel.locator(".preview-region-list button").first().click();
  await expect(source.locator("[data-tompathy-selected]")).toHaveCount(1);
  receipt.sourceLocated = true;
  if (clef) {
    const notes = saved.packet.hypotheses.filter(h => h.description.startsWith("Clef-flash joint decision;"));
    const expected = saved.packet.artifact.regions.slice(0, 20).filter(r => r.anchor.exact.length <= 12000).length * 5;
    expect(notes).toHaveLength(expected);
    expect(notes.every(h => h.evidenceStatus === "unvalidated" && h.basis === "model-judgment")).toBe(true);
    await panel.getByText("Text habits and technique notes", { exact: true }).click();
    const visibleNotes = panel.locator(".recorded-process button").filter({ hasText: "Clef-flash joint decision;" });
    await expect(visibleNotes).toHaveCount(expected);
    await visibleNotes.first().scrollIntoViewIfNeeded();
    await expect(visibleNotes.first()).toBeVisible();
    await panel.screenshot({ path: "evidence/preview-clef-techniques.png" });
    receipt.clefNotes = { count: notes.length, allUnvalidated: true, visible: true };
  }
  if (!process.argv.includes("--quick")) {
  // Exercise the actual Follow pages setting and cross-origin transitions with
  // the fast admitted path; preview inference was verified above.
  await panel.getByRole("button", { name: "Reader menu", exact: true }).click();
  await panel.getByRole("checkbox", { name: "Research preview", exact: true }).uncheck();
  await panel.getByRole("button", { name: "Close dialog", exact: true }).click();
  const permissions = await context.newPage();
  await permissions.goto("chrome://extensions/");
  await permissions.evaluate(async id => {
    for (const host of ["http://*/*", "https://*/*"])
      await chrome.developerPrivate.addHostPermission(id, host);
  }, session.review.receipt.extensionId);
  await permissions.close();
  await session.page.bringToFront();
  await session.page.getByRole("button", { name: /Enable Follow pages/ }).click();
  await expect(session.page.locator("#following")).toContainText("Follow pages is on");
  receipt.navigation = [];
  for (const url of ["https://paulgraham.com/identity.html", "https://abrahamhaskins.org/art/"]) {
    await source.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
    await source.bringToFront();
    await expect.poll(async () => (await reading())?.packet?.artifact?.source, { timeout: 30000 }).toBe(url);
    expect((await reading()).packet.provider.id).toBe("tompathy-engine");
    receipt.navigation.push({ source: url, automaticReading: true, toolbarUsed: false });
  }
  expect((await reading()).artifact.revision).toBe(saved.artifact.revision);
  }
  receipt.passed = true;
} catch (error) {
  receipt.passed = false;
  receipt.failure = error.message;
  await panel?.screenshot({ path: "evidence/preview-cache-failure.png" }).catch(() => {});
  throw error;
} finally {
  let cleanupError;
  try {
    await session?.stop();
    if (session) {
      let alive = false;
      try { await fetch(session.url + "/v1/health", { signal: AbortSignal.timeout(1000) }); alive = true; } catch {}
      if (alive) throw Error("Owned companion remained reachable after shutdown");
      receipt.ownedCompanionClosed = true;
    }
  } catch (error) { cleanupError = error; receipt.passed = false; receipt.cleanupError = error.message; }
  finally {
    await session?.review.cdp.send("Browser.close").catch(() => {});
    for (const browser of connections) await browser.close().catch(() => {});
  }
  await writeFile(`evidence/${clef ? "preview-clef-cache" : "preview-cache"}-validation.json`, JSON.stringify(receipt, null, 2));
  console.log(JSON.stringify({ passed: receipt.passed, cacheSeconds: receipt.seconds, cachedAt: receipt.cachedAt,
    revision: receipt.revision, navigation: receipt.navigation, failure: receipt.failure, cleanupError: receipt.cleanupError }));
  if (cleanupError) throw cleanupError;
}
