import type { Packet } from "../core/model";

export function PopulationValues({
  packet,
  maker,
}: {
  packet: Packet;
  maker?: string;
}) {
  const population = packet.population!;
  const items = population.items.filter((i) =>
    packet.hypotheses
      .find((h) => h.id === i.hypothesis)
      ?.makers.includes(maker ?? ""),
  );
  return (
    <section className="population-values" aria-label="Population comparison">
      {items.length ? (
        <details>
          <summary>About this population</summary>
          <p>{population.description}</p>
        </details>
      ) : (
        <p>{population.description}</p>
      )}
      <p className="muted">
        {population.makersPooled} makers pooled · {population.populationId}
      </p>
      {items.map((item) => {
        const h = packet.hypotheses.find((h) => h.id === item.hypothesis)!;
        const maxX = Math.max(1, ...item.curve.map((p) => p.records));
        const maxY = Math.max(0.001, ...item.curve.map((p) => p.intervalWidth));
        return (
          <article key={h.id}>
            <strong>{h.label}</strong>
            {item.quantiles && <figure><svg viewBox="0 0 300 55" role="img" aria-label="Twenty supplied population quantiles">
              {item.quantiles.map((q, i) => <circle key={i} cx={15 + 270 * (q - item.populationSupport.scale[0]) / (item.populationSupport.scale[1] - item.populationSupport.scale[0])} cy={10 + (i % 4) * 11} r="3" fill="currentColor"><title>{q.toPrecision(4)}</title></circle>)}
            </svg><figcaption>20 supplied population quantiles; no personal evidence is added.</figcaption></figure>}
            <dl>
              <dt>Population support</dt>
              <dd>{item.populationSupport.value.toFixed(3)}</dd>
              <dt>Creator support</dt>
              <dd>{h.support?.value.toFixed(3) ?? "Unknown"}</dd>
              <dt>Creator records</dt>
              <dd>{item.makerRecords}</dd>
              <dt>Personal evidence share</dt>
              <dd>{Math.round(item.shrinkage * 100)}%</dd>
            </dl>
            <p className="muted">
              {item.populationSupport.meaning}{" "}
              {item.makerRecords === 0
                ? "Prior only: no personal records."
                : "The remaining weight comes from the population prior."}
            </p>
            {item.curve.length === 1 && (
              <figure>
                <svg
                  viewBox="0 0 300 60"
                  role="img"
                  aria-label="Supplied prior uncertainty width"
                >
                  <path
                    d="M30 10V40M270 10V40M30 25H270"
                    fill="none"
                    stroke="currentColor"
                    opacity=".6"
                  />
                  <circle cx="150" cy="25" r="4" fill="currentColor" />
                  <text x="150" y="58" textAnchor="middle" fontSize="11">
                    0 personal records
                  </text>
                </svg>
                <figcaption>
                  Supplied prior interval width:{" "}
                  {item.curve[0].intervalWidth.toPrecision(3)}. No personal
                  narrowing is measured.
                </figcaption>
              </figure>
            )}
            {item.curve.length > 1 && (
              <figure>
                <svg
                  viewBox="0 0 300 100"
                  role="img"
                  aria-label="Supplied uncertainty width by number of records"
                >
                  <path
                    d="M25 5V80H295"
                    fill="none"
                    stroke="currentColor"
                    opacity=".3"
                  />
                  <polyline
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    points={item.curve
                      .map(
                        (p) =>
                          `${25 + (265 * p.records) / maxX},${80 - (70 * p.intervalWidth) / maxY}`,
                      )
                      .join(" ")}
                  />
                  <text x="25" y="98" fontSize="10">
                    0 records
                  </text>
                  <text x="295" y="98" textAnchor="end" fontSize="10">
                    {maxX} records
                  </text>
                </svg>
                <figcaption>
                  Supplied interval width as records accumulate;{" "}
                  {item.populationSupport.semantics} support.
                </figcaption>
              </figure>
            )}
          </article>
        );
      })}
      {!items.length && (
        <p>No population comparison supplied for this creator.</p>
      )}
    </section>
  );
}
