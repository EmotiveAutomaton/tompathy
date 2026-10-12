import { test, expect, chromium } from "@playwright/test";
import { cp, mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { matchPacket, parsePacket } from "../src/core/model";
test("installed page adapter: anchors, dynamic revision, cleanup and long-page latency", async () => {
  await mkdir("evidence", { recursive: true });
  const root = path.resolve(".local/extension-test");
  await mkdir(root, { recursive: true });
  await cp("dist", root, { recursive: true });
  const manifest = JSON.parse(
    await readFile(path.join(root, "manifest.json"), "utf8"),
  );
  manifest.host_permissions = ["http://127.0.0.1/*"];
  await writeFile(path.join(root, "manifest.json"), JSON.stringify(manifest));
  const context = await chromium.launchPersistentContext("", {
    channel: "chromium",
    headless: true,
    args: [`--disable-extensions-except=${root}`, `--load-extension=${root}`],
  });
  try {
    const sw =
      context.serviceWorkers()[0] ??
      (await context.waitForEvent("serviceworker"));
    const source = await context.newPage();
    await source.goto("http://127.0.0.1:5173/fixture.html");
    const id = await sw.evaluate(async () => {
      const tabs = await chrome.tabs.query({});
      return tabs.find((t) => t.url?.includes("/fixture.html"))!.id!;
    });
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
    const result = await capture();
    expect(result.artifact.regions).toHaveLength(6);
    const joined = result.artifact.regions
      .map((r: any) => r.anchor.exact)
      .join(" ");
    expect(joined).toContain("inline text with café, 世界");
    expect(joined).not.toMatch(
      /Hidden material|Editable draft|Navigation must|Decorative hidden/,
    );
    const repeated = result.artifact.regions.filter(
      (r: any) => r.anchor.exact === "This passage repeats exactly.",
    );
    expect(repeated).toHaveLength(2);
    expect(repeated[0].anchor.start).not.toEqual(repeated[1].anchor.start);
    const command = (type: string, data = {}) =>
      sw.evaluate(
        ({ tabId, type, a, data }) =>
          chrome.tabs.sendMessage(tabId, {
            type,
            documentId: a.id,
            revision: a.revision,
            ...data,
          }),
        { tabId: id, type, a: result.artifact, data },
      );
    const drag = await source.locator("#repeat1").evaluate((el) => {
      const range = document.createRange();
      range.setStart(el.firstChild!, 1);
      range.setEnd(el.firstChild!, 20);
      const rect = range.getBoundingClientRect();
      return { x: rect.x, y: rect.y + rect.height / 2, right: rect.right };
    });
    await source.mouse.move(drag.x, drag.y);
    await source.mouse.down();
    await source.mouse.move(drag.right, drag.y, { steps: 5 });
    await source.mouse.up();
    expect(
      await source.evaluate(() => window.getSelection()?.toString().length),
    ).toBeGreaterThan(5);
    await expect(
      source.locator('[aria-label="Unlock selection"]'),
    ).toBeHidden();
    await source.locator("#repeat2").click();
    await expect(
      source.locator('[aria-label="Unlock selection"]'),
    ).toBeVisible();
    await source.locator("h1").dblclick();
    await expect(
      source.locator('[aria-label="Unlock selection"]'),
    ).toBeHidden();
    await source.locator("#repeat2").click();
    await source.keyboard.press("Escape");
    await expect(
      source.locator('[aria-label="Unlock selection"]'),
    ).toBeHidden();
    await command("TOMPATHY_FOCUS", { region: repeated[1].id });
    await expect(source.locator("#repeat2")).toHaveAttribute(
      "data-tompathy-selected",
      "",
    );
    await expect(source.locator("#repeat1")).not.toHaveAttribute(
      "data-tompathy-selected",
    );
    await source.locator("a").click();
    await expect(source).toHaveURL(/#destination$/);
    await source.getByRole("button", { name: "Change the document" }).click();
    await expect(source.locator("[data-tompathy-selected]")).toHaveCount(0);
    const changed = await capture();
    expect(changed.artifact.revision).not.toEqual(result.artifact.revision);
    await source.getByRole("button", { name: "Make long page" }).click();
    const t = Date.now();
    const long = await capture();
    const captureMs = Date.now() - t;
    expect(long.artifact.regions).toHaveLength(1006);
    const samples: number[] = [];
    for (let i = 0; i < 12; i++) {
      const elapsed = await source.evaluate(async (i) => {
        const elements = document.querySelectorAll("main>p");
        const target = elements[20 + i] as HTMLElement;
        target.scrollIntoView({ block: "center" });
        const range = document.createRange();
        range.selectNodeContents(target);
        const rect = range.getClientRects()[0];
        const start = performance.now();
        target.dispatchEvent(
          new PointerEvent("pointermove", {
            bubbles: true,
            clientX: rect.left + 12,
            clientY: rect.top + rect.height / 2,
          }),
        );
        await new Promise(requestAnimationFrame);
        if (!target.hasAttribute("data-tompathy-selected"))
          throw Error("Long-page sentence selection did not run");
        if (!(CSS as any).highlights.get("tompathy-active")?.size)
          throw Error("Sentence highlight was not painted");
        return performance.now() - start;
      }, i);
      samples.push(elapsed);
    }
    const frames = await source.evaluate(async () => {
      const s: number[] = [];
      let last = performance.now();
      for (let i = 0; i < 60; i++) {
        await new Promise(requestAnimationFrame);
        const now = performance.now();
        s.push(now - last);
        last = now;
      }
      return s;
    });
    await writeFile(
      "evidence/performance.json",
      JSON.stringify(
        {
          browser: context.browser()?.version(),
          passages: 1006,
          captureMs,
          hoverToNextPaintMs: samples,
          frameIntervalsMs: frames,
          scope:
            "Content-script selection on a controlled long page; headed/native panel response checked separately.",
        },
        null,
        2,
      ),
    );
    expect(Math.max(...samples)).toBeLessThan(100);
    await sw.evaluate(
      (tabId) => chrome.tabs.sendMessage(tabId, { type: "TOMPATHY_CLEANUP" }),
      id,
    );
    await source.locator("#repeat1").hover();
    await expect(source.locator("[data-tompathy-selected]")).toHaveCount(0);
    await source.goto("http://127.0.0.1:5173/testbed.html");
    const install = () =>
      sw.evaluate(
        async (tabId) =>
          chrome.scripting.executeScript({
            target: { tabId },
            files: ["content.js"],
          }),
        id,
      );
    await install();
    const testbed = await capture();
    const fixture = parsePacket(
      await readFile("public/testbed-result.json", "utf8"),
    );
    expect(testbed.artifact.authors).toEqual([
      { label: "The garden designer", basis: "page-metadata" },
    ]);
    expect(matchPacket(fixture, testbed.artifact, "artifact", [])).toBeNull();
    expect(testbed.artifact.regions).toHaveLength(6);
    await source.setContent(
      `<meta name="author" content="Fixture Author"><nav><p>Navigation not part of this article.</p></nav><div class="entry entryPage"><div><h1>A legacy blog article</h1><p>The author's actual article paragraph with useful content.</p></div><div class="entryFooter"><p>Subscribe to our unrelated newsletter.</p></div></div><div class="recent-articles"><p>More recent articles and promotional links.</p></div>`,
    );
    await install();
    const legacy = await capture();
    expect(legacy.artifact.regions).toHaveLength(2);
    expect(legacy.artifact.capture.method).toBe("content-container");
    expect(legacy.artifact.authors[0].label).toBe("Fixture Author");
    expect(
      legacy.artifact.regions.map((r: any) => r.anchor.exact).join(" "),
    ).not.toMatch(/Subscribe|promotional|Navigation/);
  } finally {
    await context.close();
  }
});
