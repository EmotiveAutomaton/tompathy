import type { Artifact } from "./model";

// Keep the live DOM as the anchor source. Never replace it with a parsed copy.
export function readingRoot(doc: Document): {
  root: Element;
  capture: NonNullable<Artifact["capture"]>;
} {
  const candidates: [string, NonNullable<Artifact["capture"]>["method"]][] = [
    ["article", "article"],
    [
      "[itemprop='articleBody'],.entry-content,.post-content,.entryBody,.markdown-body",
      "content-container",
    ],
    [
      ".entry.entryPage,.post-body,.article-body,section.body",
      "content-container",
    ],
    ["main,[role='main']", "main"],
  ];
  for (const [selector, method] of candidates) {
    const matches = [...doc.querySelectorAll(selector)].filter(
      (e) => !e.closest("nav,aside,footer,[hidden],[aria-hidden='true']"),
    );
    const root = matches.sort(
      (a, b) => (b.textContent?.length ?? 0) - (a.textContent?.length ?? 0),
    )[0];
    if (root && (root.textContent?.trim().length ?? 0) >= 12)
      return {
        root,
        capture: {
          method,
          note: "Captured the article content area. Review the source text before requesting analysis.",
        },
      };
  }
  return {
    root: doc.body,
    capture: {
      method: "page",
      note: "No article boundary was identified. This capture may include other page content; review it or use selected text.",
    },
  };
}

export function pageAuthors(doc: Document): NonNullable<Artifact["authors"]> {
  const found: NonNullable<Artifact["authors"]> = [];
  const add = (
    label: string | null | undefined,
    basis: NonNullable<Artifact["authors"]>[number]["basis"],
  ) => {
    const clean = label
      ?.replace(/\s+/g, " ")
      .replace(/^by\s+/i, "")
      .trim();
    if (
      clean &&
      clean.length <= 250 &&
      !found.some((a) => a.label.toLowerCase() === clean.toLowerCase()) &&
      found.length < 20
    )
      found.push({ label: clean, basis });
  };
  doc
    .querySelectorAll<HTMLMetaElement>(
      'meta[name="author"],meta[property="article:author"]',
    )
    .forEach((e) => {
      if (!/^https?:/i.test(e.content)) add(e.content, "page-metadata");
    });
  doc
    .querySelectorAll('[rel="author"],[itemprop="author"] [itemprop="name"]')
    .forEach((e) => add(e.textContent, "byline"));
  if (!found.length)
    for (const script of doc.querySelectorAll(
      'script[type="application/ld+json"]',
    )) {
      if ((script.textContent?.length ?? 0) > 100000) continue;
      try {
        const parsed = JSON.parse(script.textContent ?? "null");
        const entries = Array.isArray(parsed)
          ? parsed
          : [...(parsed?.["@graph"] ?? []), parsed];
        for (const item of entries) {
          if (!/Article|Posting|Report/i.test(String(item?.["@type"])))
            continue;
          for (const author of Array.isArray(item.author)
            ? item.author
            : [item.author])
            add(
              typeof author === "string" ? author : author?.name,
              "structured-data",
            );
        }
      } catch {
        /* Invalid publisher metadata is not an identity. */
      }
    }
  return found;
}
