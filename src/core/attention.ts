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

/** Frequency × mean supplied confidence, with one unit of weight per sentence.
 * The most specific frame wins where frames overlap; shared graph paths and
 * splitting a frame into smaller frames cannot multiply an observation. */
export function attentionForNode(
  packet: Packet,
  maker: string,
  node: GoalNode,
): Hypothesis[] {
  const graph = goalGraph(
    (packet.goalHierarchy?.nodes ?? []).filter((n) => n.maker === maker),
  );
  if (!graph.byId.has(node.id)) return [];
  const ids = graph.descendants(graph.byId.get(node.id));
  const spans = graph.all
    .filter((n) => ids.has(n.id) && n.data.span)
    .map((n) => n.data.span!);
  const frames = (packet.currentAttention ?? []).filter(
    (f) => f.maker === maker,
  );
  const covered = packet.artifact.regions.flatMap((region) =>
    sentences(region.anchor.exact)
      .filter((s) =>
        spans.length
          ? spans.some(
              (span) =>
                span.region === region.id &&
                span.start < s.end &&
                span.end > s.start,
            )
          : node.regions.includes(region.id),
      )
      .map((s) => ({ ...s, region: region.id })),
  );
  if (covered.length === 1 && node.span)
    return attentionAt(packet, maker, node.span.region, node.span.start);
  const totals = new Map<
    string,
    { sum: number; mass: number; present: number; known: boolean }
  >();
  for (const sentence of covered) {
    const candidates = frames
      .filter(
        (f) =>
          f.span.region === sentence.region &&
          f.span.start < sentence.end &&
          f.span.end > sentence.start,
      )
      .sort((a, b) => a.span.end - a.span.start - (b.span.end - b.span.start));
    const cuts = [
      ...new Set([
        sentence.start,
        sentence.end,
        ...candidates.flatMap((f) => [
          Math.max(sentence.start, f.span.start),
          Math.min(sentence.end, f.span.end),
        ]),
      ]),
    ].sort((a, b) => a - b);
    const present = new Set<string>();
    for (let i = 0; i < cuts.length - 1; i++) {
      const frame = candidates.find(
        (f) => f.span.start <= cuts[i] && f.span.end >= cuts[i + 1],
      );
      const fraction =
        (cuts[i + 1] - cuts[i]) / (sentence.end - sentence.start);
      for (const item of frame?.items ?? []) {
        const h = packet.hypotheses.find(
          (h) =>
            h.id === item.hypothesis &&
            h.kind === "attention" &&
            h.makers.includes(maker),
        );
        if (!h) continue;
        const support = item.support === undefined ? h.support : item.support;
        const old = totals.get(h.id) ?? {
          sum: 0,
          mass: 0,
          present: 0,
          known: false,
        };
        if (support) {
          old.sum +=
            (fraction * (support.value - support.scale[0])) /
            (support.scale[1] - support.scale[0]);
          old.mass += fraction;
          old.known = true;
        }
        totals.set(h.id, old);
        present.add(h.id);
      }
    }
    for (const id of present) totals.get(id)!.present++;
  }
  return [...totals]
    .map(([id, total]) => {
      const h = packet.hypotheses.find((h) => h.id === id)!;
      const meaning =
        `Appears in ${total.present} of ${covered.length} selected sentences. ` +
        (total.known
          ? `Mean supplied confidence/support where scored: ${Math.round((total.sum / total.mass) * 100)}%. Size combines recurrence with supplied confidence; missing scores add no weight. This is relative prominence, not a combined probability.`
          : "Confidence is not supplied; no weighted score is inferred.");
      return {
        ...h,
        attentionOverview: {
          sentences: covered.length,
          occurrences: total.present,
        },
        description: `${h.description}\n\n${meaning}`,
        support: total.known
          ? {
              value: total.sum / covered.length,
              scale: [0, 1] as [number, number],
              semantics: "relative" as const,
              meaning,
            }
          : null,
      };
    })
    .sort((a, b) => (b.support?.value ?? -1) - (a.support?.value ?? -1));
}
