import type { ContextItem } from "./model";
import { contextIdentity } from "./context";
import { readingRoot } from "./page";
export const COLLECT_LIMITS = {
  urls: 3,
  bytes: 256000,
  timeoutMs: 30000,
  excerpt: 12000,
};
export function publicURL(input: string): URL {
  const url = new URL(input.trim()),
    host = url.hostname.toLowerCase();
  if (
    url.protocol !== "https:" ||
    url.username ||
    url.password ||
    (url.port && url.port !== "443")
  )
    throw Error("Use a public HTTPS URL without credentials or a custom port.");
  if (
    !host.includes(".") ||
    /^[\d.]+$/.test(host) ||
    host.includes(":") ||
    /(^|\.)(localhost|local|internal|test|invalid|onion|home|lan)$/.test(
      host,
    ) ||
    host.endsWith(".arpa")
  )
    throw Error("Private, local, and IP-address sources are not supported.");
  url.hash = "";
  return url;
}
export async function retrieve(
  url: URL,
  signal: AbortSignal,
  fetcher: typeof fetch = fetch,
): Promise<ContextItem> {
  const response = await fetcher(url.href, {
    signal,
    credentials: "omit",
    redirect: "error",
    referrerPolicy: "no-referrer",
    cache: "no-store",
  });
  if (!response.ok) throw Error(`Source returned HTTP ${response.status}.`);
  const type = response.headers.get("content-type") ?? "";
  if (!/text\/(html|plain|markdown)/i.test(type))
    throw Error("Choose an HTML, plain text, or Markdown source.");
  if (Number(response.headers.get("content-length")) > COLLECT_LIMITS.bytes)
    throw Error("Source exceeds the 256 KB retrieval limit.");
  const reader = response.body?.getReader();
  if (!reader) throw Error("Source returned no readable body.");
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > COLLECT_LIMITS.bytes)
        throw Error("Source exceeds the 256 KB retrieval limit.");
      chunks.push(value);
    }
  } finally {
    await reader.cancel().catch(() => {});
  }
  const bytes = new Uint8Array(size);
  let offset = 0;
  for (const c of chunks) {
    bytes.set(c, offset);
    offset += c.length;
  }
  const text = new TextDecoder().decode(bytes);
  let excerpt = text;
  if (type.includes("html")) {
    const doc = new DOMParser().parseFromString(text, "text/html");
    doc
      .querySelectorAll(
        'script,style,nav,header,footer,form,iframe,noscript,[hidden],[aria-hidden="true"]',
      )
      .forEach((n) => n.remove());
    doc
      .querySelectorAll("p,h1,h2,h3,h4,li,div,section,br")
      .forEach((n) => n.append(doc.createTextNode(" ")));
    excerpt = readingRoot(doc).root.textContent ?? "";
  }
  excerpt = excerpt
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, COLLECT_LIMITS.excerpt);
  if (!excerpt) throw Error("No readable excerpt in this source.");
  return {
    id: await contextIdentity(url.href, excerpt),
    source: url.href,
    excerpt,
    retrievedAt: new Date().toISOString(),
    selected: false,
    lineage: "public-url",
  };
}
export async function collectSources(
  inputs: string[],
  signal: AbortSignal,
  onResult: (item: ContextItem | { source: string; error: string }) => void,
) {
  const urls = [
    ...new Set(inputs.filter(Boolean).map((x) => publicURL(x).href)),
  ];
  if (!urls.length || urls.length > 3)
    throw Error("Choose between one and three public source URLs.");
  const timeout = AbortSignal.timeout(COLLECT_LIMITS.timeoutMs),
    combined = AbortSignal.any([signal, timeout]);
  for (const href of urls) {
    if (combined.aborted)
      throw Error(
        signal.aborted
          ? "Collection cancelled."
          : "Collection timed out after 30 seconds.",
      );
    try {
      onResult(await retrieve(new URL(href), combined));
    } catch (e) {
      if (combined.aborted)
        throw Error(
          signal.aborted
            ? "Collection cancelled."
            : "Collection timed out after 30 seconds.",
        );
      onResult({
        source: href,
        error: e instanceof Error ? e.message : "Retrieval failed.",
      });
    }
  }
}
