import type { Hypothesis } from "../core/model";

type Estimate = NonNullable<Hypothesis["preferenceEstimate"]>;
export const estimateNumber = (value: number) =>
  new Intl.NumberFormat(undefined, { maximumSignificantDigits: 4 }).format(
    value,
  );

/** One supplied estimate and interval. It does not imply a measured life history. */
export function PreferenceEstimate({ estimate }: { estimate: Estimate }) {
  const { value, reference, interval } = estimate;
  const values = [
    value,
    ...(reference === undefined ? [] : [reference]),
    ...(interval ? [interval.lower, interval.upper] : []),
  ];
  // Work on normalized coordinates before subtraction, including extreme finite inputs.
  const magnitude = Math.max(1, ...values.map(Math.abs));
  const low = Math.min(...values) / magnitude;
  const high = Math.max(...values) / magnitude;
  const span = high - low || 1;
  const x = (n: number) =>
    high === low ? 151 : 40 + 222 * ((n / magnitude - low) / span);
  const center = high === low ? 151 : x(value);
  const summary = `${estimate.quantity}: ${estimateNumber(value)}. ${
    interval
      ? `${Math.round(interval.level * 100)}% interval ${estimateNumber(interval.lower)} to ${estimateNumber(interval.upper)}. ${interval.method}.`
      : "Uncertainty not supplied."
  }`;
  return (
    <div className="preference-estimate">
      <svg
        className="preference-chart"
        viewBox="0 0 302 108"
        role="img"
        aria-label={summary}
      >
        <title>{summary}</title>
        <path className="preference-axes" d="M24 65 H278" />
        {reference !== undefined && (
          <path
            className="preference-reference"
            d={`M${high === low ? 151 : x(reference)} 28 V80`}
          />
        )}
        {interval && (
          <g className="preference-interval">
            <path
              className="preference-sleeve"
              d={`M${x(interval.lower)} 65 Q${center} 36 ${x(interval.upper)} 65 Q${center} 94 ${x(interval.lower)} 65 Z`}
            />
            <path
              className="preference-line"
              d={`M${x(interval.lower)} 65 H${x(interval.upper)} M${x(interval.lower)} 59 V71 M${x(interval.upper)} 59 V71`}
            />
          </g>
        )}
        <circle className="preference-set-point" cx={center} cy="65" r="4" />
        <text x={center} y="26" textAnchor="middle">
          {estimateNumber(value)}
        </text>
        {interval && (
          <>
            <text x="24" y="101">
              {estimateNumber(interval.lower)}
            </text>
            <text x="278" y="101" textAnchor="end">
              {estimateNumber(interval.upper)}
            </text>
            <text x="151" y="101" textAnchor="middle">
              {Math.round(interval.level * 100)}% interval
            </text>
          </>
        )}
      </svg>
      <p className="preference-readout">
        {estimate.quantity}
        {reference === undefined
          ? ""
          : ` · reference ${estimateNumber(reference)}`}
      </p>
      <p className="source-note">
        {interval?.method ?? "Uncertainty not supplied; no error band is drawn"}
        .
      </p>
      <p className="source-note">{estimate.basis}</p>
    </div>
  );
}
