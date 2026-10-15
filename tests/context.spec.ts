import { test, expect } from "@playwright/test";
import { createExample } from "../src/core/example";

test("free linked-source timeline: bounded discovery, dates, cache, coverage, export and opt-in", async ({
  page,
}) => {
  const packet = await createExample();
  const creator = "Mara Vale",
    origin = "https://creator.example.org";
  packet.artifact.authors = [{ label: creator, basis: "byline" }];
  await page.addInitScript(
    ({ packet, creator, origin }) => {
      localStorage.setItem("tompathy-guide-offered-040", "yes");
      localStorage.setItem("tompathy-follow-links", "true");
      sessionStorage.setItem(
        "tompathy-session",
        JSON.stringify({
          sessionVersion: "1.0",
          artifact: packet.artifact,
          packet,
          scope: "artifact",
          context: [],
          contextSources: [{ author: creator, url: origin + "/about" }],
        }),
      );
    },
    { packet, creator, origin },
  );
  const requests: string[] = [];
  await page.route(origin + "/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    requests.push(path);
    if (path === "/about")
      return route.fulfill({
        contentType: "text/html",
        body: `<title>A garden practice</title><link rel="alternate" type="application/atom+xml" href="/feed.xml"><main><p>I design public gardens with the people who use them.</p>${Array.from({ length: 8 }, (_, i) => `<a href="/blog/${i}">Article ${i}</a>`).join("")}</main>`,
      });
    if (path === "/feed.xml")
      return route.fulfill({
        contentType: "application/atom+xml",
        body: `<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Learning through gardens</title><published>2021-04-05T12:00:00Z</published><link href="${origin}/blog/old"/><summary>Notes from a public garden.</summary></entry><entry><title>Revised notes</title><updated>2023-03-02T09:00:00Z</updated><summary>Revision date only.</summary></entry></feed>`,
      });
    if (path === "/blog/3")
      return route.fulfill({
        status: 429,
        contentType: "text/plain",
        body: "Please try later",
      });
    return route.fulfill({
      contentType: "text/html",
      body: `<title>Garden ${path}</title><meta property="article:published_time" content="2024-05-10"><script type="application/ld+json">{"@type":"Event","name":"Garden walk","startDate":"2024-06"}</script><main><p>A documented garden experiment, with its original source intact.</p><a href="/blog/recursive">Do not crawl another hop</a></main>`,
    });
  });
  await page.setViewportSize({ width: 360, height: 900 });
  await page.goto("/?panel&demo=fieldnotes");
  const values = await page.getByTestId("values").innerHTML();
  await page.getByRole("button", { name: "Reader menu", exact: true }).click();
  await page.getByRole("checkbox", { name: /^Light context/ }).check();
  await expect.poll(() => requests.length).toBe(6);
  await page.getByRole("button", { name: "View context and timeline" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("status")).toContainText("5 of 6 sources read");
  expect(requests).toEqual([
    "/about",
    "/feed.xml",
    "/blog/0",
    "/blog/1",
    "/blog/2",
    "/blog/3",
  ]);
  await expect(dialog).toContainText("Learning through gardens");
  await expect(dialog).toContainText("2021-04-05");
  await expect(dialog).toContainText("Source updated");
  await expect(dialog).toContainText("Listed event");
  await expect(dialog).toContainText("2024-06");
  await expect(dialog).toContainText("Page byline: Mara Vale");
  await dialog.getByText("Collection coverage", { exact: true }).click();
  await expect(dialog).toContainText("Six-source collection limit");
  await expect(dialog).toContainText("429");
  await dialog.getByText("Collection coverage", { exact: true }).click();
  await page.screenshot({ path: "evidence/creator-context-timeline.png" });
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    dialog.getByRole("button", { name: "Export brief" }).click(),
  ]);
  const stream = await download.createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream!) chunks.push(Buffer.from(chunk));
  const brief = Buffer.concat(chunks).toString();
  expect(brief).toContain("2021-04-05 · Published");
  expect(brief).toContain("https://creator.example.org/blog/old");
  expect(brief).toContain("not biographical event dates");
  expect(await page.getByTestId("values").innerHTML()).toBe(values);
  const session = await page.evaluate(() =>
    JSON.parse(sessionStorage.getItem("tompathy-session")!),
  );
  expect(session.context).toHaveLength(6); // byline plus five fetched sources
  expect(session.context.every((s: any) => !s.selected)).toBe(true);
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.getByRole("button", { name: "Reader menu", exact: true }).click();
  await page.getByRole("checkbox", { name: /^Light context/ }).uncheck();
  await page.getByRole("checkbox", { name: /^Light context/ }).check();
  await page.getByRole("button", { name: "View context and timeline" }).click();
  await expect(dialog.getByRole("status")).toContainText("5 cached");
  expect(requests).toHaveLength(7); // only the unsuccessful source is retried
  await dialog
    .getByText("Sources for the next analysis", { exact: true })
    .click();
  await dialog.getByRole("checkbox").first().check();
  const selected = await page.evaluate(() =>
    JSON.parse(sessionStorage.getItem("tompathy-session")!),
  );
  expect(selected.context.filter((s: any) => s.selected)).toHaveLength(1);
  expect(selected.scope).toBe("context");
  await dialog.getByRole("checkbox").first().uncheck();
  await expect
    .poll(() =>
      page.evaluate(
        () => JSON.parse(sessionStorage.getItem("tompathy-session")!).scope,
      ),
    )
    .toBe("artifact");
  await expect(page.getByTestId("values")).toContainText("Care for others");
});

