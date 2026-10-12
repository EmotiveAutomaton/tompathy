import type { ContextItem } from "./model";
import { contextIdentity } from "./context";
import { parseContextSource } from "./context-source";
export const COLLECT_LIMITS = {
  urls: 3,
  bytes: 256000,
  timeoutMs: 30000,
  excerpt: 12000,
};
import { publicURL } from "./public-source";
export { publicURL, contextSourceURL } from "./public-source";
export async function retrieveContextSource(
  url: URL,
  signal: AbortSignal,
  fetcher: typeof fetch = fetch,
) {
  const response = await fetcher(url.href, {
    signal,
    credentials: "omit",
    redirect: "error",
    referrerPolicy: "no-referrer",
    cache: "no-store",
  });
  if (!response.ok) throw Error(`Source returned HTTP ${response.status}.`);
  const type = response.headers.get("content-type") ?? "";
  const githubProfile =
    url.hostname === "api.github.com" &&
    /^\/users\/[A-Za-z0-9-]+$/.test(url.pathname);
  if (
    !/text\/(html|plain|markdown|xml)/i.test(type) &&
    !/application\/(rss\+xml|atom\+xml|xml)/i.test(type) &&
    !(githubProfile && /application\/json/i.test(type))
  )
    throw Error("Choose an HTML, text, Markdown, RSS, or Atom source.");
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
  const parsed = parseContextSource(text, type, url);
  const excerpt = parsed.excerpt;
  if (!excerpt) throw Error("No readable excerpt in this source.");
  const item: ContextItem = {
    id: await contextIdentity(url.href, excerpt),
    source: url.href,
    excerpt,
    retrievedAt: new Date().toISOString(),
    selected: false,
    lineage: "public-url",
    facts: parsed.facts,
  };
  return { item, links: parsed.links };
}
export async function retrieve(
  url: URL,
  signal: AbortSignal,
  fetcher: typeof fetch = fetch,
): Promise<ContextItem> {
  return (await retrieveContextSource(url, signal, fetcher)).item;
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
