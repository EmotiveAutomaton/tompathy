import { test, expect, chromium } from "@playwright/test";
import { mkdtemp, cp, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { sentences } from "../src/core/sentences";

test("fictional reading: independent ink and grade, evidence, scale-aware dots and a timeline", async ({
  page,
}) => {
  await page.addInitScript(() =>
    localStorage.setItem("tompathy-guide-offered-040", "yes"),
  );
  await page.goto("/?demo=fieldnotes");
  await expect(page.locator("h1")).toHaveText("The door we stopped explaining");
  await expect(page.locator("[data-ghost-kind]")).toHaveCount(30);
  await expect(page.locator(".attention-cue")).toHaveText("hover");
  await expect(page.locator(".attention-cue")).toHaveCSS("font-size", "10px");
  await expect(page.locator(".attention-cue")).toHaveCSS("opacity", "0.32");
  await expect(page.locator(".tompathy-emphasis")).toHaveCount(3);
  const edited = page.locator('[data-passage="p3"] [data-sentence="0"]');
  await edited.hover();
  await expect(
    page
      .getByRole("tooltip")
      .filter({ hasText: "Human-written, machine-polished" }),
  ).toBeVisible();
  await expect(page.locator(".tompathy-reading-help")).toContainText(
    "Less · confidence · More",
  );
  await page.keyboard.press("Escape");
  await expect(page.locator(".tompathy-reading-help")).toBeHidden();
  const sameWidth = await edited.evaluate(async (el) => {
    await document.fonts.ready;
    const text = el.querySelector<HTMLElement>(".tompathy-ghost")!;
    const measure = () => {
      const r = document.createRange();
      r.selectNodeContents(text);
      return [...r.getClientRects()].reduce((n, r) => n + r.width, 0);
    };
    const original = text.style.fontVariationSettings;
    text.style.fontVariationSettings = '"GRAD" -50';
    const thin = measure();
    text.style.fontVariationSettings = '"GRAD" 100';
    const thick = measure();
    text.style.fontVariationSettings = original;
    return {
      thin,
      thick,
      font: document.fonts.check('16px "ToMpathy Reading"'),
    };
  });
  expect(sameWidth.font).toBe(true);
  expect(sameWidth.thick).toBeCloseTo(sameWidth.thin, 2);
  await page.locator('[data-passage="p4"] [data-sentence="1"]').focus();
  await expect(page.locator('.spool[data-rank="0"]')).toHaveAttribute(
    "data-selected",
    "sentence-3-2",
  );
  await page.keyboard.press("Enter");
  await expect(page.locator('.spool[data-rank="0"]')).toHaveAttribute(
    "data-selected",
    "sentence-3-2",
  );
  await expect(page.locator(".inline-lock")).toBeVisible();
  await page.keyboard.press("Escape");
  const ghost = page.locator('[data-ghost-kind="ghost"]');
  await ghost.scrollIntoViewIfNeeded();
  await ghost.hover();
  await expect(page.locator(".ghost-prompt")).toHaveCount(0);
  await expect(page.locator(".reading-prompt")).toContainText(
    "Write one upbeat",
  );
  await expect(page.locator(".reading-prompt")).toContainText(
    "Estimated generation prompt",
  );
  await expect(page.locator(".tompathy-reading-help")).toContainText(
    "Unreviewed generation",
  );
  await page.screenshot({ path: "evidence/reading-ghost-preview.png" });
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Reader menu", exact: true }).click();
  await page.getByRole("button", { name: "View context and timeline" }).click();
  await expect(page.getByRole("dialog")).toContainText("First playtest");
  await expect(page.getByRole("dialog")).toContainText(
    "Copy edit and response",
  );
});

test("page treatment preserves inline elements, anchors, edits, keyboard and cleanup", async () => {
  const extension = await mkdtemp(path.resolve(".local/reading-extension-"));
  await cp("dist", extension, { recursive: true });
  const manifest = JSON.parse(
    await readFile(path.join(extension, "manifest.json"), "utf8"),
  );
  manifest.host_permissions = ["http://127.0.0.1/*"];
  await writeFile(
    path.join(extension, "manifest.json"),
    JSON.stringify(manifest),
  );
  const context = await chromium.launchPersistentContext("", {
    headless: true,
    channel: "chromium",
    args: [
      `--disable-extensions-except=${extension}`,
      `--load-extension=${extension}`,
    ],
  });
  try {
    const source = await context.newPage();
    await source.route("**/ghost-fixture", (r) =>
      r.fulfill({
        contentType: "text/html",
        body: '<html><body style="background:#faf9f5;color:#263a32"><article><p id="text" style="opacity:.6">One <strong style="opacity:.5">bold choice</strong> and <a href="#kept">a linked detail</a> remain intact. This claim was curated from suggestions. Nobody reviewed this generated claim.</p></article><aside style="opacity:.4">Unrelated page text.</aside></body></html>',
      }),
    );
    await source.goto("http://127.0.0.1:5173/ghost-fixture");
    await source.evaluate(() => {
      (window as any).originalStrong = document.querySelector("strong");
      (window as any).originalText =
        document.querySelector("#text")!.firstChild;
    });
    const sw =
      context.serviceWorkers()[0] ??
      (await context.waitForEvent("serviceworker"));
    const id = await sw.evaluate(
      async () =>
        (await chrome.tabs.query({})).find((t) =>
          t.url?.endsWith("ghost-fixture"),
        )!.id!,
    );
    await sw.evaluate(
      async (tabId) =>
        chrome.scripting.executeScript({
          target: { tabId },
          files: ["content.js"],
        }),
      id,
    );
    const capture = () =>
      sw.evaluate(
        (tabId) => chrome.tabs.sendMessage(tabId, { type: "TOMPATHY_CAPTURE" }),
        id,
      );
    const { artifact } = await capture(),
      region = artifact.regions[0];
    expect(region.emphasis).toHaveLength(1);
    const readings = sentences(region.anchor.exact).map((s, i) => ({
      maker: "m",
      span: { region: region.id, start: s.start, end: s.end },
      kind: ["edited", "curated", "ghost"][i],
      confidence: [0.9, 0.4, 0.8][i],
      explanation: "Supplied fixture production record.",
      confidenceExplanation: "Fixture confidence.",
      evidence: [],
      ...(i === 2 ? { prompt: "Test prompt" } : {}),
    }));
    const command = (type: string, data = {}) =>
      sw.evaluate(
        ({ tabId, type, data, a }) =>
          chrome.tabs.sendMessage(tabId, {
            type,
            documentId: a.id,
            revision: a.revision,
            ...data,
          }),
        { tabId: id, type, data, a: artifact },
      );
    const mark = () =>
      command("TOMPATHY_MARK", {
        ghostReadings: readings,
        maker: "m",
        origin: "synthetic example",
        evidence: [],
        estimates: [],
      });
    await mark();
    await expect(source.locator("#text")).toHaveCSS("opacity", "1");
    await expect(source.locator("strong")).toHaveCSS("opacity", "1");
    await expect(source.locator("aside")).toHaveCSS("opacity", "0.4");
    await expect(source.locator("strong .tompathy-emphasis")).toHaveCount(1);
    expect(
      await source.evaluate(
        () =>
          document.querySelector("strong") === (window as any).originalStrong,
      ),
    ).toBe(true);
    await source.locator('[data-ghost-kind="curated"]').focus();
    await expect(source.locator(".tompathy-reading-help")).toBeVisible();
    const pageScriptView = await source.evaluate(() => ({
      leaked: document.documentElement.innerHTML.includes("Fixture confidence"),
      attributes: document.querySelectorAll("[data-tompathy-help]").length,
      openRoot: Boolean(
        document.querySelector(".tompathy-reading-help")!.shadowRoot,
      ),
    }));
    expect(pageScriptView).toEqual({
      leaked: false,
      attributes: 0,
      openRoot: false,
    });
    const inspector = await context.newCDPSession(source);
    const accessibility = await inspector.send("Accessibility.getFullAXTree");
    expect(
      accessibility.nodes.map((n) => n.name?.value ?? "").join(" "),
    ).toContain("Curated / synthesized");
    await source.locator('[data-ghost-kind="ghost"]').focus();
    await expect(source.locator(".tompathy-reading-help")).toBeVisible();
    const ghostAX = await inspector.send("Accessibility.getFullAXTree");
    expect(ghostAX.nodes.map((n) => n.name?.value ?? "").join(" ")).toContain(
      "Estimated generation prompt",
    );
    expect(await source.locator("article").textContent()).not.toContain(
      "Test prompt",
    );
    expect(
      await source.evaluate(() =>
        document.documentElement.innerHTML.includes("Test prompt"),
      ),
    ).toBe(false);
    await source.locator('[data-ghost-kind="curated"]').focus();
    await inspector.detach();
    await source.keyboard.press("Enter");
    await expect(
      source.locator('[aria-label="Unlock selection"]'),
    ).toBeVisible();
    const selection = await source.evaluate(() =>
      (CSS as any).highlights
        .get("tompathy-active")
        .values()
        .next()
        .value.toString(),
    );
    expect(selection).toBe("This claim was curated from suggestions.");
    await source.keyboard.press("Escape");
    await command("TOMPATHY_MARK", { estimates: [] });
    await expect(source.locator("[data-tompathy-reading]")).toHaveCount(0);
    await expect(source.locator("#text")).toHaveCSS("opacity", "0.6");
    await expect(source.locator("strong")).toHaveCSS("opacity", "0.5");
    expect(
      await source.evaluate(
        () =>
          document.querySelector("#text")!.firstChild ===
          (window as any).originalText,
      ),
    ).toBe(true);
    await mark();
    await source
      .locator('[data-ghost-kind="curated"]')
      .evaluate(
        (el) => (el.textContent = "An actual page edit must survive cleanup."),
      );
    await expect(source.locator("[data-tompathy-reading]")).toHaveCount(0);
    await expect(source.locator("#text")).toContainText(
      "An actual page edit must survive cleanup.",
    );
    await command("TOMPATHY_CLEANUP");
    await expect(source.locator(".tompathy-reading-help")).toHaveCount(0);
    await expect(source.locator("a")).toHaveAttribute("href", "#kept");
  } finally {
    await context.close();
  }
});
