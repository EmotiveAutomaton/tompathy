import { expect } from "@playwright/test";
import { mkdir, mkdtemp, writeFile } from "node:fs/promises";
import path from "node:path";
import { startPractice } from "./practice-session.mjs";
import { openReview } from "./chrome-review.mjs";

await mkdir("evidence", { recursive: true });
await mkdir(".local", { recursive: true });
const profile = await mkdtemp(path.resolve(".local/practice-check-"));
let session;
const connections = [];
const receipt = {
  checkedAt: new Date().toISOString(),
  surface:
    "Ordinary Chrome native side panel, live Wikipedia and real Python companion",
  pages: [],
  errors: [],
};
try {
  session = await startPractice({ profile });
  connections.push(session.review.browser);
  receipt.browser = session.review.receipt.chromeVersion;
  receipt.build = session.review.receipt.build;
  receipt.implementation = session.implementation;
  const guide = session.page;
  // Chrome's first-use native permission bubble is outside Playwright's page
  // surface. Grant only loopback through Chrome's own extension-settings API
  // in this disposable profile; the delivered manifest is not modified.
  const settings = await session.review.browser.contexts()[0].newPage();
  await settings.goto("chrome://extensions/");
  await settings.evaluate(async (id) => {
    await chrome.developerPrivate.addHostPermission(id, "http://127.0.0.1/*");
  }, session.review.receipt.extensionId);
  await settings.close();
  await guide.bringToFront();
  receipt.permissionSetup =
    "Loopback only, through Chrome extension settings; native first-use confirmation is a manual check";
  guide.on("pageerror", (error) => receipt.errors.push(error.message));
  await expect(
    guide.getByRole("button", { name: /Connect local engine/ }),
  ).toBeEnabled();
  await guide.getByRole("button", { name: /Connect local engine/ }).click();
  await expect(guide.locator("#connection")).toContainText(
    "Connected to engine",
    {
      timeout: 20000,
    },
  );
  await guide.screenshot({
    path: "evidence/practice-connected.png",
    fullPage: true,
  });
  for (const title of ["Sneckdown", "Desire_path"]) {
    const source = await session.review.browser.contexts()[0].newPage();
    const url = `https://en.wikipedia.org/wiki/${title}`;
    await source.goto(url, { waitUntil: "domcontentloaded" });
    await source.locator("#mw-content-text").waitFor();
    await source.bringToFront();
    const widthBefore = await source.evaluate(() => innerWidth);
    const targets = await session.review.cdp.send("Target.getTargets", {
      filter: [{ type: "tab" }],
    });
    const target = targets.targetInfos.find((t) => t.url === source.url());
    await session.review.cdp.send("Extensions.triggerAction", {
      id: session.review.receipt.extensionId,
      targetId: target.targetId,
    });
    const attached = await openReview({ profile, showGuide: false });
    connections.push(attached.browser);
    const panel = attached.browser
      .contexts()[0]
      .pages()
      .find((p) => p.url().includes("/panel.html"));
    if (!panel) throw Error("Native side panel did not open");
    panel.on("pageerror", (error) => receipt.errors.push(error.message));
    const reading = () =>
      panel.evaluate(
        async () => (await chrome.storage.session.get("reading")).reading,
      );
    await expect
      .poll(async () => (await reading())?.artifact?.source, { timeout: 20000 })
      .toBe(url);
    expect((await reading()).packet).toBeNull();
    if (!receipt.pages.length)
      await expect
        .poll(() => source.evaluate(() => innerWidth))
        .toBeLessThan(widthBefore);
    // The native panel remains open when switching to the second source.
    expect(await panel.evaluate(() => innerWidth)).toBeLessThan(600);
    const started = Date.now();
    await panel
      .getByRole("button", { name: "Analyze Wikipedia history", exact: true })
      .click();
    await expect(panel.getByLabel("Live engine reading")).toBeVisible({
      timeout: 90000,
    });
    const result = await reading();
    expect(result.packet.provider.id).toBe("tompathy-engine");
    expect(result.packet.origin).toBe("live provider");
    expect(result.packet.provider.admissions).toEqual([]);
    expect(result.packet.artifact).toEqual(result.artifact);
    expect(result.packet.process.nodes.length).toBeGreaterThan(1);
    expect(result.packet.hypotheses.some((h) => h.kind === "value")).toBe(
      false,
    );
    await expect(panel.getByLabel("Recorded production history")).toBeVisible();
    const menu = panel.getByRole("button", {
      name: "Reader menu",
      exact: true,
    });
    await panel
      .getByRole("button", { name: /Recorded correction/ })
      .first()
      .click();
    await expect(panel.getByRole("dialog")).toBeVisible();
    await expect(panel.getByRole("dialog")).toContainText("Before:");
    await expect(panel.getByRole("dialog")).toContainText("After:");
    await panel.screenshot({ path: `evidence/practice-${title}-evidence.png` });
    await panel
      .getByRole("button", { name: "Close dialog", exact: true })
      .click();
    await panel
      .getByRole("button", { name: "Dismiss notice", exact: true })
      .click();
    await expect(panel.locator(".creator-current")).toContainText(
      result.packet.makers[0].label,
    );
    await menu.click();
    await panel.getByRole("button", { name: "Check saved connection" }).click();
    await expect(panel.getByText(/Connected to engine/)).toBeVisible();
    await panel
      .getByRole("button", { name: "Close dialog", exact: true })
      .click();
    await panel.screenshot({ path: `evidence/practice-${title}-panel.png` });
    await source.screenshot({ path: `evidence/practice-${title}-source.png` });
    await writeFile(
      path.join(session.folder, title + "-reading.json"),
      JSON.stringify(result),
    );
    receipt.pages.push({
      url,
      passages: result.artifact.regions.length,
      words: result.artifact.regions
        .map((r) => r.anchor.exact)
        .join(" ")
        .split(/\s+/).length,
      events: result.packet.process.nodes.length,
      contributors: result.packet.makers.length,
      seconds: (Date.now() - started) / 1000,
    });
  }
  expect(receipt.errors).toEqual([]);
  receipt.passed = true;
} catch (error) {
  receipt.passed = false;
  receipt.failure = error.message;
  if (session)
    await session.page
      .screenshot({ path: "evidence/practice-failure.png", fullPage: true })
      .catch(() => {});
  throw error;
} finally {
  await writeFile(
    "evidence/practice-validation.json",
    JSON.stringify(receipt, null, 2),
  );
  console.log(JSON.stringify(receipt, null, 2));
  await session?.stop();
  if (session) await session.review.cdp.send("Browser.close").catch(() => {});
  for (const browser of connections) await browser.close().catch(() => {});
}
