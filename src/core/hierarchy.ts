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
/** Unfold each supplied path into adjoining bands. Shared nodes get linked
 * visual instances, never a brick straddling unrelated parent outcomes. */
export function hierarchyLayout(graph: GoalGraph, height = 300, width = 320) {
  const columns = graph.depth + 1;
  const firstWidth =
    columns === 1
      ? width
      : Math.max(width / columns, Math.min(width * 0.45, height / 2));
  const edges = Array.from({ length: columns + 1 }, (_, i) =>
    i === 0
      ? 0
      : firstWidth +
        ((i - 1) * (width - firstWidth)) / Math.max(1, columns - 1),
  );
  const cw = firstWidth;
  const weights = new Map<string, number>();
  const weight = (n: GraphNode): number => {
    if (!weights.has(n.id))
      weights.set(
        n.id,
        n.children.length
          ? Math.min(
              100000,
              n.children.reduce((sum, c) => sum + weight(c), 0),
            )
          : 1,
      );
    return weights.get(n.id)!;
  };
  const total = graph.roots.reduce((sum, n) => sum + weight(n), 0) || 1;
  // One circular back supports every branch. Each lobe then narrows through
  // an inward-curving shoulder and ends in a small rounded cap.
  const fork = cw * 0.92;
  let cursor = 0;
  const lobes = graph.roots.map((root) => {
    const from = cursor;
    cursor += weight(root) / total;
    return { root, from, to: cursor, end: edges[root.rank + 1] };
  });
  const bounds = (l: (typeof lobes)[number], x: number): Interval => {
    const center = (height * (l.from + l.to)) / 2;
    const full = (height * (l.to - l.from)) / 2;
    const radius = Math.min(2.3, full * 0.12, (l.end - fork) * 0.15);
    const cap = l.end - radius;
    let half = full;
    if (x > cap) {
      half = radius * Math.sqrt(Math.max(0, 1 - ((x - cap) / radius) ** 2));
    } else if (x > fork) {
      const t = (x - fork) / (cap - fork);
      half = radius + (full - radius) * (1 - t) ** 2.4 * (1 + 2.4 * t);
    }
    return [center - half, center + half];
  };
  const back = (x: number): Interval => {
    const half =
      height *
      0.5 *
      Math.sqrt(1 - Math.pow(Math.max(0, 1 - x / (cw * 0.9)), 2));
    return [height / 2 - half, height / 2 + half];
  };
  const band = (
    l: (typeof lobes)[number],
    x: number,
    from: number,
    to: number,
  ): Interval => {
    const [a, b] = bounds(l, x),
      [lo, hi] = back(x);
    return [Math.max(lo, a + (b - a) * from), Math.min(hi, a + (b - a) * to)];
  };
  const slices = (x: number): Interval[] =>
    lobes
      .filter((l) => x <= l.end)
      .map((l) => band(l, x, 0, 1))
      .filter(([a, b]) => b > a);
  const pathFor = (
    l: (typeof lobes)[number],
    x: number,
    end: number,
    from: number,
    to: number,
  ) => {
    const points = Array.from({ length: 33 }, (_, i) => {
      const px = x + ((end - x) * i) / 32,
        [top, bottom] = band(l, px, from, to);
      return { x: px, top, bottom };
    }).filter((p) => p.bottom >= p.top);
    return `M${points.map((p) => `${p.x},${p.top}`).join(" L")} L${points
      .reverse()
      .map((p) => `${p.x},${p.bottom}`)
      .join(" L")} Z`;
  };
  const tiles: {
    node: GraphNode;
    key: string;
    parentKey?: string;
    rootId: string;
    from: number;
    to: number;
    x: number;
    y: number;
    width: number;
    height: number;
    dotX: number;
    dotY: number;
    exposure: number;
    path: string;
  }[] = [];
  const visit = (
    node: GraphNode,
    l: (typeof lobes)[number],
    from: number,
    to: number,
    parentKey?: string,
    parentRank = node.rank + 1,
  ) => {
    const key = `${parentKey ?? l.root.id}/${node.id}`;
    const x = edges[node.rank],
      end = edges[parentRank];
    const [la, lb] = bounds(l, x);
    const samples = Array.from({ length: 33 }, (_, i) => {
      const px = x + ((end - x) * i) / 32;
      const [a, b] = band(l, px, from, to);
      return { x: px, a, b };
    }).filter((p) => p.b >= p.a);
    const y = Math.min(...samples.map((p) => p.a)),
      extent = Math.max(...samples.map((p) => p.b)) - y;
    // Dot arcs follow this node's root lobe, independently of the shared back.
    const localY = from + to - 1;
    const desiredX = x + (end - x) * (0.34 + 0.3 * localY ** 2);
    const middle = samples.reduce<(typeof samples)[number] | undefined>(
      (best, p) =>
        !best || Math.abs(p.x - desiredX) < Math.abs(best.x - desiredX)
          ? p
          : best,
      undefined,
    ) ?? {
      x: x + cw / 2,
      a: la,
      b: lb,
    };
    const dotX = middle.x,
      dotY = (middle.a + middle.b) / 2;
    tiles.push({
      node,
      key,
      parentKey,
      rootId: l.root.id,
      from,
      to,
      x,
      y,
      width: end - x,
      height: extent,
      dotX,
      dotY,
      exposure: 1,
      path: pathFor(l, x, end, from, to),
    });
    let offset = from;
    for (const child of node.children) {
      const next = offset + ((to - from) * weight(child)) / weight(node);
      visit(child, l, offset, next, key, node.rank);
      offset = next;
    }
  };
  // Dense graphs use the existing scrollable detail surface; don't unfold an
  // exponentially branching DAG merely to discover it cannot fit on screen.
  const unfoldedCount = (n: GraphNode): number =>
    1 + n.children.reduce((s, c) => s + count(c), 0);
  const counts = new Map<string, number>();
  const count = (n: GraphNode): number => {
    if (!counts.has(n.id)) counts.set(n.id, Math.min(601, unfoldedCount(n)));
    return counts.get(n.id)!;
  };
  const dense = graph.roots.reduce((s, n) => s + count(n), 0) > 600;
  if (!dense) for (const l of lobes) visit(l.root, l, 0, 1);
  return {
    width,
    height,
    outline: lobes.map((l) => pathFor(l, 0, l.end, 0, 1)),
    tiles,
    columns,
    slices,
    dense,
  };
}
