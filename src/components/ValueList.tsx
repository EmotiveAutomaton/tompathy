import type { Hypothesis, Packet } from "../core/model";
import { HoverCard } from "./HoverCard";
import { supportText, weight } from "./GoalCloud";
export function Wheel({
  value,
  large = false,
}: {
  value: number | null;
  large?: boolean;
}) {
  const angle = (value ?? 0) * Math.PI * 2,
    x = 18 + 14 * Math.sin(angle),
    y = 18 - 14 * Math.cos(angle);
  return (
    <svg
      className={`support-wheel ${large ? "large" : ""}`}
      viewBox="0 0 36 36"
      aria-hidden="true"
    >
      <circle cx="18" cy="18" r="15.5" className="wheel-outline" />
      <circle cx="18" cy="18" r="14" className="wheel-track" />
      {value !== null &&
        (value >= 0.999 ? (
          <circle cx="18" cy="18" r="14" className="wheel-fill" />
        ) : (
          <path
            d={`M18,18 L18,4 A14,14 0 ${value > 0.5 ? 1 : 0},1 ${x},${y} Z`}
            className="wheel-fill"
          />
        ))}
      {value === null && (
        <text x="18" y="23" textAnchor="middle">
          ?
        </text>
      )}
    </svg>
  );
}
export function ValueList({
  values,
  packet,
  inspect,
}: {
  values: Hypothesis[];
  packet: Packet | null;
  inspect: (h: Hypothesis) => void;
}) {
  return (
    <div className="core-values" data-testid="values">
      {[...values]
        .sort(
          (a, b) => (b.support ? weight(b) : -1) - (a.support ? weight(a) : -1),
        )
        .slice(0, 9)
        .map((h) => (
          <HoverCard
            key={h.id}
            className="value-hover"
            content={
              <>
                <div className="value-detail-heading">
                  <Wheel value={h.support ? weight(h) : null} large />
                  <div>
                    <strong>{h.label}</strong>
                    <p>{supportText(h)}</p>
                  </div>
                </div>
                <p className="value-summary">{h.description}</p>
                <p className="muted support-summary">
                  {h.support?.meaning ??
                    "No reliability estimate was supplied."}
                </p>
                <h3>Where this comes from</h3>
                {h.evidence.length ? (
                  h.evidence.slice(0, 3).map((id) => {
                    const e = packet?.evidence.find((e) => e.id === id);
                    return (
                      e && (
                        <div key={id} className="source-note">
                          <strong>
                            {e.source === packet?.artifact.source
                              ? "This page"
                              : packet?.scope.kind === "context"
                                ? "Context"
                                : "External source"}
                          </strong>
                          <p className="source-excerpt">{e.excerpt}</p>
                        </div>
                      )
                    );
                  })
                ) : (
                  <p>No evidence supplied.</p>
                )}
                {h.decisionNodes?.slice(0, 1).map((id) => {
                  const n = packet?.goalHierarchy?.nodes.find(
                    (n) => n.id === id,
                  );
                  return (
                    n && (
                      <div key={id} className="source-note">
                        <strong>Specific decision · {n.label}</strong>
                      </div>
                    )
                  );
                })}
                <p className="muted">
                  Sources support an interpretation; they are not additive
                  slices of confidence. Select the row to inspect the full
                  account.
                </p>
              </>
            }
          >
            <button className="core-value-row" onClick={() => inspect(h)}>
              <Wheel value={h.support ? weight(h) : null} />
              <span>{h.label}</span>
            </button>
          </HoverCard>
        ))}
      {!values.length && (
        <span className="quiet-empty">No values supplied</span>
      )}
    </div>
  );
}
