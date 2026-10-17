import { expect } from "@playwright/test";
import { mkdir, mkdtemp, writeFile } from "node:fs/promises";
import path from "node:path";
import { openReview } from "./chrome-review.mjs";

await mkdir("evidence", { recursive: true });
await mkdir(".local", { recursive: true });
const profile = await mkdtemp(path.resolve(".local/context-stability-"));
const connections = [];
const receipt = {
  checkedAt: new Date().toISOString(),
  surface: "Native Chrome side panel",
  checks: [],
  errors: [],
  liveGitHub:
    "https://github.com/EmotiveAutomaton/tompathy/blob/main/README.md",
};
let review, panel;
try {
  review = await openReview({ profile, showGuide: false });
  connections.push(review.browser);
  Object.assign(receipt, {
    browser: review.receipt.chromeVersion,
    build: review.receipt.build,
  });
  const context = review.browser.contexts()[0];
  await context.route("https://example.com/**", (route) =>
    route.fulfill({
      contentType: "text/html",
      body: `<!doctype html><meta name="author" content="${route.request().url().endsWith("/second") ? "Second Reviewer" : "Constructed Reviewer"}"><title>Constructed context audit</title><article><h1>Constructed context audit</h1><p>Original fixture text for testing automatic source collection. It makes no claim about the author of the public repository.</p>${route.request().url().endsWith("/second") ? "" : `<p><a rel="author" href="https://example.org/about">Constructed Reviewer</a> · <a rel="author" href="https://example.net/about">Constructed Reviewer</a></p><p><a href="${receipt.liveGitHub}">Source repository</a></p>`}</article>`,
    }),
  );
  await context.route("https://example.org/about", (route) =>
    route.fulfill({
      contentType: "text/plain",
      body: "An original constructed profile for the context stability check.",
    }),
  );
  const settings = await context.newPage();
  await settings.goto("chrome://extensions/");
  const grant = async (origins) =>
    settings.evaluate(
      async ({ id, origins }) => {
        for (const origin of origins)
          await chrome.developerPrivate.addHostPermission(id, origin);
      },
      { id: review.receipt.extensionId, origins },
    );
  await grant(["https://example.org/*", "https://api.github.com/*"]);
  const source = await context.newPage();
  await source.goto("https://example.com/first");
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
  // The native panel is discovered on the second CDP attachment, so route its
  // constructed source on that context as well. GitHub remains a live request.
  await panel.context().route("https://example.org/about", (route) =>
    route.fulfill({
      contentType: "text/plain",
      body: "An original constructed profile for the context stability check.",
    }),
  );
  panel.on("pageerror", (e) => receipt.errors.push(e.message));
  receipt.responses = [];
  panel.on("response", (response) => {
    if (response.url().startsWith("https://api.github.com/"))
      receipt.responses.push({
        url: response.url(),
        status: response.status(),
      });
  });
  // Runtime host access and the extension's optional grant are separate Chrome
  // states. Complete the preapproved grant before testing automatic retrieval.
  const granted = await panel.evaluate(() =>
    Promise.race([
      chrome.permissions.request({
        origins: ["https://example.org/*", "https://api.github.com/*"],
      }),
      new Promise((resolve) => setTimeout(() => resolve(false), 10000)),
    ]),
  );
  expect(granted).toBe(true);
  await panel.evaluate(() => {
    localStorage.setItem("tompathy-context-enabled", "true");
    localStorage.setItem("tompathy-use-github", "true");
  });
  await panel.reload();
  receipt.permissions = await panel.evaluate(() => chrome.permissions.getAll());
  const reading = () =>
    panel.evaluate(
      async () => (await chrome.storage.session.get("reading")).reading,
    );
  await expect
    .poll(
      async () =>
        (await reading())?.context?.some(
          (c) =>
            c.source === receipt.liveGitHub &&
            c.facts?.some((f) => f.label.startsWith("File revision")),
        ),
      { timeout: 35000 },
    )
    .toBe(true);
  const first = await reading();
  expect(
    first.context.some((c) => c.source === "https://example.org/about"),
  ).toBe(true);
  expect(
    first.context.some((c) => c.source === "https://example.net/about"),
  ).toBe(false);
  expect(first.context.every((c) => !c.selected)).toBe(true);
  receipt.checks.push(
    "Saved Light context automatically retrieves an allowed source and actual public GitHub file/revision metadata; ungranted source does not block them",
  );
  await panel.getByRole("button", { name: "Reader menu", exact: true }).click();
  await panel
    .getByRole("button", { name: "View context and timeline" })
    .click();
  await panel.getByText("Collection coverage", { exact: true }).click();
  await expect(panel.getByRole("dialog")).toContainText(
    "Source access has not been granted",
  );
  await expect(panel.getByRole("dialog")).toContainText("File revision");
  await panel.screenshot({ path: "evidence/stability-native-context.png" });
  const githubItem = first.context.find((c) => c.source === receipt.liveGitHub);
  receipt.githubFacts = githubItem.facts.map((f) => ({
    label: f.label,
    date: f.date,
    dateKind: f.dateKind,
  }));
  await panel
    .getByRole("button", { name: "Close dialog", exact: true })
    .click();
  await source.bringToFront();
  await review.cdp.send("Extensions.triggerAction", {
    id: review.receipt.extensionId,
    targetId: targets.targetInfos.find((t) => t.url === source.url()).targetId,
  });
  await expect
    .poll(async () => (await reading())?.artifact?.capturedAt)
    .not.toBe(first.artifact.capturedAt);
  await expect
    .poll(async () =>
      (await reading())?.context?.some((c) => c.id === githubItem.id),
    )
    .toBe(true);
  await expect
    .poll(async () => (await reading())?.artifact?.revision)
    .toBe(first.artifact.revision);
  receipt.checks.push(
    "Recapturing the same revision retains retrieved context",
  );
  await grant(["https://*/*", "http://*/*"]);
  await panel.getByRole("button", { name: "Reader menu", exact: true }).click();
  await panel
    .getByRole("checkbox", { name: "Automatically read new pages" })
    .click();
  await expect(
    panel.getByRole("checkbox", { name: "Automatically read new pages" }),
  ).toBeChecked();
  await panel
    .getByRole("button", { name: "Close dialog", exact: true })
    .click();
  await source.bringToFront();
  await source.goto("https://example.com/second");
  await expect
    .poll(async () =>
      (await reading())?.context?.some(
        (c) => c.provenance?.author === "Second Reviewer",
      ),
    )
    .toBe(true);
  const second = await reading();
  expect(second.context.some((c) => c.source === receipt.liveGitHub)).toBe(
    false,
  );
  expect(second.context.every((c) => !c.selected)).toBe(true);
  receipt.checks.push(
    "Following a new page automatically refreshes context for its byline; previous creator context is not carried over",
  );
  expect(receipt.errors).toEqual([]);
  receipt.passed = true;
} catch (error) {
  receipt.passed = false;
  receipt.failure = error.message;
  receipt.diagnostic = await panel
    ?.evaluate(async () => {
      const reading = (await chrome.storage.session.get("reading")).reading;
      return {
        enabled: localStorage.getItem("tompathy-context-enabled"),
        sources: reading?.contextSources,
        repositories: reading?.repositoryLinks,
        context: reading?.context?.map((c) => ({
          source: c.source,
          facts: c.facts?.map((f) => f.label),
        })),
        status: document
          .querySelector(".context-progress")
          ?.getAttribute("aria-label"),
      };
    })
    .catch(() => null);
  await panel
    ?.getByRole("button", { name: "Reader menu", exact: true })
    .click()
    .catch(() => {});
  await panel
    ?.getByRole("button", { name: "View context and timeline" })
    .click()
    .catch(() => {});
  receipt.coverage = await panel
    ?.locator(".context-timeline")
    .innerText()
    .catch(() => null);
  await panel
    ?.screenshot({ path: "evidence/stability-native-context-failure.png" })
    .catch(() => {});
  throw error;
} finally {
  await writeFile(
    "evidence/context-stability-validation.json",
    JSON.stringify(receipt, null, 2),
  );
  console.log(JSON.stringify(receipt, null, 2));
  await review?.cdp.send("Browser.close").catch(() => {});
  for (const browser of connections) await browser.close().catch(() => {});
}