test("timeline cancellation keeps completed byline and rejects late source responses", async ({
  page,
}) => {
  const packet = await createExample();
  packet.artifact.authors = [{ label: "Mara Vale", basis: "byline" }];
  await page.addInitScript((packet) => {
    localStorage.setItem("tompathy-guide-offered-040", "yes");
    sessionStorage.setItem(
      "tompathy-session",
      JSON.stringify({
        sessionVersion: "1.0",
        artifact: packet.artifact,
        packet,
        scope: "artifact",
        context: [],
        contextSources: [
          {
            author: "Mara Vale",
            url: "https://creator.example.org/slow",
          },
        ],
      }),
    );
  }, packet);
  let release!: () => void;
  const response = new Promise<void>((r) => {
    release = r;
  });
  let requested = false;
  await page.route("https://creator.example.org/slow", async (route) => {
    requested = true;
    await response;
    await route
      .fulfill({
        contentType: "text/plain",
        body: "Late source must not become context.",
      })
      .catch(() => {});
  });
  await page.goto("/?panel&demo=fieldnotes");
  await page.getByRole("button", { name: "Reader menu", exact: true }).click();
  await page.getByRole("checkbox", { name: /^Light context/ }).check();
  await expect.poll(() => requested).toBe(true);
  await page.getByRole("button", { name: "View context and timeline" }).click();
  await page.getByRole("button", { name: "Cancel collection" }).click();
  release();
  await expect(
    page.getByRole("button", { name: "Refresh sources" }),
  ).toBeEnabled();
  await page.waitForTimeout(100);
  const context = await page.evaluate(
    () => JSON.parse(sessionStorage.getItem("tompathy-session")!).context,
  );
  expect(context).toHaveLength(1);
  expect(context[0].provenance.basis).toBe("page-byline");
  expect(context[0].selected).toBe(false);
});

test("feed and metadata extraction rejects malformed dates and never executes fetched markup", async ({
  page,
}) => {
  await page.goto("/?panel&demo=fieldnotes");
  const result = await page.evaluate(async () => {
    const moduleURL = "/src/core/context-source.ts";
    const { parseContextSource } = (await import(
      moduleURL
    )) as typeof import("../src/core/context-source");
    const source = new URL("https://creator.example.org/feed");
    const rss = parseContextSource(
      `<rss><channel><item><title>Garden journal</title><pubDate>Tue, 05 Apr 2022 12:00:00 GMT</pubDate><link>https://creator.example.org/blog/journal</link><description>&lt;b&gt;Safe excerpt&lt;/b&gt;</description></item></channel></rss>`,
      "application/rss+xml",
      source,
    );
    const html = parseContextSource(
      `<title>Undated writing</title><meta property="article:published_time" content="2023-02-29"><script>window.untrustedContextExecuted=true</script><main><p>This source has an impossible date and remains undated.</p><a href="http://127.0.0.1/private">Private</a></main>`,
      "text/html",
      source,
    );
    let malformed = "";
    try {
      parseContextSource("<feed><entry>", "application/atom+xml", source);
    } catch (e) {
      malformed = String(e);
    }
    return {
      rss,
      html,
      malformed,
      executed: (window as any).untrustedContextExecuted,
    };
  });
  expect(result.rss.facts[0].date).toBe("2022-04-05");
  expect(result.rss.facts[0].quote).toContain("Safe excerpt");
  expect(
    result.html.facts.every((f) => f.dateKind === "undated" && !f.date),
  ).toBe(true);
  expect(result.html.links).toEqual([]);
  expect(result.executed).toBeUndefined();
  expect(result.malformed).toContain("not a readable RSS or Atom feed");
});
