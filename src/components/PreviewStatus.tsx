import type { Hypothesis, Packet } from "../core/model";
import { PREVIEW_NOTICE } from "../core/preview";

export function EvidenceEntries({ packet, kinds }: { packet: Packet; kinds: Hypothesis["kind"][] }) {
  if (packet.provider.mode !== "preview") return null;
  const names = { page: "From the page", person: "From the person", process: "From the process" };
  const entries = [...new Set(packet.hypotheses.filter(h => kinds.includes(h.kind)).flatMap(h => h.entry ? [h.entry] : []))];
  return <small className="preview-entries">{entries.length ? entries.map(e => names[e]).join(" · ") : "No evidence supplied"}</small>;
}

export function EvidenceBadge({ item }: { item: Pick<Hypothesis, "basis" | "evidenceStatus"> }) {
  if (!item.evidenceStatus) return null;
  const labels = { admitted: "tested", "constructed-tested": "lab-tested", unvalidated: "untested" };
  const reasons = { admitted: "Passed the required scientific admission gates.", "constructed-tested": "Lab-tested on templated items for this exact reader; natural-data accuracy is unestablished.", unvalidated: "No applicable validation has passed." };
  return <span className={`evidence-badge evidence-${item.evidenceStatus}`} title={`${item.basis}: ${reasons[item.evidenceStatus]}`}>{labels[item.evidenceStatus]}</span>;
}

export function PreviewBanner({ packet }: { packet: Packet | null }) {
  return packet?.provider.mode === "preview" ? <p className="preview-banner">{packet.provider.previewNotice ?? PREVIEW_NOTICE}</p> : null;
}

export function PreviewModules({ packet, ids, onRegion }: { packet: Packet; ids: string[]; onRegion?: (region: string) => void }) {
  if (!packet.preview) return null;
  const modules = packet.preview.modules.filter(m => ids.includes(m.id));
  return <details className="preview-modules"><summary>Research preview · {modules.filter(m => m.status === "complete").length}/{modules.length} modules ready</summary>
    {modules.map(m => <p key={m.id}><strong>{m.title}: {m.status}</strong>{m.completed != null && <> · {m.completed}/{m.total} {m.unit}</>}{m.elapsedMs != null && <> · {(m.elapsedMs / 1000).toFixed(1)} s</>}<br />{m.detail}</p>)}
    {ids.includes("deviation") && packet.preview.statistics && <p>Content-word surprisal: mean {packet.preview.statistics.mean.toFixed(2)} nats; median {packet.preview.statistics.median.toFixed(2)}; interquartile range {packet.preview.statistics.iqr.toFixed(2)}. Names and numbers held apart: {packet.preview.statistics.heldOut}. <span title={packet.preview.statistics.heldOutExamples.join(", ")}>Statistics cover the text processed so far; partial rankings can change.</span></p>}
    {ids.includes("deviation") && packet.preview.readers.map(r => <p key={r.id} title={`Revision ${r.revision}; SHA-256 ${r.sha256}`}>{r.id}<br />{r.backend}</p>)}
    {ids.includes("agreement") && packet.preview.agreement && <>
      <p>With more context, these readers' top-departure overlap {packet.preview.agreement.full.overlap > packet.preview.agreement.short.overlap ? "increases" : packet.preview.agreement.full.overlap < packet.preview.agreement.short.overlap ? "decreases" : "stays unchanged"}: {(packet.preview.agreement.short.overlap * 100).toFixed(1)}% → {(packet.preview.agreement.full.overlap * 100).toFixed(1)}%.</p>
      <p>Rank correlation: {packet.preview.agreement.short.spearman?.toFixed(3) ?? "undefined (constant scores)"} → {packet.preview.agreement.full.spearman?.toFixed(3) ?? "undefined (constant scores)"}. {packet.preview.agreement.method}</p>
      {["Both readers", "Qwen only", "Smol only"].map((label, index) => {
        const regions = packet.preview!.agreement!.regions.filter(r => index === 0 ? r.readers.length === 2 : r.readers.length === 1 && r.readers[0] === index - 1);
        return <details className="preview-region-group" key={label}><summary>{label} · {regions.length} passages</summary>
          <div className="preview-region-list">{regions.map(r => {
            const source = packet.artifact.regions.find(p => p.id === r.region)?.anchor.exact ?? r.region;
            const excerpt = source.length > 100 ? source.slice(0, 100) + "…" : source;
            return onRegion ? <button type="button" className="text-button" key={r.region} onClick={() => onRegion(r.region)}>{excerpt}</button> : <p key={r.region}>{excerpt}</p>;
          })}</div>
        </details>;
      })}
    </>}
    {packet.preview.cachedAt && <p>Cached real run: {packet.preview.cachedAt}</p>}
    {ids.includes("payoff") && packet.preview.payoff && <>
      {packet.preview.payoff.sentencesScored != null && <p>Payoff coverage: {packet.preview.payoff.sentencesScored} of {packet.preview.payoff.totalSentences} sentences have comparable scores. Partial rankings can change.</p>}
      <p>Pays off: places this page's own earlier text made easy. Re-reads the past: passages after which the earlier text makes more sense to the reader model. Proxies for what the author set up; not measured enjoyment.</p>
      <p>Novel-span top-item retention: layer 1 {(packet.preview.payoff.layer1NovelRetention * 100).toFixed(0)}%; layer 2 {packet.preview.payoff.layer2NovelRetention == null ? "unavailable" : `${(packet.preview.payoff.layer2NovelRetention * 100).toFixed(0)}%`}. The requested check is at least 50%. {packet.preview.payoff.layer2Status}.</p>
      {packet.preview.payoff.easyWithoutContext && <p>Low context-free surprisal (below 2 nats/token): possible memorization or predictable wording. This heuristic is not proof of memorization or source attribution.</p>}
    </>}
  </details>;
}
