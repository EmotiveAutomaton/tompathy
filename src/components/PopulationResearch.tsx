import aggregate from "../core/phase0-aggregate.json";
import type { Packet } from "../core/model";

export function PopulationResearch({ findings }: { findings?: Packet["globalFindings"] }) {
  if (findings?.length) return <section className="population-values" aria-label="Public population research">
    {findings.map(f => <article key={f.source}><p><strong>{f.source}</strong> · {f.evidenceStatus === "descriptive" ? "descriptive" : "in constructed worlds"}</p><p>{f.claim}</p>{f.number != null && <p>{f.number.toFixed(4)} {f.unit}{f.interval && <> · interval {f.interval.map(n => n.toFixed(4)).join(" to ")}</>}</p>}<a href={f.link} target="_blank" rel="noreferrer">Source and limits</a></article>)}
    <p>Constructed-world intervals describe nominated settings and are not selection-adjusted confirmation intervals. These results do not admit personal taste or habit estimates.</p>
  </section>;
  const rows = [
    ["Against population frequencies", aggregate.overall.gain_over_population],
    ["Against each writer's past frequencies", aggregate.overall.gain_over_personal],
  ] as const;
  return <section className="population-values" aria-label="Public population research">
    <p>A model that starts from everyone and adjusts a little for each writer, given the context, forecast these writers better than their own past choices alone did.</p>
    <p>{aggregate.overall.writers} writers · {aggregate.overall.decisions.toLocaleString()} decisions. Historical, previously exposed data; descriptive results, without engine admission.</p>
    <dl>{rows.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value.mean.toFixed(3)} half-Brier improvement · crossed writer-and-prompt interval {value.crossed_interval.map(x => x.toFixed(5)).join(" to ")}</dd></div>)}</dl>
    <p>Against personal frequencies: {aggregate.noHistory.gain_over_personal.mean.toFixed(3)} with no prior records; {aggregate.atLeast300.gain_over_personal.mean.toFixed(3)} with at least 300 records ({aggregate.atLeast300.writers} writers). The latter interval, {aggregate.atLeast300.gain_over_personal.crossed_interval.map(x => x.toFixed(3)).join(" to ")}, includes zero.</p>
    <p>Different writers fill different history bins. These are not individual learning curves. Context features and shrunken writer offsets are bundled in this comparison.</p>
    <details><summary>Source and limits</summary><p>{aggregate.source}</p><p className="source-pin">SHA-256 {aggregate.sourceSha256}</p>{aggregate.limits.map(line => <p key={line}>{line}</p>)}</details>
    <a href="https://www.harvardmagazine.com/2010/03/pleasure-by-proxy" target="_blank" rel="noreferrer" title="Literature finding: In other studies, people predicted how much they'd enjoy something better from another person's report than from a description of the thing.">Literature finding · Gilbert et al. (2009)</a>
  </section>;
}
