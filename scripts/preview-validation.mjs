import { expect } from "@playwright/test";
import { mkdir, mkdtemp, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { startPractice } from "./practice-session.mjs";
import { openReview } from "./chrome-review.mjs";

await mkdir("evidence", { recursive: true });
const profile = await mkdtemp(path.resolve(".local/preview-check-"));
const receipt = { checkedAt: new Date().toISOString(), surface: "Native Chrome side panel, service-worker relay, real CPU readers", checks: [], errors: [] };
let session, panel;
const connections = [];
try {
  session = await startPractice({ profile });
  connections.push(session.review.browser);
  Object.assign(receipt, { browser: session.review.receipt.chromeVersion, build: session.review.receipt.build });
  const context = session.review.browser.contexts()[0];
  context.setDefaultTimeout(15000);
  const settings = await context.newPage();
  await settings.goto("chrome://extensions/");
  await settings.evaluate(async id => {
    await chrome.developerPrivate.addHostPermission(id, "http://127.0.0.1/*");
    await chrome.developerPrivate.addHostPermission(id, "https://example.org/*");
  }, session.review.receipt.extensionId);
  await settings.close();
  receipt.permissionSetup = "Loopback and example.org only in a disposable profile; first-use permission bubbles remain a manual check.";
  await context.route("https://example.org/preview-check", route => route.fulfill({ contentType: "text/html", body: '<!doctype html><title>Constructed transport test</title><meta name="description" content="Software verification fixture, not research evidence."><article><h1>Constructed transport test</h1><p>We walked through the garden. We walked through the garden, but this time the gate was open.</p><p>The old path turned suddenly toward the river. A paper boat waited beside a broken umbrella.</p></article>' }));
  await session.page.locator("#connect").click();
  await expect(session.page.locator("#connection")).toContainText("Connected to engine");
  await session.page.evaluate(async () => { await chrome.storage.local.set({ "tompathy-follow-pages": true }); });
  const source = await context.newPage();
  await source.goto("https://example.org/preview-check");
  await source.bringToFront();
  const targets = await session.review.cdp.send("Target.getTargets", { filter: [{ type: "tab" }] });
  await session.review.cdp.send("Extensions.triggerAction", { id: session.review.receipt.extensionId, targetId: targets.targetInfos.find(t => t.url === source.url()).targetId });
  const attached = await openReview({ profile, showGuide: false });
  connections.push(attached.browser);
  panel = attached.browser.contexts()[0].pages().find(p => p.url().includes("/panel.html"));
  if (!panel) throw Error("Native side panel did not open");
  panel.on("pageerror", e => receipt.errors.push(e.message));
  const reading = () => panel.evaluate(async () => (await chrome.storage.session.get("reading")).reading);
  await expect.poll(async () => (await reading())?.packet?.provider.mode, { timeout: 180000 }).toBe("preview");
  const packet = (await reading()).packet;
  receipt.modules = packet.preview.modules;
  receipt.readers = packet.preview.readers;
  receipt.agreement = packet.preview.agreement;
  expect(packet.hypotheses.some(h => h.kind === "attention")).toBe(true);
  expect(packet.hypotheses.every(h => h.evidenceStatus && h.basis)).toBe(true);
  expect(packet.preview.modules.find(m => m.id === "deviation").status).toBe("complete");
  expect(packet.preview.modules.find(m => m.id === "agreement").status).toBe("complete");
  await expect(panel.locator(".preview-banner")).toHaveCount(3);
  await expect(panel.getByLabel("Creator selection")).toHaveValue("all");
  await expect(panel.locator("summary", { hasText: "Makers and source evidence" })).toHaveCount(1);
  await expect(panel.locator(".living-cloud .cloud-position").first()).toBeVisible();
  const headingOverlap = await panel.evaluate(() => [...document.querySelectorAll(".region")].some(region => {
    const heading = region.querySelector(".section-heading h2")?.getBoundingClientRect();
    const banner = region.querySelector(".preview-banner")?.getBoundingClientRect();
    return heading && banner && banner.top < heading.bottom;
  }));
  expect(headingOverlap).toBe(false);
  await panel.screenshot({ path: "evidence/preview-native.png" });
  receipt.checks.push("Automatic native reading uses real pinned CPU models through the service worker; three banners, complete labels, All makers default");
  await panel.getByRole("button", { name: "Reader menu", exact: true }).click();
  await expect(panel.getByRole("checkbox", { name: "Research preview", exact: true })).toBeChecked();
  await panel.getByRole("checkbox", { name: "Research preview", exact: true }).uncheck();
  await panel.getByRole("button", { name: "Close dialog", exact: true }).click();
  await expect.poll(async () => Boolean((await reading())?.packet), { timeout: 15000 }).toBe(true);
  expect((await reading()).packet.provider.mode).not.toBe("preview");
  await expect(panel.locator(".preview-banner")).toHaveCount(0);
  receipt.checks.push("Turning preview off clears the preview and requests the admitted path");
  const setup = await session.page.evaluate(async () => (await chrome.storage.session.get("tompathy-practice-setup"))["tompathy-practice-setup"]);
  const headers = { Authorization: `Bearer ${setup.token}`, "Content-Type": "application/json" };
  // Backups contain actual earlier engine outputs, including unfinished modules.
  const cachedResponse = await fetch(setup.url + "/v1/analyze", { method: "POST", headers,
    body: JSON.stringify({ requestId: crypto.randomUUID(), artifact: packet.artifact, scope: "artifact", mode: "preview", preferCache: true }),
    signal: AbortSignal.timeout(15000) });
  expect(cachedResponse.ok).toBe(true);
  const cached = await cachedResponse.json();
  expect(cached.preview.cachedAt).toBeTruthy();
  expect(cached.preview.modules).toEqual(packet.preview.modules);
  receipt.checks.push("Exact-input real-run backup returns its timestamp and original module statuses");
  receipt.cancellations = [];
  for (const kind of ["news", "wikipedia", "github"]) {
    const artifact = JSON.parse(await readFile(`.local/preview-live-${kind}.json`, "utf8"));
    const requestId = crypto.randomUUID();
    const response = await fetch(setup.url + "/v1/analyze", { method: "POST", headers: { ...headers, Accept: "text/event-stream" },
      body: JSON.stringify({ requestId, artifact, scope: "artifact", mode: "preview", ...(["wikipedia", "github"].includes(kind) ? { history: kind, historyLimit: 20 } : {}) }),
      signal: AbortSignal.timeout(120000) });
    expect(response.ok).toBe(true);
    const stream = response.body.getReader(), decoder = new TextDecoder();
    let events = "", cancelled = false, phase;
    while (true) {
      const { done, value } = await stream.read();
      if (done) break;
      events += decoder.decode(value, { stream: true });
      const targetPhase = kind === "news" ? "Technique notes" : "Content corrections";
      if (!cancelled && events.includes(`"phase": "${targetPhase}"`)) {
        // Let an actual CPU inference start, then exercise the public cancel API.
        await new Promise(resolve => setTimeout(resolve, 500));
        const stopped = await fetch(setup.url + "/v1/analyze/" + requestId, { method: "DELETE", headers, signal: AbortSignal.timeout(10000) });
        expect(stopped.ok).toBe(true);
        cancelled = true;
        phase = targetPhase;
      }
      if (events.length > 10_000_000) throw Error("Cancellation check exceeded its event bound");
    }
    expect(cancelled).toBe(true);
    expect(events).toContain("event: cancelled");
    if (kind !== "news") expect(events).toContain('"kind": "person"');
    const health = await fetch(setup.url + "/v1/health", { headers, signal: AbortSignal.timeout(10000) });
    expect(health.ok).toBe(true);
    // A successful fresh admitted request proves the single worker was released.
    const next = await fetch(setup.url + "/v1/analyze", { method: "POST", headers,
      body: JSON.stringify({ requestId: crypto.randomUUID(), artifact, scope: "artifact", mode: "admitted" }), signal: AbortSignal.timeout(15000) });
    expect(next.ok).toBe(true);
    receipt.cancellations.push({ tier: kind === "news" ? "T0" : "T1", source: kind, phase, cancelled: true, healthy: true, subsequentRequest: true });
  }
  if (process.argv.includes("--curator")) {
    const permissions = await context.newPage();
    await permissions.goto("chrome://extensions/");
    await permissions.evaluate(async id => chrome.developerPrivate.addHostPermission(id, "https://abrahamhaskins.org/*"), session.review.receipt.extensionId);
    await permissions.close();
    await source.goto("https://abrahamhaskins.org/art/", { waitUntil: "domcontentloaded", timeout: 45000 });
    await source.bringToFront();
    await expect.poll(async () => (await reading())?.artifact?.source, { timeout: 20000 }).toBe("https://abrahamhaskins.org/art/");
    await expect.poll(async () => Boolean((await reading())?.packet), { timeout: 15000 }).toBe(true);
    await panel.getByRole("button", { name: "Reader menu", exact: true }).click();
    await panel.getByRole("checkbox", { name: "Research preview", exact: true }).check();
    await panel.getByRole("button", { name: "Close dialog", exact: true }).click();
    const started = performance.now();
    await expect.poll(async () => (await reading())?.packet?.provider.mode, { timeout: 180000 }).toBe("preview");
    const curatorPacket = (await reading()).packet;
    await writeFile(".local/preview-curator-native-packet.json", JSON.stringify(curatorPacket));
    receipt.curator = { source: curatorPacket.artifact.source, revision: curatorPacket.artifact.revision,
      seconds: (performance.now() - started) / 1000, modules: curatorPacket.preview.modules, agreement: curatorPacket.preview.agreement, payoff: curatorPacket.preview.payoff };
    expect(curatorPacket.preview.agreement).toBeTruthy();
    await panel.screenshot({ path: "evidence/preview-curator-native.png" });
    await panel.locator(".goals-region .preview-modules > summary").filter({ hasText: /^Research preview/ }).click();
    const comparison = panel.getByText(/^With more context, these readers' top-departure overlap/);
    await comparison.scrollIntoViewIfNeeded();
    await expect(comparison).toBeVisible();
    await panel.screenshot({ path: "evidence/preview-curator-agreement.png" });
    await panel.locator(".preview-region-group summary").first().click();
    await panel.locator(".preview-region-list button").first().click();
    await expect(source.locator("[data-tompathy-selected]")).toHaveCount(1);
    receipt.checks.push("Full live curator essay renders both real reader agreement shares in the native panel after explicit CPU cache preparation");
  }
  expect(receipt.errors).toEqual([]);
  receipt.passed = true;
} catch (error) {
  receipt.passed = false;
  receipt.failure = error.message;
  await panel?.screenshot({ path: "evidence/preview-failure.png" }).catch(() => {});
  throw error;
} finally {
  await writeFile("evidence/preview-validation.json", JSON.stringify(receipt, null, 2));
  console.log(JSON.stringify(receipt, null, 2));
  await session?.stop();
  await session?.review.cdp.send("Browser.close").catch(() => {});
  for (const browser of connections) await browser.close().catch(() => {});
}
