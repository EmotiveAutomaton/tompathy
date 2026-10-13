import { githubRepository } from "./public-source";
import { readBoundedBody } from "./collector";
import { contextIdentity } from "./context";
import { calendarDate } from "./dates";
import type { ContextItem } from "./model";
export { githubRepository } from "./public-source";

/** At most eight public, unauthenticated requests; no crawling or code search. */
export async function retrieveGitHubContext(
  url: URL,
  signal: AbortSignal,
  fetcher: typeof fetch = fetch,
  onStep: (completed: number) => void = () => {},
) {
  const repo = githubRepository(url.href);
  if (!repo) throw Error("Not an explicit GitHub repository or file link.");
  const base = `https://api.github.com/repos/${repo.owner}/${repo.repository}`;
  let requests = 0;
  const json = async (path: string, missingOK = false): Promise<any> => {
    signal.throwIfAborted();
    if (++requests > 8) throw Error("GitHub request budget reached.");
    const response = await fetcher(base + path, {
      signal,
      credentials: "omit",
      redirect: "error",
      referrerPolicy: "no-referrer",
      cache: "no-store",
      headers: {
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
      },
    });
    if (missingOK && response.status === 404) {
      await response.body?.cancel();
      return null;
    }
    if (!response.ok) {
      await response.body?.cancel();
      throw Error(
        response.status === 403 || response.status === 429
          ? "GitHub access or rate limit reached; no automatic retries."
          : `GitHub returned HTTP ${response.status}.`,
      );
    }
    if (!/application\/json/i.test(response.headers.get("content-type") ?? ""))
      throw Error("GitHub did not return JSON.");
    const value = JSON.parse(await readBoundedBody(response));
    onStep(requests);
    return value;
  };
  const metadata = await json("");
  if (metadata.private !== false)
    throw Error("Only public GitHub repositories are supported.");
  const home = `https://github.com/${repo.owner}/${repo.repository}`;
  const facts: NonNullable<ContextItem["facts"]> = [
    {
      label: repo.tail.length
        ? "Explicit source-file link"
        : "Explicit repository link; article file not established",
      quote: `${home}. ${String(metadata.description ?? "").slice(0, 500)} Repository ownership and commit attribution do not establish who wrote the current page.`,
      source: url.href,
      dateKind: "undated",
    },
  ];
  let ref = String(metadata.default_branch ?? ""),
    file = "",
    excerpt = "";
  if (repo.tail.length) {
    // Branch names may contain slashes. Resolve against the Contents API rather
    // than guessing that the first path segment is always the complete ref.
    for (let split = 1; split <= Math.min(3, repo.tail.length - 1); split++) {
      ref = repo.tail.slice(0, split).join("/");
      const candidate = repo.tail.slice(split).join("/");
      const result = await json(
        `/contents/${candidate.split("/").map(encodeURIComponent).join("/")}?ref=${encodeURIComponent(ref)}`,
        true,
      );
      if (!result || result.type !== "file" || result.path !== candidate)
        continue;
      file = candidate;
      if (result.encoding === "base64" && typeof result.content === "string") {
        const bytes = Uint8Array.from(
          atob(result.content.replace(/\s/g, "")),
          (c) => c.charCodeAt(0),
        );
        const text = new TextDecoder().decode(bytes);
        if (!text.includes("\0")) excerpt = text.slice(0, 1800);
      }
      break;
    }
    if (!file)
      throw Error(
        "The linked file/ref could not be resolved within the bounded GitHub lookup.",
      );
    facts.push({
      label: `Source file: ${file}`.slice(0, 600),
      quote:
        `Ref: ${ref}. ${excerpt || "No readable text returned for this file."}`.slice(
          0,
          1500,
        ),
      source: url.href,
      dateKind: "undated",
    });
  }
  const commits = await json(
    `/commits?per_page=3&sha=${encodeURIComponent(ref)}${file ? `&path=${encodeURIComponent(file)}` : ""}`,
  );
  if (!Array.isArray(commits))
    throw Error("GitHub returned an unexpected commit list.");
  let detailUnavailable = "";
  for (const commit of commits.slice(0, 3)) {
    if (!/^[a-f0-9]{40}$/i.test(commit.sha ?? "")) continue;
    const info = commit.commit ?? {},
      date = calendarDate(String(info.author?.date ?? "").slice(0, 10));
    let patch = "";
    if (file && requests < 8 && !detailUnavailable) {
      try {
        const detail = await json(`/commits/${commit.sha}`);
        const change = detail.files?.find((f: any) => f.filename === file);
        patch = change
          ? ` Change: ${change.status}; +${change.additions}/−${change.deletions}. ${String(change.patch ?? "No text patch supplied.").slice(0, 700)}`
          : " This response did not include the file patch.";
      } catch (e) {
        signal.throwIfAborted();
        detailUnavailable =
          e instanceof Error ? e.message : "Details unavailable";
      }
    }
    if (detailUnavailable)
      patch = ` Commit metadata retained; patch lookup stopped: ${detailUnavailable}`;
    facts.push({
      label:
        `${file ? "File revision" : "Repository commit (not page-specific)"}: ${String(info.message ?? "").split("\n")[0]}`.slice(
          0,
          600,
        ),
      quote:
        `Git-recorded author: ${String(info.author?.name ?? "unknown")}; author timestamp: ${String(info.author?.date ?? "unknown")}; committer timestamp: ${String(info.committer?.date ?? "unknown")}. ${String(info.message ?? "").slice(0, 400)}${patch}`.slice(
          0,
          1500,
        ),
      source: `${home}/commit/${commit.sha}`,
      ...(date
        ? { date, dateKind: "source-updated" as const }
        : { dateKind: "undated" as const }),
    });
  }
  const summary = facts.map((f) => `${f.label}\n${f.quote}`).join("\n\n");
  const item: ContextItem = {
    id: await contextIdentity(url.href, summary),
    source: url.href,
    excerpt: summary.slice(0, 12000),
    retrievedAt: new Date().toISOString(),
    selected: false,
    lineage: "public-url",
    facts,
  };
  return { item, links: [] as string[] };
}
