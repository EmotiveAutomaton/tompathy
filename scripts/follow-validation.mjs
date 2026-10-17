import { expect } from "@playwright/test";
import { mkdir, mkdtemp, writeFile } from "node:fs/promises";
import path from "node:path";
import { startPractice } from "./practice-session.mjs";
import { openReview } from "./chrome-review.mjs";

await mkdir("evidence", { recursive: true });
await mkdir(".local", { recursive: true });
const profile = await mkdtemp(path.resolve(".local/follow-check-"));
const connections = [];
const receipt = {
  checkedAt: new Date().toISOString(),
  surface: "Native Chrome side panel with real Python companion",
  checks: [],
  errors: [],
};
let session, panel;
try {
  session = await startPractice({ profile });
  connections.push(session.review.browser);
  Object.assign(receipt, {
    browser: session.review.receipt.chromeVersion,
    build: session.review.receipt.build,
  });
  const context = session.review.browser.contexts()[0];
  // Stable constructed pages for cross-origin and mutation checks. Wikipedia
  // below remains a live network source; these pages are explicitly fixtures.
  for (const host of ["example.com", "example.org"]) {
    await context.route(`https://${host}/**`, (route) =>
      route.fulfill({
        contentType: "text/html",
        body: route.request().url().endsWith("/empty")
          ? "<!doctype html><title>Empty test page</title><body></body>"
          : `<!doctype html><title>Constructed practice article</title><article><h1>Constructed practice article</h1><p>This short article is original test text for page following on ${host}. A writer changed a path description after walking through the park.</p><p>The page offers final text without any recorded drafting history. Its capture must not create a claim about the writer's motives.</p></article>`,
      }),
    );
  }
  receipt.fixturePages = ["https://example.com/", "https://example.org/"];
  const guide = session.page;
  const id = session.review.receipt.extensionId;
  const source = await context.newPage();
  await source.goto("chrome://version/");
  await source.bringToFront();
  const targets = await session.review.cdp.send("Target.getTargets", {
    filter: [{ type: "tab" }],
  });
  await session.review.cdp.send("Extensions.triggerAction", {
    id,
    targetId: targets.targetInfos.find((t) => t.url === source.url()).targetId,
  });
  const attached = await openReview({ profile, showGuide: false });
  connections.push(attached.browser);
  panel = attached.browser
    .contexts()[0]
    .pages()
    .find((p) => p.url().includes("/panel.html"));
  if (!panel) throw Error("Native side panel did not open");
  panel.on("pageerror", (e) => receipt.errors.push(e.message));
  const reading = () =>
    panel.evaluate(
      async () => (await chrome.storage.session.get("reading")).reading,
    );
  await expect(
    panel.getByRole("heading", { name: "We couldn’t read this page" }),
  ).toBeVisible();
  await expect(
    panel.getByRole("button", { name: "Try the safe example" }),
  ).toBeVisible();
  await panel.screenshot({ path: "evidence/follow-protected.png" });
  const center = await panel.locator("#values-view").evaluate((el) => {
    const outer = el.getBoundingClientRect(),
      empty = el.querySelector(".quiet-empty").getBoundingClientRect();
    return {
      x: Math.abs((outer.left + outer.right - empty.left - empty.right) / 2),
      y: Math.abs((outer.top + outer.bottom - empty.top - empty.bottom) / 2),
    };
  });
  expect(center.x).toBeLessThan(3);
  expect(center.y).toBeLessThan(3);
  receipt.checks.push(
    "Protected page offers safe example and paste; empty values centered",
  );
  await panel.getByRole("button", { name: "Try the safe example" }).click();
  await expect
    .poll(async () => (await reading())?.packet?.origin)
    .toBe("synthetic example");
  receipt.checks.push(
    "Bundled safe example opens without internet or an engine",
  );
  // The native permission prompt cannot be clicked through a page target.
  // Use Chrome's own extension-settings API, then exercise the real opt-in UI.
  const settings = await context.newPage();
  await settings.goto("chrome://extensions/");
  await settings.evaluate(async (id) => {
    for (const origin of ["http://*/*", "https://*/*"])
      await chrome.developerPrivate.addHostPermission(id, origin);
  }, id);
  await settings.close();
  await guide.bringToFront();
  await guide.getByRole("button", { name: /Connect local engine/ }).click();
  await expect(guide.locator("#connection")).toContainText(
    "Connected to engine",
  );
  await guide.getByRole("button", { name: /Enable Follow pages/ }).click();
  await expect(guide.locator("#following")).toContainText("Follow pages is on");
  for (const url of [
    "https://example.com/",
    "https://en.wikipedia.org/wiki/Sneckdown",
  ]) {
    await source.bringToFront();
    await source.goto(url);
    await expect
      .poll(async () => (await reading())?.packet?.artifact.source, {
        timeout: 90000,
      })
      .toBe(url);
    const result = await reading();
    expect(result.packet.provider.id).toBe("tompathy-engine");
    expect(result.packet.artifact).toEqual(result.artifact);
    expect(result.packet.provider.admissions).toEqual([]);
    if (url.includes("wikipedia"))
      expect(result.packet.process.nodes.length).toBeGreaterThan(1);
    await expect(panel.getByLabel("Live engine reading")).toBeVisible();
    await panel.screenshot({
      path: `evidence/follow-${url.includes("wikipedia") ? "history" : "capture"}.png`,
    });
    receipt.checks.push(
      `Automatic capture and real engine reading across navigation (${url.includes("wikipedia") ? "live source" : "constructed source"}): ${url}`,
    );
  }
  // A new active tab must also follow without another toolbar gesture.
  const next = await context.newPage();
  await next.goto("https://example.org/");
  await next.bringToFront();
  await expect
    .poll(async () => (await reading())?.packet?.artifact.source, {
      timeout: 20000,
    })
    .toBe("https://example.org/");
  receipt.checks.push("New active tab followed without toolbar click");
  const originalRevision = (await reading()).artifact.revision;
  await next.locator("h1").evaluate((el) => {
    el.textContent = "Constructed live-update check";
  });
  await expect
    .poll(
      async () => {
        const result = await reading();
        return (
          !!result?.packet &&
          result.packet.artifact.revision !== originalRevision
        );
      },
      {
        timeout: 15000,
      },
    )
    .toBe(true);
  expect((await reading()).packet.artifact).toEqual((await reading()).artifact);
  receipt.checks.push(
    "Visible text changes recapture and analyze an exact new revision",
  );
  let release,
    intercepted = false;
  const pending = new Promise((resolve) => {
    release = resolve;
  });
  await panel.route(session.url + "/v1/analyze", async (route) => {
    if (
      route.request().postDataJSON().artifact.source.endsWith("?slow-reading")
    ) {
      intercepted = true;
      await pending;
    }
    await route.continue().catch(() => {});
  });
  try {
    await next.goto("https://example.com/?slow-reading");
    await expect.poll(() => intercepted).toBe(true);
    const cancelled = panel.waitForRequest(
      (r) => r.method() === "DELETE" && r.url().startsWith(session.url),
    );
    await next.goto("https://example.org/?new-reading");
    await cancelled;
    await expect
      .poll(async () => (await reading())?.packet?.artifact.source, {
        timeout: 15000,
      })
      .toBe("https://example.org/?new-reading");
    receipt.checks.push(
      "Navigation cancels the pending old reading; only the new capture is displayed",
    );
  } finally {
    release();
    await panel.unroute(session.url + "/v1/analyze");
  }
  await session.stop();
  await next.goto("https://example.com/?offline-check");
  await expect(
    panel.getByRole("heading", { name: "The engine is offline" }),
  ).toBeVisible();
  await expect(
    panel.getByRole("button", { name: "Retry reading" }),
  ).toBeVisible();
  await expect(
    panel.getByRole("button", { name: "Open engine setup" }),
  ).toBeVisible();
  expect((await reading()).artifact.source).toBe(
    "https://example.com/?offline-check",
  );
  expect((await reading()).packet).toBeNull();
  await panel.screenshot({ path: "evidence/follow-offline.png" });
  receipt.checks.push(
    "Stopped engine explains recovery and preserves captured text",
  );
  await panel.getByRole("button", { name: "Reader menu", exact: true }).click();
  await panel
    .getByRole("checkbox", { name: "Automatically read new pages" })
    .uncheck();
  await panel
    .getByRole("button", { name: "Close dialog", exact: true })
    .click();
  await next.goto("https://example.org/?manual-check");
  await expect(
    panel.getByRole("heading", { name: "Ready for an account" }),
  ).toBeVisible();
  await expect(
    panel.getByRole("button", { name: "Analyze capture", exact: true }),
  ).toBeEnabled();
  receipt.checks.push(
    "Follow can be disabled; manual reading remains available",
  );
  await next.goto("https://example.org/empty");
  await expect(
    panel.getByRole("heading", { name: "Start with a piece of writing" }),
  ).toBeVisible();
  await panel.screenshot({ path: "evidence/follow-empty.png" });
  receipt.checks.push("Readable but empty webpage has a quiet starting state");
  expect(receipt.errors).toEqual([]);
  receipt.passed = true;
} catch (error) {
  receipt.passed = false;
  receipt.failure = error.message;
  await panel
    ?.screenshot({ path: "evidence/follow-failure.png" })
    .catch(() => {});
  throw error;
} finally {
  await writeFile(
    "evidence/follow-validation.json",
    JSON.stringify(receipt, null, 2),
  );
  console.log(JSON.stringify(receipt, null, 2));
  await session?.stop();
  await session?.review.cdp.send("Browser.close").catch(() => {});
  for (const browser of connections) await browser.close().catch(() => {});
}
