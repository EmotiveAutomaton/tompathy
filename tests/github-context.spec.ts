import { test, expect } from "@playwright/test";
import { createExample } from "../src/core/example";

test("changing creators preserves the enabled context preference and collects the new byline", async ({
  page,
}) => {
  const packet = await createExample();
  packet.makers.push({
    ...packet.makers[0],
    id: "maker-2",
    label: "Rowan Lee",
  });
  packet.artifact.authors = [
    { label: "Mara Vale", basis: "byline" },
    { label: "Rowan Lee", basis: "byline" },
  ];
  await page.addInitScript((packet) => {
    localStorage.setItem("tompathy-guide-offered-040", "yes");
    localStorage.setItem("tompathy-context-enabled", "true");
    localStorage.setItem("tompathy-use-github", "false");
    sessionStorage.setItem(
      "tompathy-session",
      JSON.stringify({
        sessionVersion: "1.0",
        artifact: packet.artifact,
        packet,
        scope: "artifact",
        context: [],
      }),
    );
  }, packet);
  await page.goto("/?panel&demo=fieldnotes");
  await expect(page.locator(".context-progress.done")).toBeVisible();
  await page.getByLabel("Creator selection").selectOption("maker-2");
  await expect
    .poll(() =>
      page.evaluate(() =>
        JSON.parse(sessionStorage.getItem("tompathy-session")!).context.some(
          (c: any) => c.provenance?.author === "Rowan Lee",
        ),
      ),
    )
    .toBe(true);
  await page.getByRole("button", { name: "Reader menu", exact: true }).click();
  await expect(
    page.getByRole("checkbox", { name: /^Light context/ }),
  ).toBeChecked();
});

test("saved context option starts bounded GitHub history, shows a bar and retains source dates", async ({
  page,
}) => {
  const packet = await createExample();
  packet.artifact.authors = [{ label: "Mara Vale", basis: "byline" }];
  await page.addInitScript((packet) => {
    localStorage.setItem("tompathy-guide-offered-040", "yes");
    localStorage.setItem("tompathy-context-enabled", "true");
    if (!sessionStorage.getItem("tompathy-session"))
      sessionStorage.setItem(
        "tompathy-session",
        JSON.stringify({
          sessionVersion: "1.0",
          artifact: packet.artifact,
          packet,
          scope: "artifact",
          context: [],
          repositoryLinks: [
            "https://github.com/example/docs/blob/main/article.md",
          ],
        }),
      );
  }, packet);
  const calls: string[] = [];
  await page.route("https://api.github.com/**", async (route) => {
    const url = new URL(route.request().url());
    calls.push(url.pathname);
    await new Promise((resolve) => setTimeout(resolve, 350));
    const sha = "a".repeat(40);
    const body = url.pathname.endsWith("/docs")
      ? {
          private: false,
          default_branch: "main",
          description: "Public essay source",
        }
      : url.pathname.includes("/contents/")
        ? {
            type: "file",
            path: "article.md",
            encoding: "base64",
            content: btoa("A documented revision."),
          }
        : url.pathname.endsWith("/commits")
          ? [
              {
                sha,
                commit: {
                  author: { name: "Mara Vale", date: "2024-03-01T12:00:00Z" },
                  committer: { date: "2024-03-02T12:00:00Z" },
                  message: "Clarify invitation",
                },
              },
            ]
          : {
              files: [
                {
                  filename: "article.md",
                  status: "modified",
                  additions: 2,
                  deletions: 1,
                  patch: "+You can join in.",
                },
              ],
            };
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify(body),
    });
  });
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto("/?panel&demo=fieldnotes");
  await expect(page.getByRole("progressbar")).toBeVisible();
  await expect(page.locator(".context-progress")).toContainText(
    "Fetching GitHub",
  );
  await expect
    .poll(() => page.locator(".context-progress-fill").getAttribute("width"))
    .not.toBe("0");
  await page.screenshot({ path: "evidence/github-progress.png" });
  await expect(page.locator(".context-progress.done")).toBeVisible();
  expect(calls).toHaveLength(4);
  await page.getByRole("button", { name: "Reader menu", exact: true }).click();
  await page.getByRole("button", { name: "View context and timeline" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toContainText("2024-03-01");
  await expect(dialog).toContainText("Clarify invitation");
  await expect(dialog).toContainText("Source updated");
  await page.screenshot({ path: "evidence/github-timeline.png" });
  await page.reload();
  await expect(page.locator(".context-progress.done")).toBeVisible();
  expect(calls).toHaveLength(4); // Fresh source history survives reopening via the saved session.
  await page.goto("/icon-prompts.html");
  await page.setViewportSize({ width: 1280, height: 1000 });
  await expect(page.locator(".logo-study")).toHaveCount(4);
  await page.locator(".logo-study > a img").last().scrollIntoViewIfNeeded();
  await expect
    .poll(() =>
      page
        .locator(".logo-study > a img")
        .evaluateAll((images) =>
          images.every(
            (im) =>
              (im as HTMLImageElement).complete &&
              (im as HTMLImageElement).naturalWidth > 0,
          ),
        ),
    )
    .toBe(true);
  await page.evaluate(() => scrollTo(0, 0));
  await page.screenshot({ path: "evidence/logo-studies.png", fullPage: false });
});
