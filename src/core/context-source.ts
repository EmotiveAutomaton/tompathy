import type { ContextItem } from "./model";
import { calendarDate } from "./dates";
import { publicURL } from "./public-source";
import { readingRoot } from "./page";

export type ContextFact = NonNullable<ContextItem["facts"]>[number];
export type ParsedSource = {
  excerpt: string;
  facts: ContextFact[];
  links: string[];
};
const clean = (s: string | null | undefined, limit = 1500) =>
  (s ?? "").replace(/\s+/g, " ").trim().slice(0, limit);
const date = (s: string | null | undefined) => {
  if (!s) return;
  const iso = calendarDate(s);
  if (iso) return iso;
  // RSS dates are RFC 822/2822; do not guess dates from arbitrary prose.
  const rfc = s
    .trim()
    .match(
      /^(?:[A-Za-z]{3},\s*)?(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})\s+\d{2}:\d{2}(?::\d{2})?\s+(?:[A-Za-z]{1,5}|[+-]\d{4})$/,
    );
  if (!rfc || !Number.isFinite(Date.parse(s))) return;
  const month =
    [
      "jan",
      "feb",
      "mar",
      "apr",
      "may",
      "jun",
      "jul",
      "aug",
      "sep",
      "oct",
      "nov",
      "dec",
    ].indexOf(rfc[2].toLowerCase()) + 1;
  // Retain the source's calendar day rather than shift it into our timezone.
  return calendarDate(
    `${rfc[3]}-${String(month).padStart(2, "0")}-${rfc[1].padStart(2, "0")}`,
  );
};
const link = (value: string | null | undefined, base: URL) => {
  try {
    return value ? publicURL(new URL(value, base).href).href : undefined;
  } catch {
    return;
  }
};

