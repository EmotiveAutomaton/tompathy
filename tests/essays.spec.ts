import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";

const source = await readFile("src/content/essays-source.txt", "utf8");
const titles = [
  "Current attention",
  "Expertise (Previous attention)",
  "Core values",
];
const sections = source
  .split(/^-.*:\r?$/m)
  .slice(1)
  .map((s) =>
    s
      .split(/_{10,}/)[0]
      .trim()
      .split(/\r?\n/)
      .filter(Boolean),
  );
const normalize = (s: string) =>
  s
    .replace(/\s+/g, " ")
    .replace(/ +([.,;:!?)])/g, "$1")
    .trim();
const visibleProse = (s: string) =>
  normalize(
    s
      .replace(/\s*\[\d+\]/g, "")
      .replace(/\[abrahamhaskins.org\/art\]/g, "abrahamhaskins.org/art")
      .replace(/\*/g, ""),
  );

test("delayed hints, authored prose, shared references and bibliography", async ({
  page,
}) => {
  test.setTimeout(90000);
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/?demo=fieldnotes");
  const sources = new Map<string, number>();
  for (let i = 0; i < titles.length; i++) {
    const trigger = page.getByRole("button", {
      name: `About ${titles[i]}`,
      exact: true,
    });
    const rightOfLabel = await trigger.evaluate((el) => {
      const label = el.previousElementSibling!;
      return (
        el.getBoundingClientRect().left >= label.getBoundingClientRect().right
      );
    });
    expect(rightOfLabel).toBe(true);
    await trigger.hover();
    await page.waitForTimeout(700);
    await expect(page.getByRole("tooltip")).toHaveCount(0);
    await expect(page.getByRole("tooltip")).toContainText(
      i === 0
        ? "Click for a fun explanation"
        : `Click for part ${i === 1 ? "two" : "three"}`,
    );
    await expect(page.locator(".essay-preview br")).toHaveCount(1);
    await trigger.click();
    const dialog = page.locator(".essay-dialog");
    await expect(dialog).toBeVisible();
    const prose = await dialog
      .locator("[data-essay-paragraph]")
      .evaluateAll((nodes) =>
        nodes.map((node) => {
          const copy = node.cloneNode(true) as HTMLElement;
          copy.querySelectorAll("sup").forEach((sup) => sup.remove());
          return copy.textContent ?? "";
        }),
      );
    expect(prose.map(normalize)).toEqual(sections[i].map(visibleProse));
    await expect(dialog.locator(".essay-placement-note")).toHaveCount(0);
    const links = await dialog
      .locator("sup a")
      .evaluateAll((nodes) =>
        nodes.map((n) => ({
          number: Number(n.textContent),
          href: (n as HTMLAnchorElement).href,
        })),
      );
    for (const ref of links) {
      const key = ref.href.replace(/\/$/, "");
      if (!sources.has(key)) sources.set(key, sources.size + 1);
      expect(ref.number).toBe(sources.get(key));
    }
    const repositories = links.filter((ref) =>
      ref.href.includes("github.com/EmotiveAutomaton/"),
    );
    expect(repositories).toHaveLength(i === 2 ? 4 : 0);
    if (i === 1) {
      await expect(dialog.locator("em")).toHaveText(["why", "because", "appear"]);
      expect(
        links.some((ref) => ref.href === "https://arxiv.org/abs/2502.00873"),
      ).toBe(true);
      await expect(
        dialog
          .locator(".essay-figure")
          .filter({ hasText: "Don't panic please" }),
      ).toContainText("skill decay should account for less than 1.5% over that timeline");
    }
    await expect(
      dialog.getByRole("button", { name: "Close essay" }),
    ).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(dialog).not.toBeVisible();
    await expect(trigger).toBeFocused();
  }
  await page.getByRole("button", { name: "Reader menu", exact: true }).click();
  await page.getByRole("button", { name: "Bibliography", exact: true }).click();
  const bibliography = page.locator(".essay-bibliography");
  await expect(bibliography).toBeVisible();
  const entries = await bibliography
    .locator("li")
    .evaluateAll((nodes) =>
      nodes.map((n) => ({
        number: (n as HTMLLIElement).value,
        href: n.querySelector("a")!.href,
      })),
    );
  expect(entries).toHaveLength(sources.size);
  for (const entry of entries)
    expect(entry.number).toBe(sources.get(entry.href.replace(/\/$/, "")));
  await page.screenshot({ path: "evidence/essays-bibliography.png" });
  await page.getByRole("button", { name: "Close essay" }).click();
  expect(errors).toEqual([]);
});

