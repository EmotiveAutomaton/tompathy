// Focused native side-panel verification; owns one disposable Chrome profile.
import { expect } from "@playwright/test";
import { mkdir, mkdtemp, writeFile } from "node:fs/promises";
import path from "node:path";
import { openReview } from "./chrome-review.mjs";

await mkdir("evidence", {recursive: true});
const profile = await mkdtemp(path.resolve(".local/ai-mark-validation-"));
const connections = [];
const receipt = {checkedAt: new Date().toISOString(), profile, errors: []};
let review;
try {
  review = await openReview({profile, showGuide: false});
  connections.push(review.browser);
  Object.assign(receipt, {build: review.receipt.build, browser: review.receipt.chromeVersion});
  const source = await review.browser.contexts()[0].newPage();
  await source.goto(`chrome-extension://${review.receipt.extensionId}/review.html`);
  await source.getByRole("link", {name: /Open the safe example/}).click();
  await source.getByRole("button", {name: "Open Maker Reader"}).click();
  const attached = await openReview({profile, showGuide: false});
  connections.push(attached.browser);
  const panel = attached.browser.contexts()[0].pages().find(p => p.url().includes("/panel.html"));
  if (!panel) throw Error("Native side panel did not open");
  panel.on("pageerror", e => receipt.errors.push(e.message));
  const checkbox = panel.getByRole("checkbox", {name: "Mark likely AI"});
  await checkbox.check();
  await expect(panel.locator(".ai-marked")).toHaveCount(3);
  const marks = await panel.locator(".ai-outline-outer").evaluateAll(nodes => nodes.map(node => ({
    id: node.getAttribute("data-ai-node"), width: Number(node.getAttribute("data-outline-width")),
    opacity: Number(getComputedStyle(node).strokeOpacity),
  })));
  const opacity = id => marks.find(mark => mark.id === id).opacity;
  expect(opacity("sentence-8-1")).toBeCloseTo(.94);
  expect(opacity("sentence-6-2")).toBeCloseTo(.915);
  expect(opacity("sentence-6-3")).toBeCloseTo(.99);
  expect(marks.map(m => m.width).sort()).toEqual([1,1.5,2]);
  await expect(panel.locator(".pyramid svg > g > .ai-outline-layer:last-child")).toHaveCount(1);
  const control = await panel.locator(".mark-ai").boundingBox();
  const heading = await panel.locator(".process-region .section-heading h2").boundingBox();
  expect(control.y).toBeGreaterThan(heading.y + heading.height);
  expect(Math.abs(control.x + control.width - heading.x - heading.width)).toBeLessThan(15);
  const box = await panel.locator(".mark-ai-box").boundingBox();
  const cross = await panel.locator(".mark-ai-box svg").boundingBox();
  expect(cross.width).toBeGreaterThan(box.width);
  expect(Math.abs(box.x + box.width / 2 - cross.x - cross.width / 2)).toBeLessThan(.6);
  expect(Math.abs(box.y + box.height / 2 - cross.y - cross.height / 2)).toBeLessThan(.6);
  await panel.mouse.move(0, 0);
  await checkbox.evaluate(el => el.blur());
  await expect(panel.locator(".mark-ai")).toHaveCSS("opacity", "1");
  await panel.screenshot({path: "evidence/ai-mark-native.png"});
  await checkbox.focus();
  await checkbox.press("Space");
  await expect(panel.locator(".ai-marked")).toHaveCount(0);
  await checkbox.press("Space");
  await expect(panel.locator(".ai-marked")).toHaveCount(3);
  expect(receipt.errors).toEqual([]);
  Object.assign(receipt, {marks, control, heading, box, cross, passed: true});
} catch (error) {
  Object.assign(receipt, {passed: false, failure: error.message});
  throw error;
} finally {
  await review?.cdp.send("Browser.close").catch(() => {});
  for (const browser of connections) await browser.close().catch(() => {});
  await writeFile("evidence/ai-mark-validation.json", JSON.stringify(receipt, null, 2));
  console.log(JSON.stringify(receipt, null, 2));
}