/** Extract source statements and explicitly marked dates; never infer a biography. */
export function parseContextSource(
  text: string,
  type: string,
  url: URL,
): ParsedSource {
  const facts: ContextFact[] = [],
    links: string[] = [];
  const add = (
    label: string,
    quote: string,
    source = url.href,
    when?: string,
    kind: ContextFact["dateKind"] = "undated",
  ) => {
    if (!clean(label) || !clean(quote) || facts.length >= 20) return;
    const d = date(when);
    facts.push({
      label: clean(label, 600),
      quote: clean(quote),
      source,
      ...(d ? { date: d } : {}),
      dateKind: d ? kind : "undated",
    });
  };
  const addLink = (value: string | null | undefined) => {
    const href = link(value, url);
    if (href && href !== url.href && !links.includes(href) && links.length < 20)
      links.push(href);
  };
  if (
    url.hostname === "api.github.com" &&
    /^\/users\/[A-Za-z0-9-]+$/.test(url.pathname) &&
    /application\/json/i.test(type)
  ) {
    const p = JSON.parse(text);
    if (
      typeof p.login !== "string" ||
      p.login.toLowerCase() !== url.pathname.split("/").pop()!.toLowerCase()
    )
      throw Error(
        "The returned GitHub profile does not match the linked account.",
      );
    const fields: [string, unknown][] = [
      ["GitHub account", p.login],
      ["Name", p.name],
      ["Bio", p.bio],
      ["Company (self-described)", p.company],
      ["Website", p.blog],
      ["Location (self-described)", p.location],
    ];
    for (const [label, value] of fields)
      if (typeof value === "string" && clean(value))
        add(`${label}: ${value}`, value);
    if (typeof p.created_at === "string")
      add(
        "GitHub account created",
        `Account created: ${p.created_at}`,
        url.href,
        p.created_at,
        "account-created",
      );
    if (typeof p.updated_at === "string")
      add(
        "GitHub profile updated",
        `Profile updated: ${p.updated_at}`,
        url.href,
        p.updated_at,
        "profile-updated",
      );
    if (typeof p.blog === "string") addLink(p.blog);
    return {
      excerpt: facts
        .map((f) => (f.date ? f.quote : f.label))
        .join(". ")
        .slice(0, 12000),
      facts,
      links,
    };
  }
  if (/xml|rss|atom/i.test(type)) {
    const doc = new DOMParser().parseFromString(text, "application/xml");
    if (
      doc.querySelector("parsererror") ||
      !["rss", "feed", "rdf:rdf"].includes(
        doc.documentElement.tagName.toLowerCase(),
      )
    )
      throw Error("This source is not a readable RSS or Atom feed.");
    for (const item of Array.from(doc.querySelectorAll("item,entry")).slice(
      0,
      20,
    )) {
      const title = clean(item.querySelector("title")?.textContent, 600);
      const source =
        link(
          item.querySelector("link[href]")?.getAttribute("href") ??
            item.querySelector("link")?.textContent,
          url,
        ) ?? url.href;
      const published = item.querySelector("pubDate,published")?.textContent;
      const updated = item.querySelector("updated")?.textContent;
      const raw = published ?? updated;
      // Feed summaries may contain markup. Keep only inert readable text.
      const summary = clean(
        new DOMParser().parseFromString(
          item.querySelector("description,summary")?.textContent ?? title,
          "text/html",
        ).body.textContent,
        1000,
      );
      add(
        title || "Linked publication",
        `${title}. ${summary}${raw ? ` (Source date: ${clean(raw)})` : ""}`,
        source,
        raw ?? undefined,
        published ? "publication" : "source-updated",
      );
      addLink(source);
    }
    return {
      excerpt: facts
        .map(
          (f) =>
            `${f.date ?? "Undated"} [${f.dateKind}] ${f.quote} ${f.source}`,
        )
        .join("\n")
        .slice(0, 12000),
      facts,
      links,
    };
  }
  if (/html/i.test(type)) {
    const doc = new DOMParser().parseFromString(text, "text/html");
    const title = clean(
      doc.querySelector('meta[property="og:title"]')?.getAttribute("content") ??
        doc.querySelector("h1,title")?.textContent,
      600,
    );
    const published =
      doc
        .querySelector(
          'meta[property="article:published_time"],meta[itemprop="datePublished"]',
        )
        ?.getAttribute("content") ??
      doc
        .querySelector('time[itemprop="datePublished"],time[pubdate]')
        ?.getAttribute("datetime");
    if (published)
      add(
        title || "Linked publication",
        `${title} (Publication date: ${published})`,
        url.href,
        published,
        "publication",
      );
    let visited = 0;
    const structured = (value: unknown) => {
      if (++visited > 150 || !value || typeof value !== "object") return;
      if (Array.isArray(value)) {
        value.slice(0, 30).forEach(structured);
        return;
      }
      const p = value as Record<string, unknown>,
        kinds = Array.isArray(p["@type"]) ? p["@type"] : [p["@type"]];
      const name =
        typeof p.headline === "string"
          ? p.headline
          : typeof p.name === "string"
            ? p.name
            : title;
      if (
        kinds.some((k) =>
          [
            "Article",
            "BlogPosting",
            "NewsArticle",
            "ScholarlyArticle",
          ].includes(String(k)),
        ) &&
        typeof p.datePublished === "string" &&
        !published
      )
        add(
          name,
          `${name} (Publication date: ${p.datePublished})`,
          url.href,
          p.datePublished,
          "publication",
        );
      if (kinds.includes("Event") && typeof p.startDate === "string")
        add(
          name,
          `${name} (Listed event date: ${p.startDate})`,
          url.href,
          p.startDate,
          "event",
        );
      if (p["@graph"]) structured(p["@graph"]);
    };
    for (const script of Array.from(
      doc.querySelectorAll('script[type="application/ld+json"]'),
    ).slice(0, 10)) {
      try {
        structured(JSON.parse(script.textContent ?? ""));
      } catch {
        /* malformed metadata supplies no fact */
      }
    }
    doc.querySelectorAll('link[rel="alternate"]').forEach((el) => {
      if (/rss|atom/i.test(el.getAttribute("type") ?? ""))
        addLink(el.getAttribute("href"));
    });
    const anchors = Array.from(
      doc.querySelectorAll<HTMLAnchorElement>("a[href]"),
    );
    anchors.sort(
      (a, b) =>
        Number(!!b.querySelector("time")) - Number(!!a.querySelector("time")),
    );
    for (const a of anchors) {
      const href = link(a.getAttribute("href"), url);
      if (!href) continue;
      const u = new URL(href);
      if (
        u.hostname === "github.com" &&
        (a.rel.split(/\s+/).includes("me") ||
          /github|source|repository/i.test(a.textContent ?? ""))
      )
        addLink(href);
      if (
        u.origin === url.origin &&
        !u.search &&
        !/\/(?:login|admin|search|tags?|categories|contact)(?:\/|$)/i.test(
          u.pathname,
        ) &&
        (a.querySelector("time") ||
          /\/(?:about|bio|posts?|articles?|blog|writing|notes|feed|rss)(?:[./-]|$)/i.test(
            u.pathname,
          ))
      )
        addLink(href);
    }
    doc
      .querySelectorAll(
        'script,style,nav,header,footer,form,iframe,noscript,[hidden],[aria-hidden="true"]',
      )
      .forEach((n) => n.remove());
    const root = readingRoot(doc).root;
    for (const p of Array.from(root.querySelectorAll("p")).slice(0, 4)) {
      const quote = clean(p.textContent, 1000);
      if (quote.length > 25) add(quote.slice(0, 160), quote);
    }
    root
      .querySelectorAll("p,h1,h2,h3,h4,li,div,section,br")
      .forEach((n) => n.append(doc.createTextNode(" ")));
    const excerpt = clean(root.textContent, 10000);
    if (!facts.length && excerpt)
      add(title || "Linked source excerpt", excerpt.slice(0, 1000));
    return {
      excerpt: clean(
        excerpt +
          " " +
          facts
            .filter((f) => f.date)
            .map((f) => f.quote)
            .join(" "),
        12000,
      ),
      facts,
      links,
    };
  }
  const excerpt = clean(text, 12000);
  if (excerpt) add("Linked source excerpt", excerpt.slice(0, 1000));
  return { excerpt, facts, links };
}
