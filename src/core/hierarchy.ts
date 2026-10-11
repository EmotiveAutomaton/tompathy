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
  return (
    nodes.find(
      (n) =>
        n.span?.region === region &&
        n.span.start <= offset &&
        n.span.end > offset,
    ) ??
    nodes.find((n) => n.level === "paragraph" && n.regions.includes(region)) ??
    nodes.find((n) => n.regions.includes(region))
  );
}
