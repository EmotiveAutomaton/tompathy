import type { ContextItem, Hypothesis, Packet } from "./model";
import { goalGraph, type GoalNode } from "./hierarchy";
import { readerNames } from "./bottom-box";

export const needs = (["N1", "N2", "N3", "N4", "N5", "N6"] as const).map(id => ({ id, label: readerNames[id] }));
export type NeedId = typeof needs[number]["id"];
export const bodyChannels = [
  { id: "heat", label: "Heat" }, { id: "food", label: "Food" }, { id: "sleep", label: "Sleep" },
] as const;
export const needDetails = [...needs, ...bodyChannels, { id: "S1", label: "Stress" }] as const;
export type NeedDetailId = typeof needDetails[number]["id"];
export type NeedSource = { id: string; label: string; type: "fluency" | "channel" | "action";
  confidence: number | null; regions: string[]; nodes: string[]; hypothesis?: Hypothesis;
  date?: string; current?: boolean; needs: { id: NeedId; direction: -1 | 1; illustration: boolean }[] };

/** Only actual packet spans are joined. This is not a label-to-need inference. */
export function pageNeedSources(packet: Packet): NeedSource[] {
  return (packet.bottom_box?.on_page ?? []).filter(r => r.id !== null && /^C[1-9]$/.test(r.id)).map(r => {
    const links = new Map<string, NeedSource["needs"][number]>();
    for (const event of r.events) {
      const stake = event.stake;
      if (!stake || stake.direction === "either" || stake.need === "N5") continue;
      const direction = ["up", "restored"].includes(stake.direction) ? 1 : -1;
      links.set(`${stake.need}:${direction}`, { id: stake.need, direction, illustration: false });
    }
    return { id: `page:${r.pack}:${r.id}`, label: readerNames[r.id!] ?? r.id!, type: "channel",
      confidence: r.events.length ? r.events.reduce((s, e) => s + e.confidence, 0) / r.events.length : null,
      regions: packet.artifact.regions.filter(region => r.events.some(e =>
        e.span[0] < region.anchor.start + region.anchor.exact.length && region.anchor.start < e.span[1])).map(r => r.id),
      nodes: [], needs: [...links.values()] };
  });
}

export function pageNeedActivity(packet: Packet) {
  return Object.fromEntries(needs.map(n => [n.id, (packet.bottom_box?.on_page ?? [])
    .filter(r => r.id === n.id && n.id !== "N5")
    .flatMap(r => r.events.map(e => ({ span: e.span, tag: e.label, pack: r.pack })))])) as
    Record<NeedId, { span: [number, number]; tag: string; pack: string }[]>;
}

export function pageStress(packet: Packet, research = false) {
  return research ? (packet.bottom_box?.on_page ?? []).filter(r => r.id === "S1" && r.series.length) : [];
}
const support = (h?: Hypothesis) => !h?.support ? null : Math.max(0, Math.min(1,
  (h.support.value - h.support.scale[0]) / (h.support.scale[1] - h.support.scale[0])));
// Explicit interface illustration, restricted to the constructed example provider.
// This table is not an emotion-to-need inference rule for real documents.
const illustrationNeeds: Record<string, NeedId> = {
  curiosity: "N1", seeking: "N1", adaptability: "N2", stability: "N2", stewardship: "N2",
  belonging: "N3", fairness: "N3", play: "N3", restraint: "N4", care: "N5", accessibility: "N6",
};
const illustrationFluencies: Record<string, NeedId[]> = {
  "Make room for discovery": ["N1"], "Keep learning from play": ["N1", "N3"],
  "Keep play accessible": ["N3", "N6"], "Complete automated assembly": ["N2"],
};
export function workNeedSources(packet: Packet, nodes: GoalNode[], values: Hypothesis[], research = false): NeedSource[] {
  const illustration = packet.provider.id === "tompathy-example" && packet.origin === "synthetic example";
  const roots = goalGraph(nodes).roots.map(n => n.data);
  const entries: NeedSource[] = roots.map(node => ({ id: node.id, label: node.label, type: "fluency",
    confidence: support(packet.hypotheses.find(h => h.id === node.id)), regions: node.regions,
    nodes: [node.id], hypothesis: packet.hypotheses.find(h => h.id === node.id), needs: [] }));
  for (const h of values.filter(v => v.valueCategory === "drive")) entries.push({ id: h.id,
    label: h.label === "Belonging" ? "PANIC/GRIEF" : h.label, type: "channel", confidence: support(h),
    regions: h.regions, nodes: h.decisionNodes ?? [], hypothesis: h, needs: [] });
  if (illustration) for (const source of entries) {
    const related = values.filter(h => h.id === source.id || h.decisionNodes?.includes(source.id)
      || h.regions.some(r => source.regions.includes(r)));
    const ids = new Set([...(illustrationFluencies[source.label] ?? []), ...related.flatMap(h => {
      const key = Object.keys(illustrationNeeds).find(k => h.id.toLowerCase().includes(k) || h.label.toLowerCase() === k);
      return key ? [illustrationNeeds[key]] : [];
    })]);
    source.needs = [...ids].map(id => ({ id, direction: 1, illustration: true }));
  }
  if (illustration) for (const source of entries.filter(s => s.type === "channel")) {
    const related = entries.filter(s => s.type === "fluency" && s.needs.some(n => source.needs.some(t => t.id === n.id)));
    source.nodes = [...new Set([...source.nodes, ...related.flatMap(s => s.nodes)])];
    source.regions = [...new Set([...source.regions, ...related.flatMap(s => s.regions)])];
  }
  return research ? [...entries, ...pageNeedSources(packet)] : entries;
}

export function authorNeedSources(packet: Packet, context: ContextItem[], work: NeedSource[]): NeedSource[] {
  const authors = new Set([...(packet.artifact.authors ?? []).map(a => a.label.toLowerCase()),
    ...packet.makers.filter(m => m.identity !== "unknown").map(m => m.label.toLowerCase())]);
  const current: NeedSource = { id: `artifact:${packet.artifact.id}`, label: packet.artifact.title || "Current artifact",
    type: "action", confidence: null, regions: packet.artifact.regions.map(r => r.id), nodes: work.flatMap(s => s.nodes),
    current: true, needs: [] };
  const rows: NeedSource[] = [];
  // Only supplied, attributed, dated action observations; paragraphs are not life events.
  for (const item of context.filter(c => c.selected && c.provenance && authors.has(c.provenance.author.toLowerCase()))) {
    for (const [i, fact] of (item.facts ?? []).entries()) {
      if (!fact.date || !["event", "publication"].includes(fact.dateKind)) continue;
      if (fact.source === packet.artifact.source && fact.dateKind === "publication") { current.date = fact.date; continue; }
      rows.push({ id: `${item.id}:${i}`, label: fact.label, type: "action", confidence: null,
        date: fact.date, regions: [], nodes: [], needs: [] });
    }
  }
  const illustration = packet.provider.id === "tompathy-example" && packet.origin === "synthetic example";
  if (illustration) current.needs = [...new Set(work.flatMap(s => s.needs.map(n => n.id)))].map(id => ({ id, direction: 1, illustration: true }));
  if (current.date) return [...rows, current].sort((a, b) => a.date!.localeCompare(b.date!));
  // Without the artifact's date, do not manufacture a before/after chronology.
  return [current, ...rows.sort((a, b) => a.date!.localeCompare(b.date!))];
}
