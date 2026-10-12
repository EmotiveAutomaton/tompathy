import type { GhostReading, Packet } from "./model";

export const ghostLabels: Record<GhostReading["kind"], string> = {
  original: "Creator-written",
  edited: "Human-written, machine-polished",
  curated: "Curated / synthesized",
  ghost: "Unreviewed generation",
  unknown: "Involvement unknown",
};
type RGB = [number, number, number];
export const rgb = (css: string): RGB => {
  const values = css.match(/[\d.]+/g)?.map(Number);
  return values && values.length >= 3
    ? (values.slice(0, 3) as RGB)
    : [38, 58, 50];
};
const luminance = (c: RGB) =>
  c
    .map((v) => v / 255)
    .map((v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4))
    .reduce((sum, v, i) => sum + v * [0.2126, 0.7152, 0.0722][i], 0);
export function contrast(a: RGB, b: RGB) {
  const x = luminance(a),
    y = luminance(b);
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
}
const mix = (a: RGB, b: RGB, opacity: number): RGB =>
  a.map((v, i) => Math.round(v * opacity + b[i] * (1 - opacity))) as RGB;
const css = (c: RGB) => `rgb(${c.join(", ")})`;
export function ghostInk(
  kind: GhostReading["kind"],
  foreground: RGB,
  background: RGB,
) {
  // Opacity is composited into the ink, not the element: locks, selection and
  // tooltips remain opaque. The curator threshold uses the actual surface.
  const fallback: RGB =
    luminance(background) > 0.18 ? [0, 0, 0] : [255, 255, 255];
  const ink = contrast(foreground, background) >= 4.5 ? foreground : fallback;
  let opacity = kind === "edited" ? 0.95 : kind === "curated" ? 0.6 : 1;
  while (
    opacity < 1 &&
    contrast(mix(ink, background, opacity), background) < 4.5
  )
    opacity = Math.min(1, opacity + 0.005);
  return {
    color: css(kind === "ghost" ? background : mix(ink, background, opacity)),
    background: kind === "ghost" ? css(ink) : "transparent",
    opacity,
  };
}
export const grade = (confidence: number | null) =>
  confidence === null ? 0 : Math.round(-50 + 150 * confidence);
export function ghostAt(
  packet: Packet | null | undefined,
  maker: string | undefined,
  region: string,
  start: number,
  end: number,
) {
  return packet?.ghostReadings?.find(
    (g) =>
      g.maker === maker &&
      g.span.region === region &&
      g.span.start <= start &&
      g.span.end >= end,
  );
}
export type ReadingHelp = {
  kind: GhostReading["kind"];
  label: string;
  confidence: number | null;
  confidenceExplanation: string;
  summary: string;
  evidence: { source: string; text: string }[];
  fictional: boolean;
  prompt?: string;
};
export function readingHelp(
  reading: GhostReading | undefined,
  packet?: Pick<Packet, "evidence" | "origin"> | null,
): ReadingHelp {
  const seen = new Set<string>();
  const evidence = (reading?.evidence ?? [])
    .flatMap((id) => {
      const e = packet?.evidence.find((e) => e.id === id);
      if (!e || seen.has(e.excerpt)) return [];
      seen.add(e.excerpt);
      return [{ source: e.source, text: e.excerpt }];
    })
    .slice(0, 3);
  return {
    kind: reading?.kind ?? "unknown",
    label: ghostLabels[reading?.kind ?? "unknown"],
    confidence: reading?.confidence ?? null,
    confidenceExplanation:
      reading?.confidenceExplanation ?? "No confidence estimate was supplied.",
    summary:
      reading?.explanation ??
      "No sentence-level account was supplied. Original styling is retained.",
    evidence,
    prompt: reading?.kind === "ghost" ? reading.prompt : undefined,
    fictional: packet?.origin === "synthetic example",
  };
}
