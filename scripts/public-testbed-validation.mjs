import { chromium } from "@playwright/test";
import { cp, mkdir, readFile, writeFile } from "node:fs/promises";
import assert from "node:assert/strict";
import path from "node:path";
const extension = path.resolve(".local/public-testbed-extension");
await mkdir(extension, { recursive: true });
await cp("dist", extension, { recursive: true });
const urls = [
  "https://simonwillison.net/2022/May/4/datasette-lite/",
  "https://til.simonwillison.net/service-workers/intercept-fetch",
];
const manifest = JSON.parse(
  await readFile(path.join(extension, "manifest.json"), "utf8"),
);
manifest.host_permissions = urls.map((url) => new URL(url).origin + "/*");
await writeFile(
  path.join(extension, "manifest.json"),
  JSON.stringify(manifest),
);
const context = await chromium.launchPersistentContext("", {
  channel: "chromium",
  headless: true,
  args: [
    `--disable-extensions-except=${extension}`,
    `--load-extension=${extension}`,
  ],
});
const receipt = {
  checkedAt: new Date().toISOString(),
  browser: context.browser()?.version(),
  testOnlyHostPermissions: manifest.host_permissions,
  inferenceRequested: false,
  pages: [],
};
try {
  const worker =
    context.serviceWorkers()[0] ??
    (await context.waitForEvent("serviceworker"));
  for (const url of urls) {
    const page = await context.newPage();
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
    const tabId = await worker.evaluate(
      async (url) =>
        (await chrome.tabs.query({})).find((t) => t.url === url)?.id,
      url,
    );
    assert.ok(tabId);
    await worker.evaluate(
      (id) =>
        chrome.scripting.executeScript({
          target: { tabId: id },
          files: ["content.js"],
        }),
      tabId,
    );
    const result = await worker.evaluate(
      (id) => chrome.tabs.sendMessage(id, { type: "TOMPATHY_CAPTURE" }),
      tabId,
    );
    assert.ok(result.artifact, result.error);
    const text = result.artifact.regions.map((r) => r.anchor.exact).join("\n");
    const includedMainContent = /Web Worker|learning service workers/.test(
      text,
    );
    const includedBoilerplate =
      /Sponsor me|Monthly briefing|More recent articles|Adding a robots.txt/.test(
        text,
      );
    receipt.pages.push({
      url,
      passages: result.artifact.regions.length,
      authors: result.artifact.authors,
      capture: result.artifact.capture,
      includedMainContent,
      includedBoilerplate,
    });
    assert.ok(includedMainContent);
    assert.equal(includedBoilerplate, false);
    await page.close();
  }
  await writeFile(
    "evidence/public-testbed-validation.json",
    JSON.stringify(receipt, null, 2),
  );
  console.log(JSON.stringify(receipt, null, 2));
} finally {
  await context.close();
}
