import type { ContextItem } from "./model";
// Same canonical source/excerpt identity used by Sounding Line's offline exporter.
export async function contextIdentity(source: string, excerpt: string) {
  const bytes = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(JSON.stringify([source, excerpt])),
  );
  return Array.from(new Uint8Array(bytes), (x) =>
    x.toString(16).padStart(2, "0"),
  ).join("");
}
export function mergeContext(
  existing: ContextItem[],
  incoming: ContextItem,
): ContextItem[] {
  // Repeated history is one source, not additional independent evidence.
  if (
    existing.some(
      (c) => c.source === incoming.source && c.excerpt === incoming.excerpt,
    )
  )
    return existing;
  return [...existing, incoming].slice(0, 30);
}
