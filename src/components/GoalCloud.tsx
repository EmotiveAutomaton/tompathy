import { useEffect, useLayoutEffect, useRef, useState } from "react";
import {
  forceSimulation,
  forceX,
  forceY,
  type SimulationNodeDatum,
} from "d3-force";
import type { Hypothesis } from "../core/model";
import { HoverCard } from "./HoverCard";

export const weight = (h: Hypothesis) =>
  h.support
    ? (h.support.value - h.support.scale[0]) /
      (h.support.scale[1] - h.support.scale[0])
    : 0.25;
export const supportText = (h: Hypothesis) =>
  !h.support
    ? "Support not supplied"
    : h.support.semantics === "probability"
      ? `${Math.round(h.support.value * 100)}% declared probability`
      : `${h.support.value} on a ${h.support.scale.join("–")} relative support scale`;
type Word = SimulationNodeDatum & {
  id: string;
  width: number;
  height: number;
  font: number;
  lines: string[];
  tx: number;
  ty: number;
};
export function GoalCloud({
  goals,
  onInspect,
  list = false,
  active = true,
}: {
  goals: Hypothesis[];
  onInspect: (h: Hypothesis) => void;
  list?: boolean;
  active?: boolean;
}) {
  const host = useRef<HTMLDivElement>(null),
    memory = useRef(new Map<string, Word>());
  const [size, setSize] = useState({ width: 300, height: 260 });
  const [words, setWords] = useState<Word[]>([]);
  const [displayed, setDisplayed] = useState(goals);
  const [visible, setVisible] = useState(() => !document.hidden);
  useEffect(() => {
    const update = () => setVisible(!document.hidden);
    document.addEventListener("visibilitychange", update);
    return () => document.removeEventListener("visibilitychange", update);
  }, []);
  const latest = useRef(goals);
  latest.current = goals;
  const ids = goals.map((h) => h.id).join("|");
  useEffect(() => {
    setDisplayed((previous) => [
      ...goals,
      ...previous.filter((h) => !goals.some((g) => g.id === h.id)),
    ]);
    const timer = setTimeout(() => setDisplayed(latest.current), 480);
    return () => clearTimeout(timer);
  }, [ids]);
  useLayoutEffect(() => {
    const observer = new ResizeObserver(([entry]) =>
      setSize({
        width: entry.contentRect.width,
        height: entry.contentRect.height,
      }),
    );
    if (host.current) observer.observe(host.current);
    return () => observer.disconnect();
  }, []);
  const identity = goals
    .map((h) => `${h.id}:${h.label}:${weight(h)}`)
    .join("|");
  useLayoutEffect(() => {
    if (!size.width || !size.height) return;
    if (!visible) return;
    if (!active) {
      setWords([]);
      setDisplayed([]);
      return;
    }
    if (goals.length > 40 || list) {
      setWords([]);
      return;
    }
    const canvas = document.createElement("canvas").getContext("2d")!;
    const combined = goals.length > 8;
    const peak = combined ? Math.max(0.01, ...goals.map(weight)) : 1;
    const padding = 6;
    const gapX = 2,
      gapY = 3;
    const dominant = [...goals].sort((a, b) => weight(b) - weight(a))[0]?.id;
    const bounds = host.current?.getBoundingClientRect();
    const obstacles = bounds
      ? Array.from(
          host.current!.parentElement!.querySelectorAll(
            ".section-heading h2, .creator-control",
          ),
        ).map((el) => {
          const r = el.getBoundingClientRect();
          return {
            left: r.left - bounds.left - 3,
            right: r.right - bounds.left + 3,
            top: r.top - bounds.top - 3,
            bottom: r.bottom - bounds.top + 3,
          };
        })
      : [];
    const nodes: Word[] = goals.map((h) => {
      let font =
        (7 + Math.pow(weight(h) / peak, 1.65) * 27) *
        Math.min(1, size.width / 330);
      canvas.font = `${font}px Georgia`;
      const parts = h.label.split(/\s+/);
      let lines = [h.label];
      if (
        parts.length > 1 &&
        (h.label.length > 21 ||
          canvas.measureText(h.label).width > size.width * 0.56)
      ) {
        let best = Infinity;
        for (let split = 1; split < parts.length; split++) {
          const candidate = [
            parts.slice(0, split).join(" "),
            parts.slice(split).join(" "),
          ];
          const widths = candidate.map(
            (line) => canvas.measureText(line).width,
          );
          const score =
            Math.max(...widths) + Math.abs(widths[0] - widths[1]) * 0.25;
          if (score < best) {
            best = score;
            lines = candidate;
          }
        }
      }
      font *= Math.min(
        1,
        (size.width - 28) /
          Math.max(...lines.map((line) => canvas.measureText(line).width)),
      );
      canvas.font = `${font}px Georgia`;
      const width =
          Math.max(...lines.map((line) => canvas.measureText(line).width)) +
          padding,
        height = font * 1.25 * lines.length + padding;
      const previous = memory.current.get(h.id);
      const hash = Array.from(h.id).reduce(
        (sum, char) => (sum * 31 + char.charCodeAt(0)) >>> 0,
        17,
      );
      const angle = (hash % 628) / 100,
        radius =
          22 +
          (1 - weight(h)) * Math.min(size.width, size.height) * 0.36 +
          (hash % 29);
      const central = h.id === dominant;
      const tx = central
        ? size.width / 2
        : previous
          ? previous.x! * 0.55 +
            (size.width / 2 +
              Math.cos(angle) * Math.min(radius, size.width / 2.5)) *
              0.45
          : size.width / 2 +
            Math.cos(angle) * Math.min(radius, size.width / 2.5);
      const ty = central
        ? size.height / 2
        : previous
          ? previous.y! * 0.55 +
            (size.height / 2 +
              Math.sin(angle) * Math.min(radius, size.height / 2.5)) *
              0.45
          : size.height / 2 +
            Math.sin(angle) * Math.min(radius, size.height / 2.5);
      return {
        id: h.id,
        width,
        height,
        font,
        lines,
        tx,
        ty,
        x: tx,
        y: ty,
        ...(central ? { fx: tx, fy: ty } : {}),
      };
    });
    const simulation = forceSimulation(nodes)
      .stop()
      .force("x", forceX<Word>((n) => n.tx).strength(0.08))
      .force("y", forceY<Word>((n) => n.ty).strength(0.08));
    // Phrase-shaped collisions preserve horizontal labels; circular collision wastes space.
    simulation.force("phrases", () => {
      for (let i = 0; i < nodes.length; i++)
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i],
            b = nodes[j],
            dx = b.x! - a.x!,
            dy = b.y! - a.y!;
          const ox = (a.width + b.width) / 2 + gapX - Math.abs(dx),
            oy = (a.height + b.height) / 2 + gapY - Math.abs(dy);
          if (ox > 0 && oy > 0) {
            const share = a.fx != null || b.fx != null ? 1 : 0.5;
            if (ox < oy) {
              const push = (dx < 0 ? -1 : 1) * ox * share;
              if (a.fx == null) a.x! -= push;
              if (b.fx == null) b.x! += push;
            } else {
              const push = (dy < 0 ? -1 : 1) * oy * share;
              if (a.fy == null) a.y! -= push;
              if (b.fy == null) b.y! += push;
            }
          }
        }
      for (const n of nodes) {
        n.x = Math.max(
          n.width / 2 + 4,
          Math.min(size.width - n.width / 2 - 4, n.x!),
        );
        n.y = Math.max(
          n.height / 2 + 6,
          Math.min(size.height - n.height / 2 - 6, n.y!),
        );
      }
    });
    simulation.tick(90);
    // Settle into an exact rectangle packing. Force relaxation alone can leave
    // edge-clamped phrases overlapping in Chrome's narrow native panel.
    const ordered = [...nodes].sort(
      (a, b) =>
        Number(b.fx != null) - Number(a.fx != null) || b.width - a.width,
    );
    for (let attempt = 0; attempt < 12; attempt++) {
      const placed: Word[] = [];
      let fits = true;
      for (const n of ordered) {
        const free = (x: number, y: number) =>
          obstacles.every(
            (r) =>
              x + n.width / 2 < r.left ||
              x - n.width / 2 > r.right ||
              y + n.height / 2 < r.top ||
              y - n.height / 2 > r.bottom,
          ) &&
          placed.every(
            (p) =>
              Math.abs(x - p.x!) >= (n.width + p.width) / 2 + gapX ||
              Math.abs(y - p.y!) >= (n.height + p.height) / 2 + gapY,
          );
        let best: { x: number; y: number; distance: number } | undefined;
        if (n.fx != null && free(size.width / 2, size.height / 2))
          best = { x: size.width / 2, y: size.height / 2, distance: 0 };
        else
          for (
            let y = n.height / 2 + 5;
            y <= size.height - n.height / 2 - 5;
            y += 4
          )
            for (
              let x = n.width / 2 + 3;
              x <= size.width - n.width / 2 - 3;
              x += 4
            ) {
              const preferredX = memory.current.has(n.id) ? n.tx : n.x!;
              const preferredY = memory.current.has(n.id) ? n.ty : n.y!;
              const distance = (x - preferredX) ** 2 + (y - preferredY) ** 2;
              if ((!best || distance < best.distance) && free(x, y))
                best = { x, y, distance };
            }
        if (!best) {
          fits = false;
          break;
        }
        n.x = best.x;
        n.y = best.y;
        placed.push(n);
      }
      if (fits) break;
      for (const n of nodes) {
        n.width = (n.width - padding) * 0.93 + padding;
        n.height = (n.height - padding) * 0.93 + padding;
        n.font *= 0.93;
      }
    }
    for (const node of nodes) {
      memory.current.delete(node.id);
      memory.current.set(node.id, node);
    }
    // Keep recent positions without retaining every attention ID in a long reading.
    while (memory.current.size > 64)
      memory.current.delete(memory.current.keys().next().value!);
    setWords(nodes);
  }, [identity, size.width, size.height, list, active, visible]);
  const dense = list || goals.length > 40;
  const dominant = [...goals].sort((a, b) => weight(b) - weight(a))[0]?.id;
  return (
    <div
      ref={host}
      className={`living-cloud ${goals.length > 8 ? "cloud-combined" : ""} ${dense ? (list ? "cloud-list" : "cloud-overflow") : ""} ${visible ? "" : "cloud-suspended"}`}
      data-testid="goals"
    >
      {(active ? (dense ? goals : displayed) : []).map((old) => {
        const h = goals.find((g) => g.id === old.id) ?? old;
        const leaving = !goals.some((g) => g.id === h.id);
        const n = words.find((w) => w.id === h.id) ?? memory.current.get(h.id);
        const color =
          h.id === dominant
            ? "var(--green)"
            : ["var(--trace)", "#8b7964", "#6a8290"][
                Array.from(h.id).reduce(
                  (sum, char) => sum + char.charCodeAt(0),
                  0,
                ) % 3
              ];
        return (
          <div
            key={h.id}
            data-goal={h.id}
            data-dominant={h.id === dominant || undefined}
            aria-hidden={leaving || undefined}
            inert={leaving || undefined}
            className={`cloud-position ${leaving ? "cloud-leaving" : ""} ${h.id === dominant ? "cloud-center" : ""}`}
            style={
              dense
                ? list
                  ? undefined
                  : { fontSize: 9 + weight(h) * 16, color }
                : {
                    left: n?.x ?? size.width / 2,
                    top: n?.y ?? size.height / 2,
                    fontSize: n?.font ?? 18,
                    color,
                    maxWidth: size.width - 12,
                  }
            }
          >
            <HoverCard
              content={
                <>
                  <strong>{h.label}</strong>
                  <p className="hypothesis-summary">{h.description}</p>
                  <p className="muted support-summary">
                    {supportText(h)}. {h.support?.meaning}
                  </p>
                </>
              }
            >
              <button aria-label={h.label} onClick={() => onInspect(h)}>
                {(dense ? [h.label] : (n?.lines ?? [h.label])).map(
                  (line, i) => (
                    <span className="cloud-line" key={i}>
                      {line}{" "}
                    </span>
                  ),
                )}
              </button>
            </HoverCard>
          </div>
        );
      })}
      {(!active || !goals.length) && (
        <span className="attention-cue">
          {active ? "No attention supplied" : "hover"}
        </span>
      )}
    </div>
  );
}
