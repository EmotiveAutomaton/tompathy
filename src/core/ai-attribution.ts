import type { GhostReading, Packet } from "./model";
import { exampleAIMarks } from "./example-production";
import { ghostAt, ghostLabels } from "./ghost";

export type AIMark = { confidence: number | null; involvement: GhostReading["kind"]; description: string };

/** Display confidence is not the independent gate for attributing AI involvement. */
export function aiOutlineOpacity(confidence: number | null): number {
  return confidence === null ? 0.35 : Math.max(0, Math.min(1, confidence));
}

export function aiOutlineWidth(involvement: GhostReading["kind"]): number {
  return {original: 0.65, edited: 1, curated: 1.5, ghost: 2, unknown: 1}[involvement];
}

/** Generation attribution is separate from goal support and creator involvement. */
export function markedAINodes(packet: Packet | null, maker?: string): Map<string, AIMark> {
  const marks = new Map<string, AIMark>();
  const illustrative = packet?.origin === "synthetic example" && packet.provider.id === "tompathy-example";
  for (const node of packet?.goalHierarchy?.nodes ?? []) {
    if (maker && node.maker !== maker) continue;
    const example = illustrative ? exampleAIMarks[node.id as keyof typeof exampleAIMarks] : undefined;
    const attribution = node.aiAttribution;
    if (!example && !(attribution?.basis === "documented" || attribution?.basis === "calibrated" && attribution.probability > 0.5)) continue;
    const reading = node.span ? ghostAt(packet, node.maker, node.span.region, node.span.start, node.span.end) : undefined;
    const confidence = reading ? reading.confidence : attribution?.basis === "calibrated" ? attribution.probability : null;
    const involvement = reading?.kind ?? "unknown";
    const basis = example?.description ?? (attribution?.basis === "documented" ? "Documented AI involvement." : "Supplied calibrated AI attribution above 50%.");
    marks.set(node.id, {confidence, involvement, description: `${basis} ${ghostLabels[involvement]}. ${confidence === null ? "Confidence unknown (faint outline)." : `${Math.round(confidence * 100)}% confidence, matching the text when supplied.`} Opacity is confidence; thickness is more AI involvement. Unknown involvement uses a neutral width.`});
  }
  return marks;
}
