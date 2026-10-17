import { useId, useState } from "react";
import type { Hypothesis } from "../core/model";
type Trace = NonNullable<Hypothesis["preferenceTrace"]>;
const x = (n: number) => 24 + n * 256;
const y = (n: number) => 133 - n * 106;
// Shared easing stays between adjacent samples: steep changes cannot overshoot
// the supplied bounds or make the uncertainty envelope cross its center line.
function curve(points: [number, number][]) {
  return points.slice(1).reduce(
    (path, p, i) => {
      const a = points[i],
        delta = (p[0] - a[0]) / 3;
      return `${path} C${a[0] + delta},${a[1]} ${p[0] - delta},${p[1]} ${p[0]},${p[1]}`;
    },
    `M${points[0].join(",")}`,
  );
}
export function PreferenceChart({ trace }: { trace: Trace }) {
  const [inspected, setInspected] = useState<number | null>(null);
  const index = Math.min(
    trace.points.length - 1,
    inspected ?? trace.points.length - 1,
  );
  const point = trace.points[index];
  const low = Math.max(0, point.y - point.uncertainty),
    high = Math.min(1, point.y + point.uncertainty);
  const readout = `Point ${index + 1} of ${trace.points.length}: preferred state ${point.y.toFixed(2)}, supplied range ${low.toFixed(2)}–${high.toFixed(2)} on a normalized 0–1 scale`;
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
    <div className="preference-trajectory">
      <svg
        className="preference-chart"
        viewBox="0 0 302 158"
        role="img"
        aria-label={`${trace.domain}: possible preferred trajectory from ${trace.start} to ${trace.end}, with an uncertainty band and ${trace.observations.length} observations`}
        onPointerMove={(e) => {
          const box = e.currentTarget.getBoundingClientRect();
          const coordinate =
            (((e.clientX - box.left) * 302) / box.width - 24) / 256;
          setInspected(
            trace.points.reduce(
              (best, p, i) =>
                Math.abs(p.x - coordinate) <
                Math.abs(trace.points[best].x - coordinate)
                  ? i
                  : best,
              0,
            ),
          );
        }}
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
        <path className="preference-axes" d="M20 136 H286" />
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
        <g className="preference-inspection" aria-hidden="true">
          <path
            d={`M${x(point.x)} ${y(high)} V${y(low)} M${x(point.x) - 4} ${y(high)} H${x(point.x) + 4} M${x(point.x) - 4} ${y(low)} H${x(point.x) + 4}`}
          />
          <circle cx={x(point.x)} cy={y(point.y)} r="3" />
        </g>
        <rect
          className="preference-hit"
          x="20"
          y="20"
          width="264"
          height="116"
          tabIndex={0}
          role="slider"
          aria-label="Inspect supplied trajectory points"
          aria-valuemin={1}
          aria-valuemax={trace.points.length}
          aria-valuenow={index + 1}
          aria-valuetext={readout}
          onKeyDown={(e) => {
            if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key))
              return;
            e.preventDefault();
            e.stopPropagation();
            setInspected(
              e.key === "Home"
                ? 0
                : e.key === "End"
                  ? trace.points.length - 1
                  : Math.max(
                      0,
                      Math.min(
                        trace.points.length - 1,
                        index + (e.key === "ArrowRight" ? 1 : -1),
                      ),
                    ),
            );
          }}
        />
        <text x="151" y="152" textAnchor="middle">
          {trace.start} → {trace.end}
        </text>
      </svg>
      <p className="preference-readout">
        {readout}. The sleeve is the supplied uncertainty, not a calibrated
        probability interval.
      </p>
    </div>
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
                {o.label} · {o.date}
              </strong>
              <p>{o.explanation}</p>
              <small>
                {o.horizon} · supplied cost {o.cost.toFixed(2)} on 0–1
              </small>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
