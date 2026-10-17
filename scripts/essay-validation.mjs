import { expect } from "@playwright/test";
import { mkdir, mkdtemp, writeFile } from "node:fs/promises";
import path from "node:path";
import { openReview } from "./chrome-review.mjs";

await mkdir("evidence", { recursive: true });
const profile = await mkdtemp(path.resolve(".local/essay-validation-"));
const connections = [];
const pendingKeys = [];
const receipt = {
  checkedAt: new Date().toISOString(),
  surface: "Native Chrome side panel and source-page essay",
  checks: [],
  errors: [],
};
let review, panel, source;
try {
  review = await openReview({ profile, showGuide: false });
  connections.push(review.browser);
  Object.assign(receipt, {
    browser: review.receipt.chromeVersion,
    build: review.receipt.build,
  });
  const context = review.browser.contexts()[0];
  context.setDefaultTimeout(10000);
  await context.route("https://example.com/**", (route) =>
    route.fulfill({
      contentType: "text/html",
      body: `<!doctype html><title>Essay review fixture</title><style>body{margin:60px auto;max-width:680px;font:20px/1.7 Georgia;background:#f2f0e9;color:#283d37}p{margin:2em 0}</style><article><h1>A page behind the essay</h1><p>This constructed page checks that a reader can open an essay without leaving the piece of writing behind.</p><p>The source stays visible around the edges. Closing the essay returns to the same reading.</p><p>These paragraphs are original test fixtures. They do not supply any research result or inferred preference.</p></article>`,
    }),
  );
  source = await context.newPage();
  await source.goto("https://example.com/essays");
  await source.bringToFront();
  const targets = await review.cdp.send("Target.getTargets", {
    filter: [{ type: "tab" }],
  });
  await review.cdp.send("Extensions.triggerAction", {
    id: review.receipt.extensionId,
    targetId: targets.targetInfos.find((t) => t.url === source.url()).targetId,
  });
  const attached = await openReview({ profile, showGuide: false });
  connections.push(attached.browser);
  panel = attached.browser
    .contexts()[0]
    .pages()
    .find((p) => p.url().includes("/panel.html"));
  if (!panel) throw Error("Native panel did not open");
  panel.setDefaultTimeout(10000);
  panel.on("pageerror", (e) => receipt.errors.push(e.message));
  source.on("pageerror", (e) => receipt.errors.push(e.message));
  const reading = () =>
    panel.evaluate(
      async () => (await chrome.storage.session.get("reading")).reading,
    );
  await expect
    .poll(async () => (await reading())?.artifact?.source)
    .toBe(source.url());
  const before = (await reading()).artifact;
  const trigger = panel.getByRole("button", {
    name: "About Expertise (Previous attention)",
    exact: true,
  });
  await trigger.hover();
  await expect(panel.getByRole("tooltip")).toContainText(
    "Click for part two of a cool",
  );
  await panel.screenshot({ path: "evidence/essays-native-panel.png" });
  await trigger.click();
  const host = source.locator('[data-tompathy-ui="essay"]');
  const frame = host.frameLocator("iframe");
  await expect(
    frame.getByRole("heading", { name: "Expertise (Previous Attention)" }),
  ).toBeVisible();
  expect((await host.locator("dialog").boundingBox()).width).toBeGreaterThan(
    700,
  );
  await expect(panel.locator(".essay-dialog")).toHaveCount(0);
  await source.screenshot({ path: "evidence/essays-native-source.png" });
  await frame.locator("figure").first().scrollIntoViewIfNeeded();
  await expect
    .poll(() =>
      frame
        .locator("img")
        .first()
        .evaluate((img) => img.complete && img.naturalWidth > 0),
    )
    .toBe(true);
  await source.screenshot({ path: "evidence/essays-native-figures.png" });
  for (const image of await frame.locator(".essay-images img").all()) {
    await image.scrollIntoViewIfNeeded();
    await expect
      .poll(() => image.evaluate((img) => img.complete && img.naturalWidth > 0))
      .toBe(true);
  }
  const firstCitation = frame.locator("sup a").first();
  expect(await firstCitation.getAttribute("href")).toContain(
    "10.1037/h0061626",
  );
  await frame.getByRole("button", {name:"Enlarge The inference of empathy", exact:true}).click();
  await expect(host.locator("dialog")).toHaveClass("image-open");
  await expect(frame.locator(".essay-lightbox")).toBeVisible();
  const expandedBox = await host.locator("dialog").boundingBox();
  expect(expandedBox.x).toBe(0);
  expect(expandedBox.y).toBe(0);
  expect(expandedBox.width).toBe(await source.evaluate(() => innerWidth));
  await source.screenshot({path:"evidence/essays-native-lightbox.png"});
  await frame.locator(".essay-lightbox").click();
  await expect(frame.locator(".essay-lightbox")).toHaveCount(0);
  await expect(host.locator("dialog")).not.toHaveClass("image-open");
  await frame.getByRole("button", {name:"Enlarge The inference of empathy", exact:true}).press("Enter");
  await frame.locator(".essay-lightbox").press("Escape");
  await expect(frame.locator(".essay-lightbox")).toHaveCount(0);
  await expect(host.locator("dialog")).toBeVisible();
  await frame.getByRole("link", {name:"next",exact:true}).click();
  await expect(frame.getByRole("heading")).toHaveText("Core Values");
  await frame.getByRole("link", {name:"here",exact:true}).click();
  await expect(frame.getByRole("heading")).toHaveText("Current Attention");
  await frame.getByRole("link", {name:"next",exact:true}).click();
  await expect(frame.getByRole("heading")).toHaveText("Expertise (Previous Attention)");
  // A page cannot close the extension frame by spoofing its public message name.
  await source.evaluate(() =>
    window.postMessage({ type: "TOMPATHY_ESSAY_CLOSE", nonce: "wrong" }, "*"),
  );
  await expect(host.locator("dialog")).toBeVisible();
  await frame.getByRole("button", { name: "Close essay" }).click();
  await expect(host).toHaveCount(0);
  await trigger.click();
  await expect(host.locator("iframe")).toBeVisible();
  await frame.getByRole("button", { name: "Close essay" }).focus();
  // Chrome can strand the CDP key acknowledgement when Escape destroys its
  // focused cross-origin frame. Verify the actual dismissal, then settle the
  // pending protocol call when this disposable browser closes in finally.
  pendingKeys.push(source.keyboard.press("Escape").catch(() => {}));
  await expect(host).toHaveCount(0);
  await trigger.click();
  await expect(
    frame.getByRole("button", { name: "Close essay" }),
  ).toBeVisible();
  await source.mouse.click(8, 8);
  await expect(host).toHaveCount(0);
  // Exercise all new raster formats and the bibliography through the real iframe.
  for (const label of ["Current attention", "Core values"]) {
    await panel
      .getByRole("button", { name: "About " + label, exact: true })
      .click();
    await expect(host.locator("iframe")).toBeVisible();
    for (const image of await frame.locator(".essay-images img").all()) {
      await image.scrollIntoViewIfNeeded();
      await expect
        .poll(() =>
          image.evaluate((img) => img.complete && img.naturalWidth > 0),
        )
        .toBe(true);
    }
    await frame.getByRole("button", { name: "Close essay" }).click();
  }
  await panel.getByRole("button", { name: "Reader menu", exact: true }).click();
  await panel
    .getByRole("button", { name: "Bibliography", exact: true })
    .click();
  await expect(
    frame.getByRole("heading", { name: "Bibliography", exact: true }),
  ).toBeVisible();
  await expect(
    frame.locator(
      '.essay-bibliography a[href="https://arxiv.org/abs/2502.00873"]',
    ),
  ).toBeVisible();
  await source.screenshot({ path: "evidence/essays-native-bibliography.png" });
  await frame.getByRole("button", { name: "Close essay" }).click();
  expect((await reading()).artifact.revision).toBe(before.revision);
  expect((await reading()).artifact.regions).toEqual(before.regions);
  receipt.checks.push(
    "Native delayed hint; wide overlay; cropped thumbnails and original-image full-viewport lightbox; click/Escape image dismissal; first/next essay navigation; all raster formats; shared bibliography; direct citations; X/Escape/outside essay dismissal; spoofed close ignored; original captured text unchanged",
  );
  // A protected/unavailable source falls back to the same local reading surface.
  await source.goto("chrome://version/");
  await trigger.click();
  await expect(panel.locator(".essay-dialog")).toBeVisible({ timeout: 10000 });
  await panel.getByRole("button", { name: "Close essay" }).click();
  receipt.checks.push(
    "Unavailable source falls back to a dismissible panel essay",
  );
  await source.goto(`chrome-extension://${review.receipt.extensionId}/review.html`);
  await source.getByRole("link", {name: /Open the safe example/}).click();
  await source.getByRole("button", {name: "Open Maker Reader"}).click();
  const ai = panel.getByRole("checkbox", {name: "Mark likely AI"});
  await expect(ai).toBeVisible();
  await ai.check();
  await expect(panel.locator('.ai-marked[data-node="sentence-6-3"]')).toHaveCount(1);
  await expect(panel.getByRole("button", {name: "Drive SEEKING", exact: true})).toBeVisible();
  await panel.screenshot({path: "evidence/safe-example-native.png"});
  receipt.checks.push("Review desk safe example opens in the native panel, shows drive artwork and explicit AI marking");
  expect(receipt.errors).toEqual([]);
  receipt.passed = true;
} catch (error) {
  receipt.passed = false;
  receipt.failure = error.message;
  await source
    ?.screenshot({ path: "evidence/essays-native-failure.png" })
    .catch(() => {});
  throw error;
} finally {
  await writeFile(
    "evidence/essay-validation.json",
    JSON.stringify(receipt, null, 2),
  );
  console.log(JSON.stringify(receipt, null, 2));
  await review?.cdp.send("Browser.close").catch(() => {});
  for (const browser of connections) await browser.close().catch(() => {});
  await Promise.all(pendingKeys);
}
