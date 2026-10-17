// Public-page software acceptance checks; never scientific admission.
import { mkdir, mkdtemp, writeFile } from "node:fs/promises";
import path from "node:path";
import { build } from "esbuild";
import { startPractice } from "./practice-session.mjs";

await build({ entryPoints: ["src/core/model.ts"], bundle: true, platform: "node", format: "esm", outfile: ".local/preview-contract.mjs" });
const { parsePacket } = await import("../.local/preview-contract.mjs");
const pages = [
  ["news", "https://www.nasa.gov/image-article/black-eye-galaxy/"],
  ["blog", "https://paulgraham.com/identity.html"],
  ["wikipedia", "https://en.wikipedia.org/wiki/Sneckdown"],
  ["github", "https://github.com/jbhuang0604/awesome-tips/blob/main/paper-writing.md"],
  ["curator", "https://abrahamhaskins.org/art/"],
];
await mkdir("evidence", { recursive: true });
const receipt = { checkedAt: new Date().toISOString(), scope: "Five public pages: real extension captures and real local models; not scientific validation", pages: [] };
let session;
try {
  const profile = await mkdtemp(path.resolve(".local/preview-live-"));
  session = await startPractice({ profile });
  const context = session.review.browser.contexts()[0];
  const settings = await context.newPage();
  await settings.goto("chrome://extensions/");
  await settings.evaluate(async ({ id, urls }) => {
    for (const url of urls) await chrome.developerPrivate.addHostPermission(id, new URL(url).origin + "/*");
  }, { id: session.review.receipt.extensionId, urls: pages.map(p => p[1]) });
  await settings.close();
  const setup = await session.page.evaluate(async () => (await chrome.storage.session.get("tompathy-practice-setup"))["tompathy-practice-setup"]);
  for (const [kind, url] of pages) {
    const page = await context.newPage();
    const result = { kind, url };
    try {
      await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
      await page.waitForLoadState("load", { timeout: 15000 }).catch(() => {});
      await page.bringToFront();
      const targets = await session.review.cdp.send("Target.getTargets", { filter: [{ type: "tab" }] });
      const target = targets.targetInfos.find(t => t.url === page.url());
      if (!target) throw Error("Source browser target is unavailable");
      await session.review.cdp.send("Extensions.triggerAction", { id: session.review.receipt.extensionId, targetId: target.targetId });
      const capture = await session.page.evaluate(async () => {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab?.id) throw Error("Source tab is unavailable");
        await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] });
        return chrome.tabs.sendMessage(tab.id, { type: "TOMPATHY_CAPTURE" });
      });
      if (!capture.artifact) throw Error(capture.error ?? "No capture");
      result.revision = capture.artifact.revision;
      result.regions = capture.artifact.regions.length;
      result.words = capture.artifact.regions.reduce((n, r) => n + r.anchor.exact.split(/\s+/).length, 0);
      // Ignored local captures permit exact review without putting public prose in fixtures.
      await writeFile(`.local/preview-live-${kind}.json`, JSON.stringify(capture.artifact));
      console.log(JSON.stringify({ started: kind, words: result.words }));
      const started = performance.now();
      const response = await fetch(setup.url + "/v1/analyze", { method: "POST", redirect: "error", signal: AbortSignal.timeout(180000),
        headers: { Authorization: `Bearer ${setup.token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ requestId: crypto.randomUUID(), artifact: capture.artifact, scope: "artifact", mode: "preview",
          ...(["wikipedia", "github"].includes(kind) ? { history: kind, historyLimit: 20 } : {}) }),
      });
      if (!response.ok) throw Error(`Companion HTTP ${response.status}`);
      const packet = parsePacket(await response.text());
      result.seconds = (performance.now() - started) / 1000;
      result.modules = packet.preview.modules;
      result.agreement = packet.preview.agreement;
      result.payoff = packet.preview.payoff;
      result.cachedAt = packet.preview.cachedAt;
      result.makerKinds = packet.makers.map(m => m.kind);
      result.completeLabels = packet.hypotheses.every(h => h.evidenceStatus && h.basis);
      result.historyReconstructed = !["wikipedia", "github"].includes(kind) || packet.makers.some(m => m.kind === "person" || m.kind === "bot");
      result.failedModules = packet.preview.modules.filter(m => m.status === "failed").map(m => m.id);
      result.admissions = packet.provider.admissions;
      result.withinThreeMinutes = result.seconds < 180;
      result.passed = result.withinThreeMinutes && result.completeLabels && result.historyReconstructed && !result.failedModules.length && packet.provider.mode === "preview";
      await writeFile(`.local/preview-live-${kind}-packet.json`, JSON.stringify(packet));
    } catch (error) { result.passed = false; result.failure = error.message; }
    finally { await page.close(); }
    receipt.pages.push(result);
    await writeFile("evidence/preview-live-pages.json", JSON.stringify(receipt, null, 2));
    console.log(JSON.stringify(result));
  }
} finally {
  await writeFile("evidence/preview-live-pages.json", JSON.stringify(receipt, null, 2));
  await session?.stop();
  await session?.review.cdp.send("Browser.close").catch(() => {});
  await session?.review.browser.close().catch(() => {});
}
