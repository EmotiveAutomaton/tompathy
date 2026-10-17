import type { Hypothesis, Packet } from "../core/model";
import { EvidenceBadge } from "./PreviewStatus";

export function RecordedProcess({
  packet,
  maker,
  inspect,
}: {
  packet: Packet;
  maker?: string;
  inspect: (h: Hypothesis) => void;
}) {
  const events = packet.process.nodes
    .map((id) => packet.hypotheses.find((h) => h.id === id))
    .filter((h): h is Hypothesis => !!h && (!maker || h.makers.includes(maker)));
  return (
    <div className="recorded-process" aria-label="Recorded production history">
      <p className="muted">
        {packet.provider.mode === "preview" ? "Surface descriptions and observed history. These do not establish a maker's motives." : "Recorded history. The purpose of each change remains unestablished."}
      </p>
      <ol>
        {events.map((h) => (
          <li key={h.id}>
            <button onClick={() => inspect(h)}>
              <strong>{h.label}</strong>
              <EvidenceBadge item={h} />
              <span>{h.description}</span>
            </button>
          </li>
        ))}
      </ol>
    </div>
  );
}
