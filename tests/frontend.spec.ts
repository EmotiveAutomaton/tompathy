import { test, expect, type Page } from "@playwright/test";
async function tool(page: Page, name: string) {
  await page.getByRole("button", { name: "Reader menu", exact: true }).click();
  await page.getByRole("button", { name, exact: true }).click();
}
test("linked hypotheses, stable values, pin/release and evidence", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator(".identity-note")).toBeVisible();
  const values = await page.getByTestId("values").innerHTML();
  await page.locator('[data-passage="p4"]').hover();
  await expect(page.getByTestId("process")).toContainText("Test & refine");
  await expect(page.getByTestId("goals")).toContainText("Test an assumption");
  expect(await page.getByTestId("values").innerHTML()).toEqual(values);
  await page.locator('[data-passage="p4"]').click();
  await page.locator('[data-passage="p2"]').hover();
  await expect(page.locator(".passage-strip")).toContainText(
    "Pinned passage 4",
  );
  await page.keyboard.press("Escape");
  await page.locator('[data-passage="p3"]').hover();
  await expect(page.locator(".passage-strip")).toContainText(
    "Following passage 3",
  );
  await page
    .getByRole("button", { name: "Reframe the problem", exact: false })
    .click();
  await expect(
    page.getByRole("region", { name: "Hypothesis evidence" }),
  ).toContainText("not a probability");
  await page.getByRole("button", { name: "Passage 2", exact: true }).click();
  await expect(page.locator(".passage-strip")).toContainText(
    "Pinned passage 2",
  );
  await page
    .getByRole("button", { name: "Expand process into word cloud" })
    .click();
  await expect(page.locator(".process-map.cloud")).toBeVisible();
  await expect(page.getByTestId("process")).toContainText("Earlier experience");
  await page.getByRole("button", { name: "Collapse to process tree" }).click();
  await expect(page.locator(".process-tree ul").first()).toBeVisible();
  await page.getByRole("button", { name: "Reader menu" }).click();
  await page.getByLabel("Show hypotheses as a list").check();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await expect(page.getByTestId("process")).toContainText("Earlier experience");
});
test("context changes invalidate scope; explicit revision updates fixed values", async ({
  page,
}) => {
  await page.goto("/");
  await tool(page, "Context");
  await page
    .getByLabel("Excerpt", { exact: true })
    .fill("A pasted notebook with a competing account.");
  await page.getByRole("button", { name: "Add excerpt", exact: true }).click();
  await expect(page.locator(".context-item")).toContainText(
    "competing account",
  );
  await page.getByLabel("Analysis scope").selectOption("context");
  await page.getByRole("button", { name: "Close dialog" }).click();
  await expect(page.getByText("A different evidence scope")).toBeVisible();
  await expect(page.getByTestId("values")).toContainText(
    "snapshot will appear",
  );
  await tool(page, "Context · 1");
  await page.getByLabel("Analysis scope").selectOption("artifact");
  await page.getByRole("button", { name: "Preview example revision" }).click();
  await expect(page.getByRole("dialog")).toContainText("Work within a brief");
  await page.getByRole("button", { name: "Accept this revision" }).click();
  await expect(page.getByTestId("values")).toContainText("Practical care");
  await page.locator('[data-passage="p5"]').hover();
  await expect(page.getByTestId("process")).toContainText(
    "Work within a brief",
  );
});
test("malformed packet, pasted text and session clear expose honest empty state", async ({
  page,
}) => {
  await page.goto("/");
  await tool(page, "Import result");
  await page.getByText("Or paste JSON").click();
  await page.getByLabel("Result JSON").fill("{broken");
  await page.getByRole("button", { name: "Validate & import" }).click();
  await expect(page.getByRole("dialog").getByRole("alert")).toBeVisible();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page
    .getByRole("button", { name: "A bench is an invitation", exact: true })
    .click();
  await page
    .getByLabel("Paste a different text")
    .fill("This is a new text, written only for this browser test.");
  await page.getByRole("button", { name: "Use pasted text" }).click();
  await expect(
    page.getByText("Maker estimates are awaiting an analysis source.", {
      exact: false,
    }),
  ).toBeVisible();
  await tool(page, "Reader settings");
  await page.getByRole("button", { name: "Clear session" }).click();
  await expect(page.getByText("Start with a piece of writing")).toBeVisible();
});
test("narrow dark panel, reduced motion and keyboard dialog focus", async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 900 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/?panel");
  await tool(page, "Reader settings");
  await page.getByRole("button", { name: "dark", exact: true }).click();
  await page.keyboard.press("Escape");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await expect(page.getByTestId("values")).toBeInViewport();
  await page.getByTestId("process").evaluate((el) => {
    el.scrollTop = el.scrollHeight;
  });
  await expect(
    page.getByRole("heading", { name: "Goals", exact: true }),
  ).toBeInViewport();
  await expect(
    page.getByRole("heading", { name: "Values", exact: true }),
  ).toBeInViewport();
  await page.getByTestId("process").evaluate((el) => {
    el.scrollTop = 0;
  });
  await page.screenshot({ path: "evidence/panel-dark-320.png" });
  await tool(page, "How ToMpathy works");
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: "Reader menu" })).toBeFocused();
});
test("session save/load, file context and explicit imported-context selection", async ({
  page,
}) => {
  await page.goto("/");
  await tool(page, "Context");
  await page.locator("input[type=file]").setInputFiles({
    name: "notes.md",
    mimeType: "text/markdown",
    buffer: Buffer.from("A note from a synthetic source."),
  });
  await page.locator(".context-item input[type=checkbox]").check();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await tool(page, "Reader settings");
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Save session", exact: true }).click();
  const saved = await downloadPromise;
  const file = await saved.path();
  await page.getByRole("button", { name: "Clear session" }).click();
  await tool(page, "Reader settings");
  await page.locator("input[type=file]").setInputFiles(file!);
  await expect(
    page.getByText("Session loaded as a detached snapshot.", { exact: false }),
  ).toBeVisible();
  await tool(page, "Context · 1");
  await expect(page.locator(".context-item input")).not.toBeChecked();
  await page.getByRole("button", { name: "Remove notes.md" }).click();
  await expect(page.locator(".context-item")).toHaveCount(0);
});
test("collection cancellation and 200% zoom preserve usable controls", async ({
  page,
}) => {
  await page.goto("/");
  await tool(page, "Context");
  await page.getByText("Retrieve public sources", { exact: true }).click();
  await page.route("https://example.com/slow", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 2000));
    await route
      .fulfill({
        status: 200,
        body: "An excerpt that arrived too late.",
        contentType: "text/plain",
      })
      .catch(() => {});
  });
  await page.getByLabel("URLs, one per line").fill("https://example.com/slow");
  await page.getByRole("button", { name: "Collect selected sources" }).click();
  await page.getByRole("button", { name: "Cancel collection" }).click();
  await expect(page.getByRole("dialog")).toContainText("Collection cancelled");
  await expect(page.locator(".context-item")).toHaveCount(0);
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.setViewportSize({ width: 640, height: 1000 });
  await page.evaluate(() => {
    document.documentElement.style.zoom = "2";
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await tool(page, "Reader settings");
  await expect(
    page.getByRole("button", { name: "Close dialog" }),
  ).toBeInViewport();
  const bounds = await page.getByRole("dialog").boundingBox();
  expect(bounds!.y).toBeGreaterThanOrEqual(0);
  expect(bounds!.y + bounds!.height).toBeLessThanOrEqual(1000);
  await page.screenshot({ path: "evidence/zoom-200.png" });
});
