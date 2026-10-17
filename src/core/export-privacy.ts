/** Usernames are local UI metadata, never part of a portable reading. */
export function exportSafe<T>(value: T): T {
  const names = new Map<string, string>();
  const visit = (node: unknown) => {
    if (!node || typeof node !== "object") return;
    const row = node as Record<string, unknown>;
    const byline = row.artifact && typeof row.artifact === "object" && Array.isArray((row.artifact as Record<string, unknown>).authors) && ((row.artifact as Record<string, unknown>).authors as unknown[]).length > 0;
    if (row.provider && typeof row.provider === "object" && (row.provider as Record<string, unknown>).mode === "preview" && (byline || Array.isArray(row.makers) && row.makers.some(m => m.kind === "person" || m.localLabel))) {
      throw Error("Per-person research preview readings stay local and cannot be exported.");
    }
    if (typeof row.localLabel === "string" && typeof row.label === "string") names.set(row.localLabel, row.label);
    Object.values(row).forEach(visit);
  };
  visit(value);
  const redact = (node: unknown, field = ""): unknown => {
    if (typeof node === "string") {
      let text = node;
      for (const [name, pseudonym] of names) {
        if (name && text.includes(name)) {
          if (["exact", "prefix", "suffix", "revision"].includes(field)) throw Error("An editor username occurs in the captured source text. This reading stays local so its exact text anchors are preserved.");
          text = text.split(name).join(pseudonym);
        }
      }
      return text;
    }
    if (Array.isArray(node)) return node.map(item => redact(item, field));
    if (node && typeof node === "object") return Object.fromEntries(Object.entries(node).filter(([key]) => key !== "localLabel").map(([key, item]) => [key, redact(item, key)]));
    return node;
  };
  return redact(value) as T;
}
