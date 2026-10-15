import type { Artifact, ContextItem } from "./model";
import { contextIdentity } from "./context";
import { contextSourceURL, publicURL } from "./public-source";
import { COLLECT_LIMITS, retrieveContextSource } from "./collector";
import { githubRepository, retrieveGitHubContext } from "./github-context";

const CACHE_TTL = 15 * 60 * 1000;
const cache = new Map<
  string,
  { expires: number; value: Awaited<ReturnType<typeof retrieveContextSource>> }
>();
export type ContextReport = {
  attempted: number;
  collected: number;
  cached: number;
  failures: { source: string; reason: string }[];
  skipped: { source: string; reason: string }[];
};
export function clearContextCache() {
  cache.clear();
}

export async function bylineContext(
  artifact: Artifact,
  creator: string,
): Promise<ContextItem | null> {
  const attribution = artifact.authors?.find(
    (a) => a.label.toLocaleLowerCase() === creator.toLocaleLowerCase(),
  );
  if (!attribution) return null;
  const excerpt = `This page credits ${attribution.label} as its creator (${attribution.basis}). This is page-supplied attribution, not independently verified identity.`;
  return {
    id: await contextIdentity(artifact.source, excerpt),
    source: artifact.source,
    excerpt,
    retrievedAt: artifact.capturedAt,
    selected: false,
    lineage: "public-url",
    provenance: {
      author: creator,
      basis: "page-byline",
      linkedFrom: artifact.source,
    },
    facts: [
      {
        label: `Page byline: ${creator}`,
        quote: excerpt,
        source: artifact.source,
        dateKind: "undated",
      },
    ],
  };
}

/** Six sources, including at most one bounded repository lookup, on granted origins. */
export async function collectCreatorContext(options: {
  sources: { url: string; author: string }[];
  repositoryLinks?: string[];
  pageSource?: string;
  existingContext?: ContextItem[];
  creator: string;
  useGitHub: boolean;
  followLinks: boolean;
  signal: AbortSignal;
  onResult: (item: ContextItem) => void;
  onProgress: (completed: number, total: number, label: string) => void;
  fetcher?: typeof fetch;
  now?: () => number;
}) {
  const {
    creator,
    useGitHub,
    followLinks,
    signal,
    onResult,
    onProgress,
    fetcher = fetch,
    now = Date.now,
  } = options;
  const selectedSources = options.sources
    .filter((s) => s.author.toLocaleLowerCase() === creator.toLocaleLowerCase())
    .slice(0, 3);
  const seeds = [
    ...new Set(
      selectedSources.map((s) => contextSourceURL(s.url, useGitHub).href),
    ),
  ];
  const origins = new Set(seeds.map((s) => new URL(s).origin));
  const queue = seeds.map((url) => ({
    url,
    basis: "explicit-author-link" as "explicit-author-link" | "linked-source",
    linkedFrom:
      selectedSources.find(
        (s) => contextSourceURL(s.url, useGitHub).href === url,
      )?.url ?? url,
  }));
  const repository = useGitHub
    ? (options.repositoryLinks ?? []).find((url) => githubRepository(url))
    : undefined;
  if (repository && !seeds.includes(repository))
    queue.push({
      url: repository,
      basis: "linked-source",
      linkedFrom: options.pageSource ?? repository,
    });
  if (useGitHub) origins.add("https://api.github.com");
  const allowedOrigin = (url: string) =>
    useGitHub && githubRepository(url)
      ? "https://api.github.com"
      : new URL(url).origin;
  const seen = new Set(seeds),
    budget = followLinks ? 6 : queue.length;
  const report: ContextReport = {
    attempted: 0,
    collected: 0,
    cached: 0,
    failures: [],
    skipped: [],
  };
  const combined = AbortSignal.any([
    signal,
    AbortSignal.timeout(COLLECT_LIMITS.timeoutMs),
  ]);
  const check = () => {
    if (combined.aborted)
      throw Error(
        signal.aborted
          ? "Collection cancelled."
          : "Collection timed out after 30 seconds.",
      );
  };
  let repositoryRead = false;
  for (let i = 0; i < queue.length && i < budget; i++) {
    check();
    const job = queue[i];
    if (useGitHub && githubRepository(job.url)) {
      if (repositoryRead) {
        report.skipped.push({
          source: job.url,
          reason: "One-repository collection limit",
        });
        continue;
      }
      repositoryRead = true;
    }
    onProgress(
      i,
      queue.length,
      /github\.com/.test(new URL(job.url).hostname)
        ? "Fetching GitHub"
        : "Reading creator links",
    );
    report.attempted++;
    try {
      const hit = cache.get(job.url);
      const saved =
        useGitHub &&
        githubRepository(job.url) &&
        options.existingContext?.find(
          (item) =>
            item.source === job.url &&
            item.lineage === "public-url" &&
            item.facts?.length &&
            item.provenance?.author === creator &&
            now() - Date.parse(item.retrievedAt) >= 0 &&
            now() - Date.parse(item.retrievedAt) < CACHE_TTL,
        );
      let result: Awaited<ReturnType<typeof retrieveContextSource>>;
      if (saved) {
        result = { item: structuredClone(saved), links: [] };
        report.cached++;
      } else if (hit && hit.expires > now()) {
        result = structuredClone(hit.value);
        report.cached++;
      } else {
        result =
          useGitHub && githubRepository(job.url)
            ? await retrieveGitHubContext(
                publicURL(job.url),
                combined,
                fetcher,
                (step) =>
                  onProgress(i * 8 + step, queue.length * 8, "Fetching GitHub"),
              )
            : await retrieveContextSource(
                publicURL(job.url),
                combined,
                fetcher,
              );
        check();
        cache.delete(job.url);
        cache.set(job.url, {
          expires: now() + CACHE_TTL,
          value: structuredClone(result),
        });
        while (cache.size > 24) cache.delete(cache.keys().next().value!);
      }
      check();
      const item = {
        ...result.item,
        provenance: {
          author: creator,
          basis: job.basis,
          linkedFrom: job.linkedFrom,
        },
      };
      onResult(item);
      report.collected++;
      // One discovery hop from an explicit source; never recursively crawl.
      if (followLinks && job.basis === "explicit-author-link")
        for (const href of result.links) {
          const url = contextSourceURL(href, useGitHub).href;
          if (seen.has(url)) continue;
          seen.add(url);
          const reason = !origins.has(allowedOrigin(url))
            ? "Outside the explicitly granted source sites"
            : queue.length >= budget
              ? "Six-source collection limit"
              : null;
          if (reason) report.skipped.push({ source: url, reason });
          else queue.push({ url, basis: "linked-source", linkedFrom: job.url });
        }
    } catch (e) {
      check();
      report.failures.push({
        source: job.url,
        reason: e instanceof Error ? e.message : "Source unavailable",
      });
    }
    onProgress(
      i + 1,
      queue.length,
      `Read ${report.collected} of ${queue.length} sources${report.cached ? ` · ${report.cached} cached` : ""}`,
    );
  }
  check();
  return report;
}

