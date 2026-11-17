import type { Packet } from "../core/model";
import { readerNames } from "../core/bottom-box";

export function passageAt(packet: Packet, span: [number, number]) {
  return packet.artifact.regions.flatMap(region => {
    const start = region.anchor.start, text = region.anchor.exact;
    const a = Math.max(start, span[0]), b = Math.min(start + text.length, span[1]);
    return a < b ? [text.slice(a - start, b - start)] : [];
  }).join(" … ");
}

/** Inspection only. Unassigned labels never acquire a need or a level. */
export function ResearchReadings({ packet, enabled, need }: { packet: Packet; enabled: boolean; need?: string }) {
  if (!enabled) return null;
  const readings = (packet.bottom_box?.on_page ?? []).filter(r => r.status === "research" && r.id !== "N5" && r.events.length && (!need || r.id === need || r.events.some(e => e.stake?.need === need)));
  if (!readings.length) return null;
  return <details data-testid="research-readings"><summary>Research passage readings</summary>
    <p>Proposed readings of these sentences. They do not establish this writer’s needs, preferences or endorsement.</p>
    {readings.map(r => <details key={`${r.pack}:${r.id ?? "unassigned"}`}><summary>{r.id ? readerNames[r.id] : "Unassigned labels"} · {r.events.length} events</summary>
      <p>{r.key.corpus}. {r.score.metric}: {r.score.value.toFixed(3)}.</p>
      {r.events.filter(e => !need || r.id === need || e.stake?.need === need).map((e, i) => <div key={i}>
        <blockquote>{passageAt(packet, e.span) || `No matching passage for span ${e.span.join("–")}.`}</blockquote>
        <p>{e.label} · score {e.confidence.toFixed(3)}{r.id === null ? " · no assigned need or channel" : ""}
          {e.stake && e.stake.need !== "N5" && ` · ${readerNames[e.stake.need]}, ${e.stake.direction}, ${e.stake.by}, ${e.stake.when}`}
          {e.channel_by_table && ` · ${e.channel_by_table.version}: ${readerNames[e.channel_by_table.channel]}${e.channel_by_table.channel !== r.id ? " (disagrees with the label reader)" : ""}`}</p>
      </div>)}
    </details>)}
  </details>;
}
