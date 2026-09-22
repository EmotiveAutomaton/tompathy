import type { Artifact } from "./model";
export const normalize = (s: string) => s.replace(/\s+/gu, " ").trim();
export async function makeArtifact(
  texts: string[],
  source: string,
  title: string,
): Promise<Artifact> {
  const clean = texts.map(normalize).filter(Boolean).slice(0, 1500),
    text = clean.join("\n\n");
  const bytes = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(text),
  );
  const revision = Array.from(new Uint8Array(bytes), (x) =>
    x.toString(16).padStart(2, "0"),
  ).join("");
  let start = 0;
  return {
    id: source.split("#")[0],
    revision,
    title,
    source,
    capturedAt: new Date().toISOString(),
    truncated: texts.length > 1500,
    regions: clean.map((exact, index) => {
      const r = {
        id: `p${index + 1}`,
        anchor: {
          exact,
          index,
          start,
          prefix: text.slice(Math.max(0, start - 80), start),
          suffix: text.slice(start + exact.length, start + exact.length + 80),
        },
      };
      start += exact.length + 2;
      return r;
    }),
  };
}
