import { ghostInk, grade, readingHelp } from "../core/ghost";
import type { Artifact, GhostReading, Packet } from "../core/model";
export function ReadingText({
  text,
  start = 0,
  emphasis = [],
  reading,
  packet,
  annotate = true,
}: {
  text: string;
  start?: number;
  emphasis?: Artifact["regions"][number]["emphasis"];
  reading?: GhostReading;
  packet?: Packet | null;
  annotate?: boolean;
}) {
  const stops = [
    ...new Set([
      0,
      text.length,
      ...emphasis
        .flatMap((e) => [
          Math.max(0, e.start - start),
          Math.min(text.length, e.end - start),
        ])
        .filter((n) => n > 0 && n < text.length),
    ]),
  ].sort((a, b) => a - b);
  const ink =
    reading && reading.kind !== "unknown"
      ? ghostInk(reading.kind, [38, 58, 50], [250, 249, 245])
      : null;
  return (
    <span
      data-tompathy-help={
        annotate ? JSON.stringify(readingHelp(reading, packet)) : undefined
      }
      data-ghost-kind={ink ? reading?.kind : undefined}
      className={ink ? "tompathy-ghost" : undefined}
      style={
        ink
          ? {
              color: ink.color,
              backgroundColor: ink.background,
              fontVariationSettings: `"GRAD" ${grade(reading!.confidence)}`,
            }
          : undefined
      }
    >
      {stops.slice(0, -1).map((a, i) => {
        const bold = emphasis.some(
            (e) => e.start <= start + a && e.end > start + a,
          ),
          value = text.slice(a, stops[i + 1]);
        return bold ? (
          ink ? (
            <span key={a} className="tompathy-emphasis">
              {value}
            </span>
          ) : (
            <strong key={a}>{value}</strong>
          )
        ) : (
          value
        );
      })}
    </span>
  );
}
export function textOffset(
  el: HTMLElement,
  x: number,
  y: number,
  length: number,
) {
  const caret = document.caretRangeFromPoint(x, y);
  if (!caret || !el.contains(caret.startContainer)) return 0;
  const range = document.createRange();
  range.selectNodeContents(el);
  range.setEnd(caret.startContainer, caret.startOffset);
  return Math.min(length - 1, range.toString().length);
}
