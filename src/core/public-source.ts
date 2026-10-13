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
/** Resolve only explicitly linked GitHub profiles; never guess an identity. */
export function contextSourceURL(input: string, useGitHub: boolean): URL {
  const url = publicURL(input);
  const match = url.pathname.match(
    /^\/([A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?)\/?$/,
  );
  if (
    useGitHub &&
    url.hostname === "github.com" &&
    match &&
    ![
      "about",
      "features",
      "topics",
      "marketplace",
      "pricing",
      "settings",
      "login",
      "signup",
      "explore",
      "sponsors",
      "organizations",
    ].includes(match[1].toLowerCase())
  )
    return new URL(`https://api.github.com/users/${match[1]}`);
  return url;
}

/** Accept an explicit repository or file link, never infer one from a site name. */
export function githubRepository(input: string) {
  const url = publicURL(input);
  if (url.hostname !== "github.com") return null;
  const parts = url.pathname.split("/").filter(Boolean).map(decodeURIComponent);
  const [owner, repository, kind, ...tail] = parts;
  if (
    !/^[A-Za-z0-9-]{1,39}$/.test(owner ?? "") ||
    !/^[A-Za-z0-9_.-]{1,100}$/.test(repository ?? "") ||
    repository === "." ||
    repository === ".." ||
    (kind && (kind !== "blob" || tail.length < 2))
  )
    return null;
  if (tail.some((p) => p === "." || p === ".." || /[\\\x00-\x1f]/.test(p)))
    return null;
  return { owner, repository: repository.replace(/\.git$/, ""), tail };
}
