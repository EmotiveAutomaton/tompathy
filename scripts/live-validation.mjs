import { chromium, expect } from "@playwright/test";
import { cp, mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
const dir = path.resolve(".local/live-extension");
await mkdir(dir, { recursive: true });
await cp("dist", dir, { recursive: true });
const manifest = JSON.parse(
  await readFile(path.join(dir, "manifest.json"), "utf8"),
);
const urls = [
  "https://example.com/",
  "https://www.w3.org/Provider/Style/URI",
  "https://en.wikipedia.org/wiki/Bench_(furniture)",
];
manifest.host_permissions = urls.map((s) => new URL(s).origin + "/*");
await writeFile(path.join(dir, "manifest.json"), JSON.stringify(manifest));
const context = await chromium.launchPersistentContext("", {
  channel: "chromium",
  headless: true,
  args: [`--disable-extensions-except=${dir}`, `--load-extension=${dir}`],
});
const receipts = [];
try {
  const sw =
    context.serviceWorkers()[0] ??
    (await context.waitForEvent("serviceworker"));
  for (const url of urls) {
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    try {
      await page.goto(url, { waitUntil: "domcontentloaded", timeout: 25000 });
      const id = await sw.evaluate(async (url) => {
        const ts = await chrome.tabs.query({});
        return ts.find((t) => t.url?.startsWith(new URL(url).origin))?.id;
      }, url);
      if (!id) throw Error("Tab not available");
      await sw.evaluate(
        (tabId) =>
          chrome.scripting.executeScript({
            target: { tabId },
            files: ["content.js"],
          }),
        id,
      );
      const result = await sw.evaluate(
        (tabId) => chrome.tabs.sendMessage(tabId, { type: "TOMPATHY_CAPTURE" }),
        id,
      );
      receipts.push({
        url,
        loadedURL: page.url(),
        title: await page.title(),
        passages: result.artifact?.regions.length,
        preview: result.artifact?.regions[0]?.anchor.exact.slice(0, 160),
        error: result.error,
        errors,
      });
    } catch (e) {
      receipts.push({ url, error: e.message });
    }
    await page.close();
  }
  const panel = await context.newPage();
  await panel.goto(`chrome-extension://${sw.url().split("/")[2]}/panel.html`);
  await panel.getByRole("button", { name: "Reader menu", exact: true }).click();
  await panel.getByRole("button", { name: "Context", exact: true }).click();
  await panel.getByText("Retrieve public sources", { exact: true }).click();
  await panel.getByLabel("URLs, one per line").fill("https://example.com/");
  await panel.getByRole("button", { name: "Collect selected sources" }).click();
  await expect(panel.locator(".context-item")).toContainText("Example Domain", {
    timeout: 30000,
  });
  receipts.push({
    collector: "https://example.com/",
    result: await panel.locator(".context-item").innerText(),
    claimsGenerated: await panel.getByTestId("values").innerText(),
  });
  await panel
    .getByLabel("URLs, one per line")
    .fill("https://example.com/tompathy-missing");
  await panel.getByRole("button", { name: "Collect selected sources" }).click();
  await expect(panel.getByRole("dialog")).toContainText("404", {
    timeout: 30000,
  });
  receipts.push({ collectorFailure: "404 displayed without inference" });
  await writeFile(
    "evidence/live-validation.json",
    JSON.stringify(
      {
        browser: context.browser()?.version(),
        testManifestExtraPermissions: manifest.host_permissions,
        receipts,
      },
      null,
      2,
    ),
  );
  console.log(JSON.stringify(receipts, null, 2));
} finally {
  await context.close();
}