export const dateKindLabel: Record<
  NonNullable<ContextItem["facts"]>[number]["dateKind"],
  string
> = {
  publication: "Published",
  event: "Listed event",
  "account-created": "Account created",
  "profile-updated": "Profile updated",
  "source-updated": "Source updated",
  undated: "Undated",
};
export function contextTimeline(items: ContextItem[], creator: string) {
  const sources = items.filter(
    (item) =>
      !item.provenance ||
      item.provenance.author.toLocaleLowerCase() ===
        creator.toLocaleLowerCase(),
  );
  const seen = new Set<string>();
  const facts = sources
    .flatMap((item) =>
      (
        item.facts ?? [
          {
            label: item.excerpt.slice(0, 160),
            quote: item.excerpt.slice(0, 1500),
            source: item.source,
            dateKind: "undated" as const,
          },
        ]
      ).map((fact) => ({
        ...fact,
        itemId: item.id,
        retrievedAt: item.retrievedAt,
        basis: item.provenance?.basis ?? item.lineage,
        linkedFrom: item.provenance?.linkedFrom,
      })),
    )
    .filter((f) => {
      const key = JSON.stringify([f.source, f.date, f.dateKind, f.label]);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  return {
    sources,
    dated: facts
      .filter((f) => f.date)
      .sort((a, b) => a.date!.localeCompare(b.date!)),
    undated: facts.filter((f) => !f.date),
  };
}
export function contextBrief(items: ContextItem[], creator: string) {
  const timeline = contextTimeline(items, creator);
  const line = (f: (typeof timeline.dated)[number]) =>
    `${f.date ?? "Undated"} · ${dateKindLabel[f.dateKind]} · ${f.label}\n  Source: ${f.source}\n  Excerpt: ${f.quote}\n  Retrieved: ${f.retrievedAt} · Link basis: ${f.basis}`;
  return `Context for ${creator}\nSource-backed extraction; linked material is not independent identity verification. Dates retain their supplied precision. Publication and profile dates are not biographical event dates.\n\nTimeline\n${timeline.dated.map(line).join("\n\n") || "No explicit dates supplied."}\n\nUndated context\n${timeline.undated.map(line).join("\n\n") || "No undated context supplied."}`;
}
