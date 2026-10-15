import { test, expect } from "@playwright/test";
import { createExample } from "../src/core/example";
import { readingFile } from "../src/core/reading-file";

test("Options, persistent idle reels, connected alternatives and overlay dismissal", async ({
  page,
}) => {
  await page.addInitScript(() =>
    localStorage.setItem("tompathy-guide-offered-040", "yes"),
  );
  await page.setViewportSize({ width: 360, height: 900 });
  await page.goto("/?panel&demo=fieldnotes");
  await expect(page.getByTestId("odometer")).toBeVisible();
  const idle = await page.getByTestId("odometer").boundingBox();
  await page.mouse.move(idle!.x + 10, idle!.y + 20);
  await expect(page.locator(".spool.is-expanded")).toHaveCount(0);
  await page.locator('[data-node="paragraph-3"] circle').first().click();
  const before = await page.getByTestId("odometer").boundingBox();
  await page.locator(".spool").nth(1).hover();
  await expect(
    page.getByRole("group", { name: "Possible goals", exact: true }).first(),
  ).toBeVisible();
  for (const label of [
    "Show sustained attention",
    "Make observation concrete",
    "Admit a failed attempt",
    "Show willingness to revise",
  ])
    await expect(
      page.getByRole("button", { name: label, exact: true }),
    ).toBeVisible();
  await expect(page.locator(".reels-open .pyramid")).toHaveCSS(
    "opacity",
    "0.48",
  );
  await expect(page.locator(".spool").nth(1)).toHaveClass(/spool-emphasis/);
  const after = await page.getByTestId("odometer").boundingBox();
  expect(after!.height).toBeGreaterThan(before!.height + 80);
  expect(
    Math.abs(before!.y + before!.height - (after!.y + after!.height)),
  ).toBeLessThan(3);
  await page.screenshot({ path: "evidence/reels-expanded.png" });
  await page.locator(".spool").nth(1).focus();
  await page.keyboard.press("Escape");
  await expect(page.locator(".spool.is-expanded")).toHaveCount(0);
  await expect(page.locator(".process-lock")).toBeVisible();
  await page
    .getByRole("button", { name: "Care for others", exact: true })
    .click();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.locator(".process-lock")).toBeVisible();
  await page.getByRole("button", { name: "Reader menu", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveAccessibleName("Options");
  await expect(
    page.getByRole("dialog").getByLabel("Creator selection"),
  ).toHaveCount(0);
  await expect(page.getByRole("checkbox")).toHaveCount(5);
  await expect(
    page.getByRole("checkbox", { name: /Word-level analysis/ }),
  ).toBeDisabled();
  await expect(
    page.getByRole("checkbox", { name: /Create a small local model/ }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Source text", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByText("synthetic example", { exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("group", { name: "Color scheme", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("checkbox", { name: /Agent search/ }),
  ).toBeEnabled();
  await page.getByRole("checkbox", { name: /Use GitHub/ }).uncheck();
  expect(
    await page.evaluate(() => localStorage.getItem("tompathy-use-github")),
  ).toBe("false");
  await page.getByRole("button", { name: "dark", exact: true }).click();
  await page.screenshot({ path: "evidence/options-dark.png" });
  await page.getByRole("button", { name: "light", exact: true }).click();
  await page.screenshot({ path: "evidence/options-light.png" });
});

test("portable reading restores exact source and rejects changed anchors", async ({
  page,
}) => {
  await page.addInitScript(() =>
    localStorage.setItem("tompathy-guide-offered-040", "yes"),
  );
  await page.goto("/?demo=fieldnotes");
  await page.getByRole("button", { name: "Reader menu", exact: true }).click();
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: "Export", exact: true }).click(),
  ]);
  const path = await download.path();
  expect(path).toBeTruthy();
  await page.getByLabel("Import reading").setInputFiles(path!);
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Care for others", exact: true }),
  ).toBeVisible();
  const p = await createExample("https://example.org/saved-article");
  const session = {
    sessionVersion: "1.0" as const,
    artifact: p.artifact,
    packet: p,
    context: [],
    scope: "artifact" as const,
  };
  await page.getByRole("button", { name: "Reader menu", exact: true }).click();
  await page.getByLabel("Import reading").setInputFiles({
    name: "reading.html",
    mimeType: "text/html",
    buffer: Buffer.from(readingFile(session)),
  });
  await expect(page.locator(".saved-page header")).toContainText(
    "https://example.org/saved-article",
  );
  await page.locator('[data-passage="p4"] [data-sentence="1"]').click();
  await expect(page.locator('[data-dominant="true"]')).toHaveText(
    "Learning together",
  );
  session.artifact.regions[0].anchor.exact =
    "Tampered page with different source text";
  await page.getByRole("button", { name: "Reader menu", exact: true }).click();
  await page.getByLabel("Import reading").setInputFiles({
    name: "changed.html",
    mimeType: "text/html",
    buffer: Buffer.from(readingFile(session)),
  });
  await expect(page.getByRole("dialog").getByRole("alert")).toContainText(
    "no longer matches",
  );
});

