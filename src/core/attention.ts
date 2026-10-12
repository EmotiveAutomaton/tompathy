import type { Artifact, Hypothesis, Packet } from "./model";
import { sentences } from "./sentences";
import { goalGraph, type GoalNode } from "./hierarchy";

const labels = [
  "Noticing hesitation",
  "An invitation to connect",
  "Watching the players",
  "Trying again",
  "Making room for others",
  "Small discoveries",
  "Keeping claims modest",
  "Sharing surprise",
  "What happens next",
  "Letting the moment linger",
  "Learning together",
  "Uncertainty",
  "Finding better words",
  "Resisting overstatement",
  "AI assistance",
  "Another perspective",
  "Playtesting",
  "Teaching without instructions",
];
const leaders = [
  [1],
  [0, 0, 9],
  [1, 4, 1, 7],
  [2, 10, 3, 3],
  [5, 5, 4, 4],
  [6, 7, 8],
  [7, 12, 13],
  [13, 11, 6],
  [5, 15, 17],
  [16, 11, 2],
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
        const dominant = leaders[p]?.[j] ?? 8;
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
          items:
            p === 6 && j === 2
              ? []
              : order.map((n, k) => ({
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
  const frame = packet?.currentAttention
    ?.filter(
      (f) =>
        f.maker === maker &&
        f.span.region === region &&
        f.span.start <= offset &&
        f.span.end > offset,
    )
    .sort((a, b) => a.span.end - a.span.start - (b.span.end - b.span.start))[0];
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

/** A union of supplied attention frames, never goal labels. Each frame counts
 * once even when its sentence belongs to several branches of the DAG. */
export function attentionForNode(
  packet: Packet,
  maker: string,
  node: GoalNode,
): Hypothesis[] {
  const graph = goalGraph(
    (packet.goalHierarchy?.nodes ?? []).filter((n) => n.maker === maker),
  );
  const ids = graph.descendants(graph.byId.get(node.id));
  const spans = graph.all
    .filter((n) => ids.has(n.id) && n.data.span)
    .map((n) => n.data.span!);
  const frames = (packet.currentAttention ?? []).filter(
    (f) =>
      f.maker === maker &&
      (spans.length
        ? spans.some(
            (s) =>
              s.region === f.span.region &&
              s.start < f.span.end &&
              s.end > f.span.start,
          )
        : node.regions.includes(f.span.region)),
  );
  const totals = new Map<string, { sum: number; supplied: boolean }>();
  if (frames.length === 1)
    return attentionAt(
      packet,
      maker,
      frames[0].span.region,
      frames[0].span.start,
    );
  for (const f of frames)
    for (const item of f.items) {
      const h = packet.hypotheses.find(
        (h) =>
          h.id === item.hypothesis &&
          h.kind === "attention" &&
          h.makers.includes(maker),
      );
      if (!h) continue;
      const support = item.support === undefined ? h.support : item.support;
      const old = totals.get(h.id) ?? { sum: 0, supplied: false };
      totals.set(h.id, {
        sum:
          old.sum +
          (support
            ? (support.value - support.scale[0]) /
              (support.scale[1] - support.scale[0])
            : 0),
        supplied: old.supplied || !!support,
      });
    }
  return [...totals].map(([id, total]) => ({
    ...packet.hypotheses.find((h) => h.id === id)!,
    support: total.supplied
      ? {
          value: total.sum / frames.length,
          scale: [0, 1] as [number, number],
          semantics: "relative" as const,
          meaning: `Mean normalized support across ${frames.length} supplied attention frames in this branch, counting absent items as zero. An overview, not a combined probability.`,
        }
      : null,
  }));
}
