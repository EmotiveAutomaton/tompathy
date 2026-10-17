// Exact live-page capture through the installed extension, without model work.
import { expect } from "@playwright/test";
import { mkdir, mkdtemp, writeFile } from "node:fs/promises";
import path from "node:path";
import { openReview } from "./chrome-review.mjs";

await mkdir("evidence", { recursive: true });
const profile = await mkdtemp(path.resolve(".local/art-capture-"));
let review, attached;
try {
  review = await openReview({ profile, showGuide: false });
  const context = review.browser.contexts()[0];
  const settings = await context.newPage();
  await settings.goto("chrome://extensions/");
  await settings.evaluate(async id => {
    await chrome.developerPrivate.addHostPermission(id, "https://abrahamhaskins.org/*");
  }, review.receipt.extensionId);
  await settings.close();
  const source = await context.newPage();
  await source.goto("https://abrahamhaskins.org/art/", { waitUntil: "networkidle", timeout: 60000 });
  await source.bringToFront();
  const targets = await review.cdp.send("Target.getTargets", { filter: [{ type: "tab" }] });
  await review.cdp.send("Extensions.triggerAction", { id: review.receipt.extensionId,
    targetId: targets.targetInfos.find(t => t.url === source.url()).targetId });
  attached = await openReview({ profile, showGuide: false });
  const panel = attached.browser.contexts()[0].pages().find(p => p.url().includes("/panel.html"));
  if (!panel) throw Error("Native panel did not open");
  const capture = () => panel.evaluate(async () => (await chrome.storage.session.get("reading")).reading?.artifact);
  await expect.poll(async () => (await capture())?.source, { timeout: 20000 }).toBe(source.url());
  const artifact = await capture();
  expect(artifact.regions.some(r => r.anchor.exact === "Loading equation…")).toBe(false);
  await writeFile(".local/art-current-capture.json", JSON.stringify(artifact));
  console.log(JSON.stringify({ revision: artifact.revision, regions: artifact.regions.length,
    words: artifact.regions.reduce((n, r) => n + r.anchor.exact.split(/\s+/).filter(Boolean).length, 0), capturedAt: artifact.capturedAt }));
} finally {
  await review?.cdp.send("Browser.close").catch(() => {});
  await attached?.browser.close();
  await review?.browser.close();
}
