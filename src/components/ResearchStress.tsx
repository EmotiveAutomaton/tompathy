import type { Packet } from "../core/model";
import { pageStress } from "../core/need-view";

/** A page/window model score, never a measured trajectory of the author. */
export function ResearchStress({ packet, enabled }: { packet: Packet; enabled: boolean }) {
  const readings = pageStress(packet, enabled);
  if (!readings.length) return null;
  return <section aria-label="Research worry reading" data-testid="research-stress">
    {readings.map(r => {
      const start = Math.min(...r.series.map(s => s.from)), end = Math.max(...r.series.map(s => s.to));
      const points = r.series.map(s => `${10 + 280 * ((s.from + s.to) / 2 - start) / Math.max(1, end - start)},${70 - 60 * s.value}`).join(" ");
      return <div key={r.pack}><p>{r.key.corpus === "constructed" ? "Constructed software fixture, not a measured reading." : "Research reader trained on writers' own worry ratings in one UK COVID-era corpus."}{" "}
        Its held-out {r.score.metric} is {r.score.value.toFixed(3)}. This is a reading of these text windows, not a measure of this writer's Stress.
        Worry as Stress is a proposed mapping; the packed full-data head itself was not scored.</p>
        <svg viewBox="0 0 300 80" role="img" aria-label="Predicted worry across text windows, normalized from the answer key's scale">
          <polyline points={points} fill="none" stroke="currentColor" strokeWidth="2" />
          {r.series.map((s, i) => <circle key={i} cx={10 + 280 * ((s.from + s.to) / 2 - start) / Math.max(1, end - start)} cy={70 - 60 * s.value} r="2.5"><title>Text {s.from}–{s.to}: {s.value.toFixed(3)} on the normalized scale</title></circle>)}
        </svg><p>Consecutive sentence windows, 128-token cap, half-window steps. A long single sentence is truncated by the reader.
          Plain-prose scores are retained; they do not establish that someone is worried.
          {r.nothing_here.theme_free_mean_normalized != null && ` On the 40 theme-free controls, mean predicted worry was ${(1 + 8 * r.nothing_here.theme_free_mean_normalized).toFixed(2)} of 9.`}</p></div>;
    })}
  </section>;
}
