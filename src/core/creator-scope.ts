/** A separate admission to cross-work modeling. Context collection is not consent. */
export type WorkScopeEvidence = {
  route:
    | "owner"
    | "explicit-link"
    | "works-list"
    | "two-way-profile"
    | "search"
    | "same-name"
    | "style"
    | "pseudonymous-editor";
  hops: number;
  authorPage: string;
  work: string;
  linkedByNamedAuthor?: boolean;
  worksList?: string;
  backlink?: { href: string; rel: string[] };
};

export function creatorWorkScope(e: WorkScopeEvidence): {
  include: boolean;
  lattice: boolean;
  reason: string;
} {
  const deny = (reason: string) => ({ include: false, lattice: false, reason });
  if (!Number.isInteger(e.hops) || e.hops < 0 || e.hops > 2)
    return deny("At most two explicit hops");
  if (e.route === "owner")
    return { include: true, lattice: true, reason: "Owner-supplied work" };
  if (!e.linkedByNamedAuthor)
    return deny("No explicit link by the named author");
  let author: URL, work: URL;
  try {
    author = new URL(e.authorPage);
    work = new URL(e.work);
    if (
      ![author, work].every(
        (u) =>
          ["https:", "http:"].includes(u.protocol) &&
          !u.username &&
          !u.password,
      )
    )
      return deny("Invalid public source URL");
  } catch {
    return deny("Invalid source URL");
  }
  if (e.route === "explicit-link" && e.hops === 1)
    return {
      include: true,
      lattice: false,
      reason: "Context only: explicit work link",
    };
  if (e.route === "works-list" && e.hops >= 1 && e.worksList) {
    try {
      if (new URL(e.worksList).origin === author.origin)
        return {
          include: true,
          lattice: true,
          reason: "Author-published works list",
        };
    } catch {
      /* Invalid list is excluded. */
    }
  }
  if (
    e.route === "two-way-profile" &&
    e.hops === 2 &&
    e.backlink?.rel.some((r) => r.toLowerCase() === "me")
  ) {
    try {
      const backlink = new URL(e.backlink.href);
      backlink.hash = "";
      author.hash = "";
      if (backlink.href === author.href)
        return {
          include: true,
          lattice: true,
          reason: "Explicit profile with rel=me backlink",
        };
    } catch {
      /* Invalid backlink is excluded. */
    }
  }
  return deny("No qualifying consent route; no identity inference");
}
