import { useState } from "react";
import type { Packet } from "../core/model";

export function AttentionTimeline({ packet, onRegion }: { packet: Packet; onRegion: (region: string) => void }) {
  const [limit, setLimit] = useState(30);
  if (!packet.attentionTimeline?.length) return null;
  const coverage = packet.preview?.timelineCoverage;
  return <details className="attention-timeline preview-modules">
    <summary>Edit timeline · {packet.attentionTimeline.length} locations</summary>
    <p>Weak evidence of attention · untested. Changes are located in today’s text; revision gaps are not writing pauses or an editor’s plan.</p>
    {coverage && coverage.total > coverage.emitted && <p>{coverage.emitted} of {coverage.total} locations retained within the reading’s size limit.</p>}
    <ol>{packet.attentionTimeline.slice(0, limit).map((item, index) => <li key={`${item.step}:${index}`}>
      <time dateTime={item.t}>{new Date(item.t).toLocaleString()}</time>{" · "}
      {item.located ? <button className="text-button" onClick={() => onRegion(item.region!)}>{packet.goalHierarchy?.nodes.find(n => n.id === item.node)?.label ?? `Passage ${packet.artifact.regions.findIndex(r => r.id === item.region) + 1}`}</button> : <span>Not located in surviving text</span>}
    </li>)}</ol>
    {limit < packet.attentionTimeline.length && <button onClick={() => setLimit(n => n + 30)}>More changes</button>}
  </details>;
}
