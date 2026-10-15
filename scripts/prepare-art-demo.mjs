// Explicit maintenance command. Downloads only the public essay; never reads a
// private checkout or includes Git history in the distributable fixture.
import { chromium } from "@playwright/test";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
const source = "https://abrahamhaskins.org/art";
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  let html;
  if (process.argv[2]) html = await readFile(process.argv[2], "utf8");
  else {
    await page.route("**/*", (route) => {
      const request = route.request();
      if (
        ["image", "font", "media"].includes(request.resourceType()) ||
        new URL(request.url()).hostname !== "abrahamhaskins.org"
      )
        return route.abort();
      return route.continue();
    });
    await page.goto(source, { waitUntil: "networkidle", timeout: 45000 });
    await page
      .locator(".katex annotation")
      .first()
      .waitFor({ state: "attached", timeout: 15000 });
    html = await page.content();
    await mkdir(".local/art-source", { recursive: true });
    await writeFile(".local/art-source/rendered.html", html);
  }
  const blocks = await page.evaluate((html) => {
    const doc = new DOMParser().parseFromString(html, "text/html");
    for (const formula of doc.querySelectorAll(".katex")) {
      const tex = formula.querySelector(
        'annotation[encoding="application/x-tex"]',
      );
      if (tex) formula.replaceWith(doc.createTextNode(tex.textContent));
    }
    const elements = [
      ...doc.querySelectorAll(
        ".art-title,.art-heading,.art-subheading,.art-subtitle,.art-paragraph,.art-emphasis,.art-blockquote,.art-attribution,.art-caption,.art-ghost-demo-solid,.art-latex-block",
      ),
    ];
    const cutoff = elements.findIndex(
      (el) => el.textContent.trim() === "Bibliography",
    );
    return elements
      .slice(0, cutoff < 0 ? undefined : cutoff)
      .map((el) => {
        // Use accessible TeX once, rather than duplicated MathML and visual glyphs.
        const math = el.querySelector(
          'annotation[encoding="application/x-tex"]',
        );
        const raw =
          math && el.matches(".art-latex-block")
            ? math.textContent.trim()
            : el.textContent.trim();
        const offsets = [];
        const walker = doc.createTreeWalker(el, NodeFilter.SHOW_TEXT);
        let position = 0,
          node;
        while ((node = walker.nextNode())) {
          if (node.parentElement.closest("strong,b"))
            offsets.push({
              start: position,
              end: position + node.textContent.length,
            });
          position += node.textContent.length;
        }
        const prefix = (s) => s.replace(/\s+/gu, " ").trimStart();
        const text = raw.replace(/\s+/gu, " ").trim();
        return {
          text,
          type: el.matches(".art-title")
            ? "title"
            : el.matches(".art-heading")
              ? "section"
              : el.matches(".art-subheading,.art-subtitle")
                ? "heading"
                : el.matches(".art-caption")
                  ? "caption"
                  : el.matches(".art-latex-block")
                    ? "equation"
                    : "paragraph",
          ghost: Number(
            el.className.match(/ghost-(\d+)/)?.[1] ??
              el.parentElement.className.match(/ghost-(\d+)/)?.[1] ??
              -1,
          ),
          emphasis: offsets
            .map((e) => ({
              start: prefix(raw.slice(0, e.start)).length,
              end: Math.min(text.length, prefix(raw.slice(0, e.end)).length),
            }))
            .filter((e) => e.end > e.start),
          mixed: !!el.querySelector(".art-bright-span"),
          prompt: el.matches(".art-ghost-demo-solid")
            ? el.parentElement
                .querySelector(".art-ghost-demo-prompt")
                ?.textContent.trim()
            : undefined,
        };
      })
      .filter((b) => b.text);
  }, html);
  await writeFile(
    "src/core/art-snapshot.json",
    JSON.stringify(
      {
        source,
        title: "Art: A Unifying Model",
        creator: "Abraham Haskins",
        capturedAt: new Date().toISOString(),
        sha256: createHash("sha256").update(html).digest("hex"),
        note: "Published text and creator-supplied Ghost Scale labels. Figures and interactive bibliography remain on the original site. Equations are preserved as TeX. Mixed-involvement paragraphs remain unknown until finer attribution is supplied.",
        blocks,
      },
      null,
      2,
    ) + "\n",
  );
  console.log(`Saved ${blocks.length} public essay blocks.`);
} finally {
  await browser.close();
}
