import { stratify } from "d3-hierarchy";
import type { Packet } from "./model";
export type GoalNode = NonNullable<Packet["goalHierarchy"]>["nodes"][number];
export const parentIds = (n: GoalNode) =>
  n.parentIds ?? (n.parentId ? [n.parentId] : []);
/** Legacy tree helper; the interactive view uses goalGraph for multiple ends. */
export function goalTree(nodes: GoalNode[]) {
  return nodes.length
    ? stratify<GoalNode>()
        .id((n) => n.id)
        .parentId((n) => n.parentId)(nodes)
    : null;
}
export type GraphNode = {
  id: string;
  data: GoalNode;
  rank: number;
  parents: GraphNode[];
  children: GraphNode[];
};
export function goalGraph(nodes: GoalNode[]) {
  const all: GraphNode[] = nodes.map((data) => ({
    id: data.id,
    data,
    rank: -1,
    parents: [],
    children: [],
  }));
  const byId = new Map(all.map((n) => [n.id, n]));
  for (const n of all)
    for (const id of parentIds(n.data)) {
      const p = byId.get(id);
      if (p) {
        n.parents.push(p);
        p.children.push(n);
      }
    }
  const rank = (n: GraphNode): number =>
    n.rank >= 0
      ? n.rank
      : (n.rank = n.children.length
          ? 1 + Math.max(...n.children.map(rank))
          : 0);
  all.forEach(rank);
  const roots = all
    .filter((n) => !n.parents.length)
    .sort((a, b) => b.rank - a.rank);
  const depth = Math.max(0, ...all.map((n) => n.rank));
  const walk = (
    n: GraphNode | undefined,
    direction: "parents" | "children",
  ) => {
    const seen = new Set<string>(),
      pending = n ? [n] : [];
    while (pending.length) {
      const item = pending.pop()!;
      if (seen.has(item.id)) continue;
      seen.add(item.id);
      pending.push(...item[direction]);
    }
    return seen;
  };
  return {
    all,
    byId,
    roots,
    depth,
    ancestors: (n: GraphNode | undefined) => walk(n, "parents"),
    descendants: (n: GraphNode | undefined) => walk(n, "children"),
  };
}
export function goalAt(nodes: GoalNode[], region: string, offset: number) {
  const graph = goalGraph(nodes);
  return graph.all
    .filter(
      (n) =>
        n.data.regions.includes(region) &&
        (!n.data.span ||
          (n.data.span.region === region &&
            n.data.span.start <= offset &&
            n.data.span.end > offset)),
    )
    .sort(
      (a, b) =>
        Number(!!b.data.span) - Number(!!a.data.span) || a.rank - b.rank,
    )[0]?.data;
}
export type GoalGraph = ReturnType<typeof goalGraph>;
export function reelCandidates(
  graph: GoalGraph,
  selected: GraphNode | undefined,
  rank: number,
) {
  const up = graph.ancestors(selected),
    down = graph.descendants(selected);
  const ids = rank >= (selected?.rank ?? 0) ? up : down;
  const nodes = graph.all.filter((n) => n.rank === rank && ids.has(n.id));
  const ended =
    !!selected &&
    rank > selected.rank &&
    graph.roots.some((n) => up.has(n.id) && n.rank < rank);
  return { nodes, ended, ambiguous: nodes.length + Number(ended) > 1 };
}