test("cropped artwork, responsive width and dismissal", async ({
  page,
}) => {
  test.setTimeout(90000);
  await page.goto("/?demo=fieldnotes");
  for (const [i, title] of titles.entries()) {
    await page
      .getByRole("button", { name: `About ${title}`, exact: true })
      .click();
    const dialog = page.locator(".essay-dialog");
    const box = (await dialog.boundingBox())!;
    expect(box.width).toBeGreaterThan(1000);
    expect(box.x).toBeCloseTo(24, 0);
    await expect(dialog.locator(".essay-images img")).toHaveCount(
      [7, 14, 6][i],
    );
    for (const image of await dialog.locator(".essay-images img").all()) {
      await image.scrollIntoViewIfNeeded();
      await expect
        .poll(() =>
          image.evaluate(
            (img: HTMLImageElement) => img.complete && img.naturalWidth > 0,
          ),
        )
        .toBe(true);
      const style = await image.evaluate((el) => ({
        fit: getComputedStyle(el).objectFit,
        width: el.getBoundingClientRect().width,
        title: el.getAttribute("title"),
        alt: el.getAttribute("alt"),
      }));
      expect(style.fit).toBe(["Art is compressed intent", "Pixar schadenfreude", "Inside out 2", "And we need everyone's help"].includes(style.title!) ? "contain" : "cover");
      expect(style.width).toBeLessThanOrEqual(["Art is compressed intent", "And we need everyone's help"].includes(style.title!) ? 640 : 320);
      expect(style.title).toBe(style.alt);
    }
    if (i === 0) {
      const grid = dialog.locator(".essay-image-grid").last();
      await grid.scrollIntoViewIfNeeded();
      const boxes = await grid
        .locator("img")
        .evaluateAll((nodes) =>
          nodes.map((n) => ({
            x: n.getBoundingClientRect().x,
            y: n.getBoundingClientRect().y,
          })),
        );
      expect(boxes[0].y).toBe(boxes[1].y);
      expect(boxes[2].y).toBe(boxes[3].y);
      expect(boxes[2].y).toBeGreaterThan(boxes[0].y);
      expect((await grid.boundingBox())!.width).toBeCloseTo(328, 0);
      await expect(dialog.getByAltText("AI slop")).toHaveCSS(
        "border-top-color",
        "rgb(153, 153, 153)",
      );
      await expect(dialog.getByAltText("Bot farms")).toHaveCSS(
        "border-top-color",
        "rgb(17, 17, 17)",
      );
      await page.screenshot({ path: "evidence/essays-abuse-grid.png" });
    }
    if (i === 1) {
      await expect(dialog.getByAltText("Pixar cheaters")).toHaveCSS(
        "border-top-width",
        "4px",
      );
      await dialog.getByAltText("The valuable top").scrollIntoViewIfNeeded();
      await page.screenshot({ path: "evidence/essays-illustrations.png" });
    }
    if (i === 2) {
      await expect(dialog.locator(".essay-channel > span")).toHaveText([
        "SEEKING",
        "RAGE",
        "FEAR",
        "LUST",
        "CARE",
        "PANIC/GRIEF",
        "PLAY",
      ]);
      await dialog.locator(".essay-channels").scrollIntoViewIfNeeded();
      await page.screenshot({ path: "evidence/essays-channels.png" });
      await dialog.locator(".essay-preference").scrollIntoViewIfNeeded();
      await page.screenshot({ path: "evidence/essays-preference.png" });
      await expect(dialog.locator(".preference-vector")).toHaveCount(3);
      await expect(
        dialog.locator(".essay-figure").last().locator("figcaption"),
      ).toHaveCount(0);
    }
    await page.keyboard.press("Escape");
  }
  const trigger = page.getByRole("button", {
    name: "About Expertise (Previous attention)",
    exact: true,
  });
  await trigger.focus();
  await page.keyboard.press("Enter");
  const dialog = page.locator(".essay-dialog");
  await page.screenshot({ path: "evidence/essays-wide.png" });
  const box = (await dialog.boundingBox())!;
  await page.mouse.move(box.x + 10, box.y + 10);
  await page.mouse.down();
  await page.mouse.move(3, 3);
  await page.mouse.up();
  await expect(dialog).toBeVisible();
  await page.mouse.click(3, 3);
  await expect(dialog).not.toBeVisible();
  await page.setViewportSize({ width: 360, height: 800 });
  await page.evaluate(() => (document.documentElement.dataset.theme = "dark"));
  for (const title of titles) {
    await page
      .getByRole("button", { name: `About ${title}`, exact: true })
      .click();
    expect(
      await dialog.evaluate((el) => el.scrollWidth <= el.clientWidth),
    ).toBe(true);
    expect((await dialog.boundingBox())!.x).toBeCloseTo(24, 0);
    for (const grid of await dialog
      .locator(".essay-image-grid, .essay-channels")
      .all()) {
      await grid.scrollIntoViewIfNeeded();
      expect(
        await grid.evaluate((el) => el.scrollWidth <= el.clientWidth),
      ).toBe(true);
    }
    await page.screenshot({
      path: `evidence/essays-narrow-${titles.indexOf(title)}.png`,
    });
    await dialog.getByRole("button", { name: "Close essay" }).click();
  }
  await trigger.hover();
  await page.mouse.move(1, 1);
  await page.waitForTimeout(1700);
  await expect(page.getByRole("tooltip")).toHaveCount(0);
});
test('image lightbox and essay sequence preserve the reading', async ({page})=>{
  await page.goto('/?demo=fieldnotes');
  await page.getByRole('button',{name:'About Current attention',exact:true}).click();
  const essay=page.locator('.essay-dialog');
  const image=essay.getByRole('button',{name:'Enlarge Art is compressed intent',exact:true});
  await image.click();
  const lightbox=page.locator('.essay-lightbox');
  await expect(lightbox).toBeVisible();
  await expect(lightbox.locator('img')).toHaveCSS('object-fit','contain');
  const box=(await lightbox.boundingBox())!;
  expect(box.x).toBe(0);expect(box.y).toBe(0);expect(box.width).toBe(page.viewportSize()!.width);expect(box.height).toBe(page.viewportSize()!.height);
  await page.screenshot({path:'evidence/essays-lightbox.png'});
  await lightbox.click();
  await expect(lightbox).toHaveCount(0);
  await expect(image).toBeFocused();
  await expect(essay).toBeVisible();
  await image.press('Enter');
  await page.keyboard.press('Escape');
  await expect(lightbox).toHaveCount(0);await expect(essay).toBeVisible();
  await essay.getByRole('link',{name:'next',exact:true}).click();
  await expect(essay.getByRole('heading')).toHaveText('Expertise (Previous Attention)');
  expect(await essay.evaluate(el=>el.scrollTop)).toBe(0);
  await essay.getByRole('link',{name:'next',exact:true}).click();
  await expect(essay.getByRole('heading')).toHaveText('Core Values');
  await expect(essay.getByRole('link',{name:'next',exact:true})).toHaveCount(0);
  await essay.getByRole('button',{name:'Enlarge seven channels'}).click();
  await expect(lightbox.locator('.essay-channel')).toHaveCount(7);
  await lightbox.click();
  await essay.getByRole('link',{name:'here',exact:true}).click();
  await expect(essay.getByRole('heading')).toHaveText('Current Attention');
  await expect(essay.locator('.essay-navigation').first()).toHaveText('next');
});
