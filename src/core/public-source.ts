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