type Interval = [number, number];
export function hierarchyLayout(graph: GoalGraph, height = 300, width = 320) {
  const columns = graph.depth + 1,
    cw = width / columns;
  const roots = graph.roots,
    multi = roots.length > 1;
  const lobes = roots.map((root, i) => ({
    root,
    end: (root.rank + 1) * cw,
    center:
      height *
      (multi ? 0.34 + (i * 0.47) / Math.max(1, roots.length - 1) : 0.5),
    half: height * (multi ? (i === 0 ? 0.42 : 0.32) : 0.5),
  }));
  const slices = (x: number): Interval[] => {
    const inset = x < 14 ? 14 - Math.sqrt(Math.max(0, 196 - (x - 14) ** 2)) : 0;
    const raw = lobes
      .filter((l) => x <= l.end)
      .map((l) => {
        const half = l.half * Math.pow(Math.max(0, 1 - x / l.end), 0.78);
        return [
          Math.max(inset, l.center - half),
          Math.min(height - inset, l.center + half),
        ] as Interval;
      })
      .filter(([a, b]) => b > a + 0.001)
      .sort((a, b) => a[0] - b[0]);
    const result: Interval[] = [];
    for (const [a, b] of raw) {
      const last = result.at(-1);
      if (last && a <= last[1]) last[1] = Math.max(last[1], b);
      else result.push([a, b]);
    }
    return result;
  };
  const outline = lobes.map((l) => {
    const points = Array.from({ length: 81 }, (_, i) => {
      const x = (l.end * i) / 80,
        inset = x < 14 ? 14 - Math.sqrt(Math.max(0, 196 - (x - 14) ** 2)) : 0;
      const half = l.half * Math.pow(Math.max(0, 1 - x / l.end), 0.78);
      return {
        x,
        top: Math.max(inset, l.center - half),
        bottom: Math.min(height - inset, l.center + half),
      };
    });
    return `M${points.map((p) => `${p.x},${p.top}`).join(" L")} L${[...points]
      .reverse()
      .map((p) => `${p.x},${p.bottom}`)
      .join(" L")} Z`;
  });
  const leafOrder = new Map(
    graph.all.filter((n) => !n.children.length).map((n, i) => [n.id, i]),
  );
  const center = (n: GraphNode) => {
    const leaves = [...graph.descendants(n)].filter((id) => leafOrder.has(id));
    return (
      leaves.reduce((s, id) => s + leafOrder.get(id)!, 0) /
      Math.max(1, leaves.length)
    );
  };
  const tiles = [];
  for (let rank = 0; rank < columns; rank++) {
    const x = rank * cw,
      left = slices(x),
      right = slices(x + cw);
    // Partition the actual widest edge, not an unclipped rectangular grid.
    // Each tile therefore retains its whole longest vertical edge (>=50%).
    const total = (is: Interval[]) => is.reduce((s, [a, b]) => s + b - a, 0);
    const intervals = total(left) >= total(right) ? left : right;
    const nodes = graph.all
      .filter((n) => n.rank === rank)
      .sort(
        (a, b) =>
          Number(!a.parents.length) - Number(!b.parents.length) ||
          center(a) - center(b),
      );
    let assigned = 0;
    for (
      let bin = 0;
      bin < intervals.length && assigned < nodes.length;
      bin++
    ) {
      const [top, bottom] = intervals[bin];
      const available = nodes.length - assigned;
      const count =
        bin === intervals.length - 1
          ? available
          : Math.max(
              1,
              Math.min(
                available - (intervals.length - bin - 1),
                Math.round(
                  (nodes.length * (bottom - top)) /
                    Math.max(1, total(intervals)),
                ),
              ),
            );
      for (let i = 0; i < count && assigned < nodes.length; i++) {
        const node = nodes[assigned++],
          y = top + ((bottom - top) * i) / count,
          h = (bottom - top) / count;
        let area = 0,
          sx = 0,
          sy = 0;
        for (let dx = 1; dx < cw; dx += 2)
          for (const [a, b] of slices(x + dx)) {
            const lo = Math.max(a, y),
              hi = Math.min(b, y + h),
              mass = Math.max(0, hi - lo);
            area += mass;
            sx += (x + dx) * mass;
            sy += ((lo + hi) / 2) * mass;
          }
        let dotX = area ? sx / area : x + cw * 0.35,
          dotY = area ? sy / area : y + h / 2;
        const spans = slices(dotX)
          .map(([a, b]) => [Math.max(a, y), Math.min(b, y + h)] as Interval)
          .filter(([a, b]) => b > a);
        if (spans.length) {
          const span = spans.reduce((a, b) =>
            Math.abs((a[0] + a[1]) / 2 - dotY) <
            Math.abs((b[0] + b[1]) / 2 - dotY)
              ? a
              : b,
          );
          dotY = Math.max(
            span[0] + Math.min(2, (span[1] - span[0]) / 2),
            Math.min(span[1] - Math.min(2, (span[1] - span[0]) / 2), dotY),
          );
        }
        const visible = (edge: Interval[]) =>
          edge.reduce(
            (sum, [a, b]) =>
              sum + Math.max(0, Math.min(b, y + h) - Math.max(a, y)),
            0,
          );
        tiles.push({
          node,
          x,
          y,
          width: cw,
          height: h,
          dotX,
          dotY,
          exposure: Math.max(visible(left), visible(right)) / h,
        });
      }
    }
  }
  return { width, height, outline, tiles, columns, slices };
}
