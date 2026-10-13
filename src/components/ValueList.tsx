import type { Hypothesis, Packet } from "../core/model";
import { PreferenceChart, PreferenceObservations } from "./PreferenceChart";
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
export function ValueDetails({
  h,
  packet,
}: {
  h: Hypothesis;
  packet: Packet | null;
}) {
  return (
    <>
      <strong className="value-card-title">{h.label}</strong>
      {h.preferenceTrace ? (
        <>
          <div className="value-visual-summary">
            <div className="value-confidence" title={h.support?.meaning}>
              <Wheel value={h.support ? weight(h) : null} large />
              <strong>
                {h.support ? `${Math.round(weight(h) * 100)}%` : "?"}
              </strong>
              <span>confidence</span>
            </div>
            <PreferenceChart trace={h.preferenceTrace} />
          </div>
          <PreferenceObservations trace={h.preferenceTrace} />
        </>
      ) : (
        <>
          <div className="value-detail-heading">
            <Wheel value={h.support ? weight(h) : null} large />
            <span>{supportText(h)}</span>
          </div>
          <p>{h.description}</p>
          {h.evidence.slice(0, 3).map((id) => {
            const e = packet?.evidence.find((e) => e.id === id);
            return (
              e && (
                <div key={id} className="source-note">
                  <strong>
                    {e.source === packet?.artifact.source
                      ? "This page"
                      : "Context"}
                  </strong>
                  <p>{e.excerpt}</p>
                </div>
              )
            );
          })}
        </>
      )}
    </>
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
            content={<ValueDetails h={h} packet={packet} />}
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