test("context wheel follows real completed fetches and never updates estimates", async ({
  page,
}) => {
  const p = await createExample();
  const source = "https://creator.example.org/about";
  await page.addInitScript(
    ({ p, source }) => {
      localStorage.setItem("tompathy-guide-offered-040", "yes");
      sessionStorage.setItem(
        "tompathy-session",
        JSON.stringify({
          sessionVersion: "1.0",
          artifact: p.artifact,
          packet: p,
          scope: "artifact",
          context: [],
          contextSources: [{ author: "Mara Vale", url: source }],
        }),
      );
    },
    { p, source },
  );
  let complete!: () => void;
  const gate = new Promise<void>((r) => (complete = r));
  await page.route(source, async (route) => {
    await gate;
    await route.fulfill({
      status: 200,
      contentType: "text/plain",
      body: "Mara Vale writes about public spaces and iterative design.",
    });
  });
  await page.goto("/?panel&demo=fieldnotes");
  const values = await page.getByTestId("values").innerHTML();
  await page.getByRole("button", { name: "Reader menu", exact: true }).click();
  await page.getByRole("checkbox", { name: /^Light context/ }).check();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await expect(page.getByRole("progressbar")).toHaveAttribute(
    "aria-valuenow",
    "0",
  );
  complete();
  await expect(page.locator(".context-progress.done")).toBeVisible();
  expect(await page.getByTestId("values").innerHTML()).toBe(values);
  expect(
    await page.evaluate(
      () =>
        JSON.parse(sessionStorage.getItem("tompathy-session")!).context.length,
    ),
  ).toBe(1);
});

test("first-use guide is optional, dismissible, and replayable from Help", async ({
  page,
}) => {
  await page.goto("/?panel&demo=fieldnotes");
  await page.getByRole("button", { name: "Show me", exact: true }).click();
  await expect(page.locator(".interaction-guide")).toContainText(
    "Move over a sentence",
  );
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page.locator(".interaction-guide")).toContainText(
    "Click that sentence",
  );
  await page.getByRole("button", { name: "Dismiss interaction guide" }).click();
  await page.reload();
  await expect(page.locator(".interaction-guide")).toHaveCount(0);
  await page.getByRole("button", { name: "Reader menu", exact: true }).click();
  await page.getByRole("button", { name: "How ToMpathy works" }).click();
  await page.getByRole("button", { name: "Try the interaction guide" }).click();
  await expect(page.locator(".interaction-guide")).toContainText(
    "Move over a sentence",
  );
});

test("pointed branches, faded endings, precise reel hover gaps and double-click release", async ({
  page,
}) => {
  await page.addInitScript(() =>
    localStorage.setItem("tompathy-guide-offered-040", "yes"),
  );
  await page.setViewportSize({ width: 360, height: 900 });
  await page.goto("/?panel&demo=fieldnotes");
  const lower = page.locator('[data-node="practical-care"] circle');
  await lower.hover();
  await expect(page.locator('[data-node="purpose"].ancestor')).toHaveCount(0);
  await expect(page.locator('.spool[data-level="0"]')).toHaveClass(
    /aperture-closed/,
  );
  await expect(page.locator('.spool[data-level="0"] .spool-window')).toHaveCSS(
    "height",
    "2px",
  );
  await page.screenshot({ path: "evidence/short-branch.png" });
  await page.locator('[data-node="paragraph-3"] circle').click();
  const exact = page.locator('.spool[data-rank="1"] .spool-window');
  await exact.hover();
  await expect(page.locator(".spool.is-expanded")).toHaveCount(3);
  await expect(
    page.locator('.spool.is-expanded[data-rank="0"] .spool-window'),
  ).toHaveCSS("height", "170px");
  const tall = await page
    .locator('.spool.is-expanded[data-rank="0"] .spool-window')
    .boundingBox();
  const short = await exact.boundingBox();
  // The adjacent gap is navigable; empty space above the short reel is not sticky.
  await page.mouse.move(short!.x - 2, short!.y + 10);
  await expect(page.locator(".spool.is-expanded")).toHaveCount(3);
  await page.mouse.move(short!.x + short!.width / 2, short!.y - 12);
  await expect(page.locator(".spool.is-expanded")).toHaveCount(0);
  expect(tall!.height).toBeGreaterThan(short!.height * 3);
  await exact.hover();
  await expect(page.locator(".odometer")).toHaveCSS("scrollbar-width", "none");
  await expect(page.locator('.spool[data-rank="0"] .reel-options')).toHaveCSS(
    "scrollbar-width",
    "none",
  );
  await page.locator("#process-title").dblclick();
  await expect(page.locator(".process-lock")).toHaveCount(0);
  await lower.dblclick();
  await expect(page.locator(".process-lock")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: /^Order uncertain/ }),
  ).toHaveCount(2);
});
