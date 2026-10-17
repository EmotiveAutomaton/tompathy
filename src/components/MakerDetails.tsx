import { useState } from "react";
import type { Packet } from "../core/model";

export function MakerDetails({ packet, maker }: { packet: Packet; maker?: string }) {
  const [revealed, setRevealed] = useState<string[]>([]);
  if (packet.schemaVersion !== "1.9") return null;
  return <details className="preview-modules"><summary>Makers and source evidence</summary>
    {packet.preview?.github && <p>{packet.preview.github.commits} file commits · {(packet.preview.github.declaredAiCommitShare * 100).toFixed(0)}% contain a recognized tool declaration · GitHub quota remaining: {packet.preview.github.quotaRemaining ?? "unreported"}. This is a declaration share, not a percentage of AI-written text.</p>}
    {packet.makers.filter(m => !maker || m.id === maker).map(m => <article key={m.id}>
      <strong>{m.label} · {m.kind ?? "unknown"}</strong>
      <p>{m.relationship}</p>
      {m.localLabel && <button className="text-button" onClick={() => setRevealed(old => old.includes(m.id) ? old.filter(id => id !== m.id) : [...old, m.id])}>{revealed.includes(m.id) ? `Hide username · ${m.localLabel}` : "Reveal username locally"}</button>}
      {m.evidence?.map((e, i) => <p key={i}><strong>{e.tier}</strong> · {e.source}<br />{e.detail}</p>)}
      {m.bytesChanged !== undefined && <p>{m.bytesChanged.toLocaleString()} changed bytes in witnessed parent pairs.</p>}
      {m.decisions && <p>{Object.entries(m.decisions).map(([name, count]) => `${name}: ${count}`).join(" · ")}. Counts describe source records; intent is unestablished.</p>}
      {m.role && <p>Role hypothesis: {m.role}</p>}
    </article>)}
  </details>;
}
