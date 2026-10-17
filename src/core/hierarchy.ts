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
  if (byId.size !== all.length) throw Error("Duplicate goal hierarchy IDs");
  for (const n of all)
    for (const id of parentIds(n.data)) {
      const p = byId.get(id);
      if (!p) throw Error("Missing goal hierarchy parent");
      if (!n.parents.includes(p)) {
        n.parents.push(p);
        p.children.push(n);
      }
    }
  // Rank bottom-up without recursion; malformed direct callers fail explicitly.
  const remaining = new Map(all.map((n) => [n.id, n.children.length]));
  const pending = all.filter((n) => !n.children.length);
  for (const n of pending) n.rank = 0;
  for (let i = 0; i < pending.length; i++) {
    const n = pending[i];
    for (const parent of n.parents) {
      parent.rank = Math.max(parent.rank, n.rank + 1);
      remaining.set(parent.id, remaining.get(parent.id)! - 1);
      if (remaining.get(parent.id) === 0) pending.push(parent);
    }
  }
  if (pending.length !== all.length)
    throw Error("Goal hierarchy must be acyclic");
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
export function goalAt(
  nodes: GoalNode[],
  region: string,
  offset: number,
  graph = goalGraph(nodes),
) {
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
/** Each node has one visual home. A spanning forest packs the bricks; supplied
 * extra parents remain explicit links and participate in inspection and reels. */
export function hierarchyLayout(
  graph: GoalGraph,
  height = 300,
  width = 320,
  tierShares?: number[],
) {
  height = Number.isFinite(height) && height > 0 ? height : 300;
  width = Number.isFinite(width) && width > 0 ? width : 320;
  const columns = graph.depth + 1;
  const owner = new Map(
    graph.all.flatMap((n) =>
      n.parents.length ? [[n.id, n.parents[0].id] as const] : [],
    ),
  );
  const owned = (n: GraphNode) =>
    n.children.filter((c) => owner.get(c.id) === n.id);
  // Give a secondary end a branch when its shared children can move without
  // emptying another parent. This is placement, never a preferred interpretation.
  for (const n of [...graph.all].sort((a, b) => b.rank - a.rank)) {
    if (!n.children.length || owned(n).length) continue;
    const movable = [...n.children].reverse().find((c) => {
      const previous = graph.byId.get(owner.get(c.id) ?? "");
      return previous && owned(previous).length > 1;
    });
    if (movable) owner.set(movable.id, n.id);
  }
  // Favor the most detailed tier that is still practical to target at overview.
  // On a long essay that is usually the section tier, not hundreds of sentences.
  const counts = Array.from(
    { length: columns },
    (_, rank) => graph.all.filter((n) => n.rank === rank).length,
  );
  const useful =
    counts
      .map((count, rank) => ({ count, rank }))
      .filter(
        (t) => t.rank < columns - 1 && t.count > 1 && height / t.count >= 5,
      )
      .sort((a, b) => b.count - a.count)[0]?.rank ?? 0;
  const defaults = counts.map((_, rank) =>
    rank === useful ? 2.35 : rank === 0 ? 1.3 : rank === columns - 1 ? 0.85 : 1,
  );
  const shares =
    tierShares?.length === columns &&
    tierShares.every((n) => Number.isFinite(n) && n > 0)
      ? tierShares
      : defaults;
  // Normalize before summing so extreme imported widths cannot overflow or
  // collapse a tier to zero. User-resized widths keep their proportions.
  const largestShare = Math.max(...shares);
  const normalized = shares.map((share) =>
    Math.max(1e-5, share / largestShare),
  );
  const sum = normalized.reduce((a, b) => a + b, 0);
  const edges = [0];
  for (const share of normalized)
    edges.push(edges.at(-1)! + (width * share) / sum);
  const firstWidth = edges[1];
  const cw = firstWidth;
  const weights = new Map<string, number>();
  const weight = (n: GraphNode): number => {
    if (!weights.has(n.id))
      weights.set(
        n.id,
        owned(n).length
          ? Math.min(
              100000,
              owned(n).reduce((sum, c) => sum + weight(c), 0),
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
    const steps = Math.max(96, Math.ceil((end - x) * 2));
    const points: ReturnType<typeof sample>[] = [];
    let previous = sample(x);
    if (previous.bottom >= previous.top) points.push(previous);
    for (let i = 1; i <= steps; i++) {
      const next = sample(
        x + (end - x) * Math.sin((Math.PI * i) / (2 * steps)) ** 2,
      );
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
    const leafY = height * (l.from + ((l.to - l.from) * (from + to)) / 2);
    const v = (leafY / height) * 2 - 1;
    // An analytic inset ellipse, shared by every leaf, never snapped to samples.
    // Analytic curves avoid snapping different cells to a coarse sampling grid.
    // The whole leaf arc stays before the forward taper, inside its own bands.
    const dotX =
      node.rank === 0
        ? cw * (0.46 + 0.43 * (1 - Math.sqrt(Math.max(0, 1 - v * v))))
        : Math.max(
            x + 0.08 * (end - x),
            Math.min(end - 0.08 * (end - x), desiredX),
          );
    const analyticBand = band(l, dotX, from, to);
    const dotY =
      node.rank === 0 ? leafY : (analyticBand[0] + analyticBand[1]) / 2;
    const dotBand = band(l, dotX, from, to);
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
      dotHeight: dotBand[1] - dotBand[0],
      path: pathFor(l, x, end, from, to),
    });
    let offset = from;
    for (const child of owned(node)) {
      const next = offset + ((to - from) * weight(child)) / weight(node);
      visit(child, l, offset, next, key, node.rank);
      offset = next;
    }
  };
  const dense = graph.all.length > 1800;
  if (!dense) for (const l of lobes) visit(l.root, l, 0, 1);
  const byNode = new Map(tiles.map((t) => [t.node.id, t]));
  const vertices = (tile: (typeof tiles)[number], rightFirst = false) => {
    const lobe = lobes.find((l) => l.root.id === tile.rootId)!;
    const sides = [tile.x, tile.x + tile.width];
    if (rightFirst) sides.reverse();
    return sides.flatMap((x) => {
      const [top, bottom] = band(lobe, x, tile.from, tile.to);
      // A curved back can remove a nominal corner. Never anchor in that void.
      return bottom < top
        ? []
        : [
            { x, y: top },
            { x, y: bottom },
          ];
    });
  };
  const links = tiles.flatMap((child) =>
    child.node.parents.flatMap((parent) => {
      if (owner.get(child.node.id) === parent.id) return [];
      const target = byNode.get(parent.id);
      if (!target) return [];
      const pairs = vertices(child, true).flatMap((from) =>
        vertices(target).map((to) => ({
          from,
          to,
          distance: Math.abs(to.x - from.x) + Math.abs(to.y - from.y),
        })),
      );
      // Manhattan distance is the actual length of the vertical/horizontal
      // route. Facing edges win ties; parent order cannot force a detour.
      const nearest = pairs.length
        ? pairs.reduce((best, pair) =>
            pair.distance < best.distance - 1e-7 ? pair : best,
          )
        : {
            from: { x: child.dotX, y: child.dotY },
            to: { x: target.dotX, y: target.dotY },
          };
      const { from, to } = nearest;
      return [
        {
          child: child.node.id,
          parent: parent.id,
          from,
          to,
          path: `M${from.x},${from.y} V${to.y} H${to.x}`,
        },
      ];
    }),
  );
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
    outline: dense
      ? []
      : lobes.map((l) => {
          const top = height * l.from,
            bottom = height * l.to;
          const backX = (y: number) =>
            cw *
            0.9 *
            (1 - Math.sqrt(Math.max(0, 1 - ((y / height) * 2 - 1) ** 2)));
          return (
            pathFor(l, fork, l.end, 0, 1).replace(/ Z$/, "") +
            ` L${backX(bottom)},${bottom} A${cw * 0.9},${height / 2} 0 0 1 ${backX(top)},${top} Z`
          );
        }),
    tiles,
    columns,
    edges,
    shares,
    usefulTier: useful,
    links,
    slices,
    dense,
    labelBox,
  };
}

export type HierarchyLayout = ReturnType<typeof hierarchyLayout>;

/** Reserve geometry from captured source groups, never invent goal nodes or
 * semantic parent links. Missing judgments remain empty space in the outline. */
export function previewHierarchyLayout(graph: GoalGraph, groups: string[][], height: number, width: number, shares?: number[]) {
  const root = "layout-only:document";
  const structural = goalGraph([
    { id: root, maker: "layout", label: "", description: "", regions: [], evidence: [] },
    ...groups.map((regions, i) => ({ id: `layout-only:${i}`, maker: "layout", label: "", description: "", regions, evidence: [], parentId: root })),
  ]);
  const reserved = hierarchyLayout(structural, height, width, shares);
  const tiles = reserved.tiles.flatMap(tile => {
    const node = graph.all.find(n => tile.node.id === root ? n.data.level === "document" :
      n.data.level !== "document" && n.data.regions.length === tile.node.data.regions.length && n.data.regions.every((r, i) => r === tile.node.data.regions[i]));
    return node ? [{ ...tile, node, key: `preview/${node.id}`, parentKey: node.parents[0] ? `preview/${node.parents[0].id}` : undefined }] : [];
  });
  return { ...reserved, tiles, links: [] };
}
export function instanceNeighborhood(layout: HierarchyLayout, key?: string) {
  const tile = layout.tiles.find((t) => t.key === key);
  const ancestors = new Set<string>(),
    descendants = new Set<string>();
  const byId = new Map(layout.tiles.map((t) => [t.node.id, t]));
  const walk = (direction: "parents" | "children", output: Set<string>) => {
    const pending = tile ? [tile.node] : [],
      seen = new Set<string>();
    while (pending.length) {
      const current = pending.pop()!;
      if (seen.has(current.id)) continue;
      seen.add(current.id);
      const item = byId.get(current.id);
      if (item) output.add(item.key);
      pending.push(...current[direction]);
    }
  };
  walk("parents", ancestors);
  walk("children", descendants);
  return { tile, ancestors, descendants };
}

export function instanceReelCandidates(
  graph: GoalGraph,
  layout: HierarchyLayout,
  selected: GraphNode | undefined,
  rank: number,
  key?: string,
) {
  // A single brick can have several supplied parents. Never hide those paths
  // merely because packing gave it one geometrical neighbor.
  return reelCandidates(graph, selected, rank);
}
