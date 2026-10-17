import { expect } from "@playwright/test";
import { mkdtemp, mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { openReview } from "./chrome-review.mjs";
await mkdir(".local", { recursive: true });
await mkdir("evidence", { recursive: true });
const profile = await mkdtemp(path.resolve(".local/website-check-"));
let current;
const connections = [];
const receipt = {
  checkedAt: new Date().toISOString(),
  checks: [],
  pages: [],
  errors: [],
};
try {
  current = await openReview({ profile });
  connections.push(current.browser);
  receipt.browser = current.receipt.chromeVersion;
  receipt.build = current.receipt.build;
  let context = current.browser.contexts()[0];
  const guide = context
    .pages()
    .find((p) => p.url() === current.receipt.reviewUrl);
  // This retained check exercises the legacy commissioned frontend explicitly.
  // The default research preview is verified separately with actual engine runs.
  await guide.evaluate(() => localStorage.setItem("tompathy-research-preview", "false"));
  await expect(
    guide.getByRole("link", { name: /Open the live essay/ }),
  ).toHaveAttribute("href", "https://abrahamhaskins.org/art/");
  await expect(
    guide.getByRole("link", { name: /Open the live homepage/ }),
  ).toHaveAttribute("href", "https://abrahamhaskins.org/");
  const source = await context.newPage();
  for (const kind of ["art", "home"]) {
    const url = `https://abrahamhaskins.org/${kind === "art" ? "art/" : ""}`;
    await source.goto(url, { waitUntil: "domcontentloaded" });
    await source.locator("h1").first().waitFor();
    if (kind === "art")
      await source.locator(".katex").first().waitFor({ state: "attached" });
    await source.bringToFront();
    const targets = await current.cdp.send("Target.getTargets", {
      filter: [{ type: "tab" }],
    });
    const tab = targets.targetInfos.find((t) => t.url === source.url());
    await current.cdp.send("Extensions.triggerAction", {
      id: current.receipt.extensionId,
      targetId: tab.targetId,
    });
    current = await openReview({ profile, showGuide: false });
    connections.push(current.browser);
    context = current.browser.contexts()[0];
    const panel = context.pages().find((p) => p.url().includes("/panel.html"));
    if (!panel) throw Error("Native side panel did not open");
    panel.on("pageerror", (e) => receipt.errors.push(e.message));
    const reading = () =>
      panel.evaluate(
        async () => (await chrome.storage.session.get("reading")).reading,
      );
    await expect
      .poll(async () => (await reading())?.artifact?.source, { timeout: 20000 })
      .toBe(url);
    await expect
      .poll(async () => (await reading())?.packet?.provider?.id, {
        timeout: 20000,
      })
      .toMatch(/tompathy-(art|website)-demo/);
    await expect(panel.locator(".pyramid-node")).not.toHaveCount(0);
    let session = await reading();
    const counts = (s) => ({
      regions: s.artifact.regions.length,
      sentences: s.packet.goalHierarchy.nodes.filter((n) => n.span).length,
      method: s.packet.provider.method,
      peaks: s.packet.goalHierarchy.nodes
        .filter((n) => !n.parentId && !n.parentIds)
        .map((n) => n.label),
    });
    console.log(kind, counts(session));
    await writeFile(
      `.local/${kind}-native-reading.json`,
      JSON.stringify(session),
    );
    expect(session.packet.artifact.revision).toBe(session.artifact.revision);
    expect(
      session.packet.hypotheses.filter((h) => h.valueCategory === "drive"),
    ).toHaveLength(7);
    expect(
      session.packet.hypotheses
        .filter((h) => h.kind === "value")
        .every((h) => h.preferenceTrace),
    ).toBe(true);
    await expect(panel.locator(".core-value-row")).toHaveCount(10);
    await expect(
      panel.getByRole("tab", { name: "current work only", exact: true }),
    ).toHaveAttribute("aria-selected", "true");
    const workScore = await panel
      .getByRole("button", { name: "Drive SEEKING", exact: true })
      .evaluate((el) => getComputedStyle(el).fontWeight);
    await panel.getByRole("tab", { name: "creator", exact: true }).click();
    expect(
      await panel
        .getByRole("button", { name: "Drive SEEKING", exact: true })
        .evaluate((el) => getComputedStyle(el).fontWeight),
    ).not.toBe(workScore);
    await panel
      .getByRole("tab", { name: "current work only", exact: true })
      .click();
    if (kind === "art") {
      const originalRevision = session.artifact.revision;
      for (let i = 0; i < 3; i++) {
        await source.locator(".citation-trigger").first().hover();
        await expect(source.locator(".citation-tooltip-portal")).toBeVisible();
        await source.waitForTimeout(450);
        expect((await reading()).artifact.revision).toBe(originalRevision);
        await expect(source.locator("[data-tompathy-reading]")).not.toHaveCount(
          0,
        );
        await source.mouse.move(5, 200);
        await source.waitForTimeout(300);
      }
      await expect(panel.getByRole("alert")).toHaveCount(0);
      await expect(
        panel.getByRole("button", { name: "Reload reading" }),
      ).toHaveCount(0);
      receipt.checks.push(
        "Citation hover leaves capture and annotation intact; the extra Reload control is absent",
      );
    }
    const first = source
      .locator("[data-tompathy-reading]")
      .filter({
        hasText:
          kind === "art"
            ? "My name is Abraham Haskins."
            : "Building resilient systems",
      })
      .first();
    await first.click();
    await expect(panel.locator(".process-lock")).toBeVisible();
    await expect(panel.locator(".pyramid-node.chosen")).toHaveCount(1);
    const node = await panel
      .locator(".pyramid-node.chosen")
      .getAttribute("data-node");
    await panel.locator(".pyramid-node.chosen").press("ArrowRight");
    await expect(panel.locator(".pyramid-node.chosen")).not.toHaveAttribute(
      "data-node",
      node,
    );
    const separator = panel.getByRole("separator").nth(1);
    const before = Number(await separator.getAttribute("data-x"));
    await separator.focus();
    await separator.press("ArrowLeft");
    expect(Number(await separator.getAttribute("data-x"))).toBeLessThan(before);
    const selectedBefore = await panel
      .locator(".pyramid-node.chosen")
      .getAttribute("data-node");
    const hit = separator.locator(".tier-divider-hit");
    const box = await hit.boundingBox();
    await panel.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await panel.mouse.down();
    await panel.mouse.move(box.x + box.width / 2 + 16, box.y + box.height / 2, {
      steps: 5,
    });
    await panel.mouse.up();
    expect(Number(await separator.getAttribute("data-x"))).toBeGreaterThan(
      before - 4,
    );
    await expect(panel.locator(".pyramid-node.chosen")).toHaveAttribute(
      "data-node",
      selectedBefore,
    );
    await panel.getByRole("tab", { name: "global", exact: true }).click();
    await expect(panel.locator(".core-value-row")).toHaveCount(25);
    await panel.getByRole("tab", { name: "creator", exact: true }).click();
    await panel.mouse.move(5, 5);
    await panel.screenshot({
      path: `evidence/website-${kind}-overview.png`,
      scale: "css",
    });
    await panel.locator(".core-value-row").first().hover();
    await expect(panel.locator(".hover-card .preference-chart")).toBeVisible();
    await expect(panel.locator(".hover-card .support-wheel")).toHaveCount(0);
    await expect(panel.locator(".hover-card .drive-brain")).toBeVisible();
    await expect(
      panel.locator(".hover-card .value-confidence-number"),
    ).toContainText("%");
    await panel.screenshot({
      path: `evidence/website-${kind}-panel.png`,
      scale: "css",
    });
    await source.screenshot({
      path: `evidence/website-${kind}-page.png`,
      scale: "css",
    });
    if (kind === "art") {
      const closed = source.locator("details.art-collapsible").first();
      const old = session.artifact.regions.length;
      await closed.locator("summary").click();
      await expect
        .poll(async () => (await reading())?.artifact?.regions?.length, {
          timeout: 20000,
        })
        .toBeGreaterThan(old);
      await expect
        .poll(
          async () =>
            (await reading())?.packet?.goalHierarchy?.nodes?.filter(
              (n) => n.span,
            ).length,
          { timeout: 20000 },
        )
        .toBeGreaterThan(counts(session).sentences);
      session = await reading();
      await writeFile(
        ".local/art-expanded-reading.json",
        JSON.stringify(session),
      );
      const paragraph = closed
        .locator("[data-tompathy-reading]")
        .filter({ hasText: "Marcel Duchamp" })
        .first();
      await paragraph.click();
      await expect(panel.locator(".pyramid-node.chosen")).toHaveAttribute(
        "aria-label",
        /Fountain/,
      );
      receipt.checks.push(
        "Expanding the live essay automatically recaptures and analyzes the newly visible sentences",
      );
      // Open all five substantive asides, then check exact span coverage. Math
      // stays rendered by the site and is deliberately excluded from prose.
      for (let i = 1; i < 5; i++) {
        const beforeRevision = (await reading()).artifact.revision;
        await source
          .locator("details.art-collapsible")
          .nth(i)
          .locator("summary")
          .click();
        await expect
          .poll(async () => (await reading()).artifact.revision, {
            timeout: 20000,
          })
          .not.toBe(beforeRevision);
      }
      session = await reading();
      const segmenter = new Intl.Segmenter("en", { granularity: "sentence" });
      const expectedCount = session.artifact.regions.reduce(
        (count, r) =>
          count +
          (r.pageHint?.unit === "group"
            ? 1
            : [...segmenter.segment(r.anchor.exact)].filter((s) =>
                s.segment.trim(),
              ).length),
        0,
      );
      expect(counts(session).sentences).toBe(expectedCount);
      expect(
        new Set(
          session.packet.goalHierarchy.nodes
            .filter((n) => n.span)
            .map((n) => `${n.span.region}:${n.span.start}:${n.span.end}`),
        ).size,
      ).toBe(expectedCount);
      console.log("art fully expanded", counts(session));
      await writeFile(
        ".local/art-fully-expanded-reading.json",
        JSON.stringify(session),
      );
      const sample = source
        .locator("[data-tompathy-reading]")
        .filter({ hasText: "My name is Abraham Haskins." })
        .first();
      const initialColor = await sample.evaluate(
        (el) => getComputedStyle(el).color,
      );
      const activeTheme = await source
        .locator(".art-theme-btn.active")
        .innerText();
      // The site's tray retracts while scrolling; return to its normal header.
      await source.evaluate(() =>
        window.scrollTo({ top: 0, behavior: "instant" }),
      );
      await expect(source.locator(".art-theme-tray")).not.toHaveClass(
        /is-floating/,
      );
      await source.locator(".art-theme-btn:not(.active)").first().click();
      await expect
        .poll(() => sample.evaluate((el) => getComputedStyle(el).color), {
          timeout: 20000,
        })
        .not.toBe(initialColor);
      await source
        .getByRole("button", { name: activeTheme, exact: true })
        .click();
      await expect
        .poll(() => sample.evaluate((el) => getComputedStyle(el).color), {
          timeout: 20000,
        })
        .toBe(initialColor);
      receipt.checks.push(
        "All expanded essay prose has one exact sentence node; site theme changes repaint annotations without breaking page controls",
      );
    } else {
      const footer = session.artifact.regions.find(
        (r) =>
          r.pageHint?.unit === "group" &&
          r.anchor.exact.includes("References & Assets"),
      );
      expect(footer).toBeTruthy();
      expect(
        session.packet.goalHierarchy.nodes.filter(
          (n) => n.span?.region === footer.id,
        ),
      ).toHaveLength(1);
      const projectReadings = [];
      await source
        .locator("div.group.cursor-pointer")
        .filter({
          has: source.getByRole("heading", {
            name: "Alaska Door Plug Investigations",
            exact: true,
          }),
        })
        .click();
      for (let i = 0; i < 7; i++) {
        const content = source.locator(".whitespace-pre-line").first();
        await content.waitFor();
        const text = await content.innerText();
        await expect
          .poll(
            async () =>
              ((await reading())?.artifact?.regions ?? []).some((r) =>
                r.anchor.exact.includes(
                  text.replace(/\s+/g, " ").trim().slice(0, 70),
                ),
              ),
            { timeout: 15000 },
          )
          .toBe(true);
        projectReadings.push({
          heading: await source
            .getByRole("button", { name: "Close modal", exact: true })
            .locator("..")
            .locator("h2")
            .innerText(),
          text,
        });
        if (i < 6)
          await source
            .getByRole("button", { name: "Next project", exact: true })
            .click();
      }
      await writeFile(
        ".local/website-project-captures.json",
        JSON.stringify(projectReadings, null, 2),
      );
      await expect(
        source.locator(".whitespace-pre-line [data-tompathy-reading]").first(),
      ).toBeVisible();
      await source
        .getByRole("button", { name: "Close modal", exact: true })
        .click();
      await expect
        .poll(async () => (await reading())?.artifact?.regions?.length, {
          timeout: 15000,
        })
        .toBe(session.artifact.regions.length);
      receipt.checks.push(
        "All seven live homepage project dialogs recapture their plain-text descriptions and return cleanly to the homepage",
      );
    }
    await panel
      .getByRole("tab", { name: "current work only", exact: true })
      .click();
    receipt.pages.push({ url, ...counts(session) });
    receipt.checks.push(
      `${kind}: actual website + native Chrome panel; source lock, keyboard navigation, keyboard and pointer tier resizing, seven drives, Creator/Global values and charts`,
    );
  }
  expect(receipt.errors).toEqual([]);
  await writeFile(
    "evidence/website-validation.json",
    JSON.stringify(receipt, null, 2),
  );
  console.log(JSON.stringify(receipt, null, 2));
} finally {
  if (current) await current.cdp.send("Browser.close").catch(() => {});
  for (const browser of connections) await browser.close().catch(() => {});
}
