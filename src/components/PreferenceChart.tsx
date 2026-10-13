import { useId } from "react";
import type { Hypothesis } from "../core/model";
type Trace = NonNullable<Hypothesis["preferenceTrace"]>;
const x = (n: number) => 24 + n * 256;
const y = (n: number) => 133 - n * 106;
// Cubic interpolation keeps the tube continuous through each supplied sample.
function curve(points: [number, number][]) {
  return points.slice(1).reduce(
    (path, p, i) => {
      const a = points[i],
        before = points[Math.max(0, i - 1)],
        after = points[Math.min(points.length - 1, i + 2)];
      return `${path} C${a[0] + (p[0] - before[0]) / 6},${a[1] + (p[1] - before[1]) / 6} ${p[0] - (after[0] - a[0]) / 6},${p[1] - (after[1] - a[1]) / 6} ${p[0]},${p[1]}`;
    },
    `M${points[0].join(",")}`,
  );
}
export function PreferenceChart({ trace }: { trace: Trace }) {
  const id = useId().replace(/:/g, ""),
    marker = `${id}-arrow`,
    fill = `${id}-tube`;
  const line = curve(trace.points.map((p) => [x(p.x), y(p.y)]));
  const upper = curve(
    trace.points.map((p) => [x(p.x), y(Math.min(1, p.y + p.uncertainty))]),
  );
  const lower = curve(
    [...trace.points]
      .reverse()
      .map((p) => [x(p.x), y(Math.max(0, p.y - p.uncertainty))]),
  );
  return (
    <svg
      className="preference-chart"
      viewBox="0 0 302 158"
      role="img"
      aria-label={`${trace.domain}: possible preferred trajectory from ${trace.start} to ${trace.end}, with an uncertainty band and ${trace.observations.length} observations`}
    >
      <defs>
        <marker
          id={marker}
          viewBox="0 0 8 8"
          refX="6.5"
          refY="4"
          markerWidth="5"
          markerHeight="5"
          orient="auto-start-reverse"
        >
          <path
            d="M1 1 L7 4 L1 7"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.2"
          />
        </marker>
        <linearGradient id={fill} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="currentColor" stopOpacity=".3" />
          <stop offset=".5" stopColor="currentColor" stopOpacity=".05" />
          <stop offset="1" stopColor="currentColor" stopOpacity=".3" />
        </linearGradient>
        <clipPath id={`${id}-band`}>
          <path d={`${upper} ${lower.replace(/^M/, "L")} Z`} />
        </clipPath>
      </defs>
      <path className="preference-axes" d="M20 18 V136 H286" />
      <text x="24" y="12">
        {trace.domain}
      </text>
      <path
        className="preference-band"
        d={`${upper} ${lower.replace(/^M/, "L")} Z`}
        fill={`url(#${fill})`}
      />
      <path d={line} className="preference-line" />
      <g clipPath={`url(#${id}-band)`}>
        {trace.observations.map((o, i) => (
          <g key={i} className="preference-vector">
            <path
              d={`M${x(o.from[0])},${y(o.from[1])} L${x(o.to[0])},${y(o.to[1])}`}
              strokeWidth={1 + o.cost * 1.6}
              markerEnd={`url(#${marker})`}
            />
            <circle cx={x(o.from[0])} cy={y(o.from[1])} r="3" />
            <text x={x(o.from[0]) - 9} y={y(o.from[1]) - 6}>
              {i + 1}
            </text>
          </g>
        ))}
      </g>
      <text x="24" y="152">
        {trace.start}
      </text>
      <text x="280" y="152" textAnchor="end">
        {trace.end} →
      </text>
    </svg>
  );
}
export function PreferenceObservations({ trace }: { trace: Trace }) {
  return (
    <ol className="preference-observations">
      {trace.observations.map((o, i) => {
        const dx = (o.to[0] - o.from[0]) * 256,
          dy = (o.to[1] - o.from[1]) * 106;
        const length = Math.hypot(dx, dy),
          scale = 24 / Math.max(60, length);
        const endX = 7 + dx * scale,
          endY = 21 - dy * scale;
        const angle = Math.atan2(-dy, dx),
          arm = 4;
        return (
          <li key={i}>
            <svg viewBox="0 0 42 44" aria-hidden="true">
              <text x="1" y="10">
                {i + 1}
              </text>
              <path
                d={`M7 21 L${endX} ${endY} M${endX - arm * Math.cos(angle - 0.6)} ${endY - arm * Math.sin(angle - 0.6)} L${endX} ${endY} L${endX - arm * Math.cos(angle + 0.6)} ${endY - arm * Math.sin(angle + 0.6)}`}
                strokeWidth={1 + o.cost * 1.6}
              />
            </svg>
            <div>
              <strong>
                {o.date} · {o.horizon}
              </strong>
              <p>{o.explanation}</p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
