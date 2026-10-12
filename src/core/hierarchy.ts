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
  // Sentence choices get one and a half shares, rather than half the chart.
  const firstWidth = (width * 1.5) / (columns + 0.5);
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
    const sample = (px: number) => {
      const [top, bottom] = band(l, px, from, to);
      return { x: px, top, bottom };
    };
    const steps = Math.max(32, Math.ceil((end - x) * 1.25));
    const points: ReturnType<typeof sample>[] = [];
    let previous = sample(x);
    if (previous.bottom >= previous.top) points.push(previous);
    for (let i = 1; i <= steps; i++) {
      const next = sample(x + ((end - x) * i) / steps);
      const wasVisible = previous.bottom >= previous.top;
      const isVisible = next.bottom >= next.top;
      if (wasVisible !== isVisible) {
        let low = previous.x,
          high = next.x;
        for (let j = 0; j < 24; j++) {
          const mid = (low + high) / 2,
            p = sample(mid);
          if (p.bottom >= p.top === wasVisible) low = mid;
          else high = mid;
        }
        // Include the exact curved intersection, not a vertical cut at the
        // first sampled column. This removes the missing left-edge wedges.
        const edge = sample((low + high) / 2);
        edge.top = edge.bottom = (edge.top + edge.bottom) / 2;
        points.push(edge);
      }
      if (isVisible) points.push(next);
      previous = next;
    }
    const xy = (p: ReturnType<typeof sample>, bottom = false) =>
      `${p.x.toFixed(3)},${(bottom ? p.bottom : p.top).toFixed(3)}`;
    return `M${points.map((p) => xy(p)).join(" L")} L${points
      .reverse()
      .map((p) => xy(p, true))
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
    dotHeight: number;
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
    const key = `${parentKey ?? encodeURIComponent(l.root.id)}/${encodeURIComponent(node.id)}`;
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
    // The leaf tier follows the single shared back; higher tiers follow
    // their own ultimate root. Use the uncut band centre for a smooth leaf arc.
    const localY =
      node.rank === 0
        ? ((la + ((lb - la) * (from + to)) / 2) / height) * 2 - 1
        : from + to - 1;
    const desiredX = x + (end - x) * (0.46 + 0.4 * Math.abs(localY) ** 1.5);
    const radius = node.parents.length ? 1.6 : 2.7;
    // Fit the whole dot inside its brick, including the curved upper/lower edge.
    const safe = samples.filter((p) => {
      const cy = (p.a + p.b) / 2;
      return (
        p.x - x > radius + 1 &&
        end - p.x > radius + 1 &&
        [-1, 0, 1].every((dx) => {
          const [a, b] = band(l, p.x + dx * (radius + 1), from, to);
          return cy - a > radius + 1 && b - cy > radius + 1;
        })
      );
    });
    const middle = (safe.length ? safe : samples).reduce<
      (typeof samples)[number] | undefined
    >(
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
      dotHeight: middle.b - middle.a,
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
  // Find an inscribed label rectangle. The reader calls this once against the
  // whole world, so labels stay attached to cells while the camera moves.
  const labelBox = (
    tile: (typeof tiles)[number],
    view: { left: number; right: number; top: number; bottom: number },
    maxWidth: number,
    maxHeight: number,
  ) => {
    const lobe = lobes.find((l) => l.root.id === tile.rootId)!;
    const left = Math.max(tile.x, view.left),
      right = Math.min(tile.x + tile.width, view.right);
    let best = { x: tile.dotX, y: tile.dotY, width: 0, height: 0 },
      score = 0;
    for (let i = 1; i < 10; i++) {
      const x = left + ((right - left) * i) / 10;
      const half = Math.min(maxWidth / 2, x - left, right - x);
      if (half <= 0) continue;
      const spans = [-1, 0, 1].map((d) =>
        band(lobe, x + d * half, tile.from, tile.to),
      );
      const top = Math.max(view.top, ...spans.map((b) => b[0])),
        bottom = Math.min(view.bottom, ...spans.map((b) => b[1]));
      const height = Math.max(0, Math.min(maxHeight, bottom - top));
      const area = half * 2 * height;
      if (area > score) {
        score = area;
        best = { x, y: (top + bottom) / 2, width: half * 2, height };
      }
    }
    return best;
  };
  return {
    width,
    height,
    outline: lobes.map((l) => pathFor(l, 0, l.end, 0, 1)),
    tiles,
    columns,
    slices,
    dense,
    labelBox,
  };
}

export type HierarchyLayout = ReturnType<typeof hierarchyLayout>;
export function instanceNeighborhood(layout: HierarchyLayout, key?: string) {
  const tile = layout.tiles.find((t) => t.key === key);
  const ancestors = new Set<string>(),
    descendants = new Set<string>();
  let current = tile;
  while (current) {
    ancestors.add(current.key);
    current = layout.tiles.find((t) => t.key === current!.parentKey);
  }
  if (tile)
    for (const t of layout.tiles)
      if (t.key === tile.key || t.key.startsWith(tile.key + "/"))
        descendants.add(t.key);
  return { tile, ancestors, descendants };
}

export function instanceReelCandidates(
  graph: GoalGraph,
  layout: HierarchyLayout,
  selected: GraphNode | undefined,
  rank: number,
  key?: string,
) {
  const branch = instanceNeighborhood(layout, key);
  if (!branch.tile || branch.tile.node.id !== selected?.id)
    return reelCandidates(graph, selected, rank);
  const keys = rank >= selected.rank ? branch.ancestors : branch.descendants;
  const ids = new Set(
    layout.tiles.filter((t) => keys.has(t.key)).map((t) => t.node.id),
  );
  const nodes = graph.all.filter((n) => n.rank === rank && ids.has(n.id));
  const ended = rank > graph.byId.get(branch.tile.rootId)!.rank;
  return { nodes, ended, ambiguous: nodes.length + Number(ended) > 1 };
}
