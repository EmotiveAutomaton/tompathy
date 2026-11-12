// One disposable native Chrome side panel, with owned-process cleanup.
import { expect } from "@playwright/test";
import { mkdtemp, writeFile, rm } from "node:fs/promises";
import path from "node:path";
import { openReview } from "./chrome-review.mjs";

const root = path.resolve(".local");
const profile = await mkdtemp(path.join(root, "three-views-native-"));
const connections = [];
const result = {checkedAt:new Date().toISOString(), errors:[]};
let review;
try {
  review = await openReview({profile,showGuide:false});
  connections.push(review.browser);
  Object.assign(result,{build:review.receipt.build,browser:review.receipt.chromeVersion});
  const source = await review.browser.contexts()[0].newPage();
  await source.goto(`chrome-extension://${review.receipt.extensionId}/review.html`);
  await source.getByRole("link",{name:/Open the safe example/}).click();
  await source.getByRole("button",{name:"Open Maker Reader"}).click();
  const attached = await openReview({profile,showGuide:false});
  connections.push(attached.browser);
  const panel = attached.browser.contexts()[0].pages().find(p=>p.url().includes("/panel.html"));
  if (!panel) throw Error("Native side panel did not open");
  panel.on("pageerror",e=>result.errors.push(e.message));
  const graph = panel.locator(".values-landscape");
  await expect(graph).toHaveAttribute("data-perspective","work");
  await expect(graph.getByRole("table",{name:"Core values hierarchy"})).toBeVisible();
  const scroll=graph.locator(".values-table-scroll");
  expect(await scroll.evaluate(e=>e.scrollWidth>e.clientWidth && e.scrollHeight>e.clientHeight)).toBe(true);
  const value=graph.locator('[data-cell="value:work-care"]');
  await value.scrollIntoViewIfNeeded();
  await value.hover();
  expect(await graph.locator(".values-table-links path").count()).toBeGreaterThan(0);
  await panel.screenshot({path:"evidence/values-table-native-work.png"});
  await value.focus();
  await value.press("ArrowDown");
  await expect(graph.locator('[data-cell="goal:sentence-4-3"]')).toBeFocused();
  await panel.keyboard.press("Control+Home");
  await panel.getByRole("tab",{name:"author",exact:true}).click();
  await expect(graph.locator("[data-work]")).toHaveCount(0);
  await panel.screenshot({path:"evidence/values-table-native-author.png"});
  await graph.getByRole("button",{name:/^Sources/}).click();
  await expect(panel.locator(".modal")).toBeVisible();
  await panel.keyboard.press("Escape");
  const care=graph.getByRole("button",{name:"Drive CARE",exact:true});
  await care.focus();
  await expect(panel.locator(".hover-card")).toHaveCount(0);
  await care.press("Enter");
  await expect(panel.locator(".modal .preference-vector")).toHaveCount(3);
  await expect(panel.locator(".modal")).toBeVisible();
  await panel.keyboard.press("Escape");
  await panel.getByRole("tab",{name:"global",exact:true}).click();
  await panel.screenshot({path:"evidence/values-table-native-global.png"});
  expect(result.errors).toEqual([]);
  result.passed = true;
} catch (error) {
  Object.assign(result,{passed:false,failure:error.message});
  throw error;
} finally {
  await review?.cdp.send("Browser.close").catch(()=>{});
  for (const browser of connections) await browser.close().catch(()=>{});
  // The generated directory is owned by this test; normal review profiles are untouched.
  if (path.dirname(profile) !== root || !path.basename(profile).startsWith("three-views-native-")) throw Error("Unexpected cleanup path");
  try { await rm(profile,{recursive:true,force:true,maxRetries:6,retryDelay:500}); result.profileRemoved=true; }
  catch (error) { result.cleanupError=error.message; }
  await writeFile("evidence/three-views-native.json",JSON.stringify(result,null,2));
  console.log(JSON.stringify(result,null,2));
}
