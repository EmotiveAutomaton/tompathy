import { stratify } from "d3-hierarchy";
import type { Packet } from "./model";
export type GoalNode = NonNullable<Packet["goalHierarchy"]>["nodes"][number];
export function goalTree(nodes: GoalNode[]) {
  return nodes.length
    ? stratify<GoalNode>()
        .id((n) => n.id)
        .parentId((n) => n.parentId)(nodes)
    : null;
}
export function goalAt(nodes: GoalNode[], region: string, offset: number) {
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const depth = (node: GoalNode) => {
    let result = 0,
      parent = node.parentId;
    while (parent && result < 64) {
      result++;
      parent = byId.get(parent)?.parentId;
    }
    return result;
  };
  return nodes
    .filter(
      (n) =>
        n.regions.includes(region) &&
        (!n.span ||
          (n.span.region === region &&
            n.span.start <= offset &&
            n.span.end > offset)),
    )
    .sort(
      (a, b) => Number(!!b.span) - Number(!!a.span) || depth(b) - depth(a),
    )[0];
}
