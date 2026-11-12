import { goalGraph, type GoalNode } from "./hierarchy";
import type { Hypothesis, Packet } from "./model";

type Cell = { id: string; label: string; shortLabel: string; value?: Hypothesis; node?: GoalNode; confidence?: Hypothesis };
type Edge = { from: string; to: string; weight?: number; illustrative?: boolean };
export type ValueTable = { rows: Cell[][]; edges: Edge[] };
// Excerpts, not new model interpretations. The complete label stays inspectable.
const short = (s: string) => s.split(/\s+/).length > 4 ? s.split(/\s+/).slice(0, 4).join(" ") + "…" : s;
export function valueTable(packet: Packet, nodes: GoalNode[], values: Hypothesis[]): ValueTable {
  const graph = goalGraph(nodes), edges: Edge[] = [];
  const levels = new Map<number, Cell[]>();
  const put = (rank: number, cell: Cell) => levels.set(rank, [...(levels.get(rank) ?? []), cell]);
  for (const node of graph.all) {
    put(node.rank, { id: `goal:${node.id}`, node: node.data, label: node.data.label, shortLabel: short(node.data.label), confidence: packet.hypotheses.find(h => h.id === node.id) });
    for (const parent of node.parents) edges.push({ from: `goal:${node.id}`, to: `goal:${parent.id}` });
  }
  const illustration = packet.provider.id === "tompathy-example" && packet.origin === "synthetic example";
  for (const value of values) {
    put(graph.depth + (value.valueCategory === "drive" ? 2 : 1), { id: `value:${value.id}`, value, label: value.label, shortLabel: short(value.label) });
    const targets = new Map<string, number | undefined>();
    for (const id of value.decisionNodes ?? []) if (graph.byId.has(id)) targets.set(id, undefined);
    const tip = packet.valueView?.tips.find(t => t.hypothesis === value.id && t.status === "drawn");
    for (const feed of packet.valueView?.feeds ?? []) {
      if (feed.tip !== tip?.id) continue;
      const row = packet.valueView!.rows.find(r => r.id === feed.row);
      const matching = graph.all.filter(n => row?.region && n.data.regions.includes(row.region) && n.data.evidence.some(e => row.evidence.includes(e)));
      const nearest = matching.sort((a, b) => a.rank - b.rank)[0];
      if (nearest) targets.set(nearest.id, Math.max(targets.get(nearest.id) ?? 0, feed.weight));
    }
    if (illustration && value.valueCategory !== "drive" && !targets.size) {
      for (const root of graph.roots.filter(n => value.regions.some(r => n.data.regions.includes(r)))) targets.set(root.id, undefined);
    }
    for (const [id, weight] of targets) edges.push({ from: `goal:${id}`, to: `value:${value.id}`, weight, illustrative: illustration });
  }
  if (illustration) {
    const constructed = values.filter(v => v.valueCategory !== "drive");
    for (const [i, drive] of values.filter(v => v.valueCategory === "drive").entries()) {
      if (constructed.length) edges.push({ from: `value:${constructed[i % constructed.length].id}`, to: `value:${drive.id}`, weight: [.25, .6, .9][i % 3], illustrative: true });
    }
  }
  return { rows: [...levels].sort(([a], [b]) => b - a).map(([, cells]) => cells), edges };
}
export function connectedValues(table: ValueTable, id?: string) {
  const selected = new Set<string>();
  if (!id) return selected;
  for (const direction of ["up", "down"]) {
    const adjacent = new Map<string, string[]>();
    for (const edge of table.edges) {
      const from = direction === "up" ? edge.from : edge.to, to = direction === "up" ? edge.to : edge.from;
      const list = adjacent.get(from) ?? []; list.push(to); adjacent.set(from, list);
    }
    const pending = [id], visited = new Set<string>();
    while (pending.length) {
      const current = pending.pop()!;
      if (visited.has(current)) continue;
      visited.add(current); selected.add(current);
      pending.push(...adjacent.get(current) ?? []);
    }
  }
  return selected;
}
