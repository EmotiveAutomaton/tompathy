import type { Artifact, Hypothesis, Packet } from "./model";
import { sentences } from "./sentences";

const labels = [
  "Noticing pauses",
  "A quiet invitation",
  "Watching closely",
  "Trying again",
  "Making room",
  "Small details",
  "A modest claim",
  "A shared moment",
  "What comes next",
  "Room to linger",
  "Learning from others",
  "Uncertainty",
];
const leaders = [
  [1],
  [0, 0, 9],
  [1, 4, 1, 7],
  [2, 10, 3, 3],
  [5, 5, 4, 4],
  [6, 7, 8],
];
/** Separate written attention snapshots; these do not derive from the goal graph. */
export function exampleAttention(artifact: Artifact) {
  const support = (value: number) => ({
    value,
    scale: [0, 1] as [number, number],
    semantics: "relative" as const,
    meaning:
      "Hand-written demonstration of shifting attention; not live inference or a calibrated likelihood.",
  });
  const hypotheses: Hypothesis[] = labels.map((label, i) => ({
    id: `focus-${i}`,
    kind: "attention",
    interpretation: "current-attention",
    label,
    description: `A possible current attentional focus: ${label.toLowerCase()}. This is an independent illustration, not a node in the goal hierarchy.`,
    makers: ["maker-1"],
    regions: [],
    status: "hypothesis",
    support: null,
    evidence: [`e${Math.min(5, Math.floor(i / 3) + 1)}`],
  }));
  const currentAttention: NonNullable<Packet["currentAttention"]> =
    artifact.regions.flatMap((region, p) =>
      sentences(region.anchor.exact).map((sentence, j) => {
        const dominant = leaders[p]?.[j] ?? 0;
        const order = [
          ...new Set([
            dominant,
            (dominant + 3) % labels.length,
            (dominant + 1) % labels.length,
            11,
            (dominant + 7) % labels.length,
            (dominant + 5) % labels.length,
          ]),
        ];
        return {
          maker: "maker-1",
          span: { region: region.id, start: sentence.start, end: sentence.end },
          items: order.map((n, k) => ({
            hypothesis: `focus-${n}`,
            support: support([0.94, 0.61, 0.44, 0.28, 0.17, 0.1][k]),
          })),
        };
      }),
    );
  return { hypotheses, currentAttention };
}
export function attentionAt(
  packet: Packet | null,
  maker: string,
  region: string,
  offset: number,
): Hypothesis[] {
  const frame = packet?.currentAttention?.find(
    (f) =>
      f.maker === maker &&
      f.span.region === region &&
      f.span.start <= offset &&
      f.span.end > offset,
  );
  return (frame?.items ?? []).flatMap((item) => {
    const h = packet?.hypotheses.find(
      (h) => h.id === item.hypothesis && h.kind === "attention",
    );
    return h
      ? [
          {
            ...h,
            support: item.support === undefined ? h.support : item.support,
          },
        ]
      : [];
  });
}
