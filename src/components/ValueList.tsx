import type { Hypothesis, Packet } from "../core/model";
import { useLayoutEffect, useRef } from "react";
import { PreferenceChart, PreferenceObservations } from "./PreferenceChart";
import { HoverCard } from "./HoverCard";
import { confidenceWeight, weight } from "./GoalCloud";
import { DriveBrain } from "./DriveBrain";
import { driveFor } from "../core/drive-systems";
import { ContourCurrent } from "./ContourCurrent";
import {
  Compass,
  Flame,
  Shield,
  Heart,
  HandHeart,
  Users,
  Smile,
  Activity,
  Layers,
} from "lucide-react";

function ValueIcon({ h }: { h: Hypothesis }) {
  const icons = {
    seeking: Compass,
    rage: Flame,
    fear: Shield,
    lust: Heart,
    care: HandHeart,
    "panic-grief": Users,
    play: Smile,
    body: Activity,
    value: Layers,
  };
  const Icon = h.icon ? icons[h.icon] : null;
  return Icon ? (
    <Icon className="value-category-icon" size={20} aria-hidden="true" />
  ) : h.valueCategory ? (
    <ContourCurrent
      category={h.valueCategory}
      className="value-category-icon"
    />
  ) : (
    <Wheel value={h.support ? weight(h) : null} />
  );
}
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
  const drive = driveFor(h);
  const probability = h.support?.semantics === "probability";
  const score = h.support
    ? probability
      ? `${Math.round(h.support.value * 100)}% probability`
      : `${h.support.value.toFixed(2)} on ${h.support.scale.join("–")}`
    : "Unspecified";
  const scale = probability
    ? "Less  ·  probability  ·  More"
    : "Less  ·  support  ·  More";
  return (
    <>
      <div className="value-confidence-header" title={h.support?.meaning}>
        <strong className="value-card-title">
          <ValueIcon h={h} />
          <span>{h.label}</span>
        </strong>
        <div className="value-confidence-axis" aria-label={score}>
          <strong
            className="value-confidence-number"
            style={{ fontWeight: Math.max(400, confidenceWeight(h)) }}
          >
            {score}
          </strong>
          <svg
            viewBox="0 0 220 12"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <path d="M0 6.2 L211 4.5 L211 1 L220 6 L211 11 L211 7.5 Z" />
          </svg>
          <span className="value-confidence-legend" aria-hidden="true">
            {[...scale].map((c, i) => (
              <span
                key={i}
                style={{
                  fontWeight: 100 + (800 * i) / (scale.length - 1),
                  opacity: 0.28 + (0.72 * i) / (scale.length - 1),
                }}
              >
                {c}
              </span>
            ))}
          </span>
        </div>
      </div>
      <div className={`value-introduction ${drive ? "has-network" : ""}`}>
        <p>
          {drive?.description ??
            h.description
              .split(". Invented")[0]
              .replace(/^Constructed value: /, "")}
        </p>
        {drive && <DriveBrain h={h} />}
      </div>
      {h.preferenceTrace ? (
        <>
          <PreferenceChart trace={h.preferenceTrace} />
          <PreferenceObservations trace={h.preferenceTrace} />
        </>
      ) : (
        <>
          {h.evidence.slice(0, 3).map((id) => {
            const e = packet?.evidence.find((e) => e.id === id);
            return (
              e && (
                <p className="source-note" key={id}>
                  {e.excerpt}
                </p>
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
  const grid = useRef<HTMLDivElement>(null);
  const identity = values
    .map((h) => `${h.id}:${h.label}:${weight(h)}`)
    .join("|");
  useLayoutEffect(() => {
    const region = grid.current?.closest<HTMLElement>(".values-region"),
      heading = region?.querySelector(".section-heading h2");
    if (!region || !heading || !grid.current) return;
    const fit = () => {
      const title = heading.getBoundingClientRect(),
        scrollTop = grid.current!.parentElement!.scrollTop,
        previous =
          parseFloat(
            region.style.getPropertyValue("--values-heading-clearance"),
          ) || 0,
        scale = region.getBoundingClientRect().width / region.offsetWidth;
      const clearance = Math.max(
        0,
        ...Array.from(grid.current!.querySelectorAll(".core-value-row > span"))
          .slice(0, 2)
          .map((el) => {
            const label = el.getBoundingClientRect();
            return label.right > title.left - 3 && label.left < title.right
              ? (title.bottom + 3 - label.top) / scale - scrollTop + previous
              : 0;
          }),
      );
      region.style.setProperty(
        "--values-heading-clearance",
        `${Math.ceil(clearance)}px`,
      );
    };
    fit();
    const observer = new ResizeObserver(fit);
    observer.observe(grid.current);
    observer.observe(heading);
    // Font loading can wrap a label without resizing the fixed-height grid.
    for (const label of Array.from(
      grid.current.querySelectorAll(".core-value-row > span"),
    ).slice(0, 2))
      observer.observe(label);
    let alive = true;
    void document.fonts.ready.then(() => {
      if (alive) fit();
    });
    document.fonts.addEventListener("loadingdone", fit);
    return () => {
      alive = false;
      observer.disconnect();
      document.fonts.removeEventListener("loadingdone", fit);
    };
  }, [identity]);
  return (
    <div ref={grid} className="core-values" data-testid="values">
      {[...values]
        .sort(
          (a, b) =>
            Number(
              b.interpretation === "drive" || b.valueCategory === "drive",
            ) -
              Number(
                a.interpretation === "drive" || a.valueCategory === "drive",
              ) || (b.support ? weight(b) : -1) - (a.support ? weight(a) : -1),
        )
        .map((h) => (
          <HoverCard
            key={h.id}
            className="value-hover"
            content={<ValueDetails h={h} packet={packet} />}
          >
            <button
              className="core-value-row"
              style={{ fontWeight: confidenceWeight(h) }}
              onClick={() => inspect(h)}
            >
              <ValueIcon h={h} />
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
