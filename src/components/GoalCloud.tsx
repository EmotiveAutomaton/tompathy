import { useLayoutEffect, useRef, useState } from "react";
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
  tx: number;
  ty: number;
};
export function GoalCloud({
  goals,
  onInspect,
  list = false,
}: {
  goals: Hypothesis[];
  onInspect: (h: Hypothesis) => void;
  list?: boolean;
}) {
  const host = useRef<HTMLDivElement>(null),
    memory = useRef(new Map<string, Word>());
  const [size, setSize] = useState({ width: 300, height: 260 });
  const [words, setWords] = useState<Word[]>([]);
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
    if (goals.length > 12 || list) {
      setWords([]);
      return;
    }
    const canvas = document.createElement("canvas").getContext("2d")!;
    const nodes: Word[] = goals.map((h, i) => {
      let font = (13 + weight(h) * 21) * Math.min(1, size.width / 330);
      canvas.font = `${font}px Georgia`;
      font *= Math.min(
        1,
        (size.width - 28) / canvas.measureText(h.label).width,
      );
      canvas.font = `${font}px Georgia`;
      const width = canvas.measureText(h.label).width + 12,
        height = font * 1.4 + 12;
      const previous = memory.current.get(h.id);
      const angle = i * 2.4,
        radius = 44 + i * 10;
      const central = h.interpretation === "governing-purpose";
      const tx = central
        ? size.width / 2
        : (previous?.x ??
          size.width / 2 + Math.cos(angle) * Math.min(radius, size.width / 4));
      const ty = central
        ? size.height / 2
        : (previous?.y ??
          size.height / 2 +
            Math.sin(angle) * Math.min(radius, size.height / 3));
      return {
        id: h.id,
        width,
        height,
        font,
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
          const ox = (a.width + b.width) / 2 + 5 - Math.abs(dx),
            oy = (a.height + b.height) / 2 + 7 - Math.abs(dy);
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
          placed.every(
            (p) =>
              Math.abs(x - p.x!) >= (n.width + p.width) / 2 + 5 ||
              Math.abs(y - p.y!) >= (n.height + p.height) / 2 + 7,
          );
        let best: { x: number; y: number; distance: number } | undefined;
        if (n.fx != null)
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
        n.width *= 0.93;
        n.height *= 0.93;
        n.font *= 0.93;
      }
    }
    for (const node of nodes) memory.current.set(node.id, node);
    setWords(nodes);
  }, [identity, size.width, size.height, list]);
  const dense = list || goals.length > 12;
  return (
    <div
      ref={host}
      className={`living-cloud ${dense ? "cloud-list" : ""}`}
      data-testid="goals"
    >
      {goals.map((h, i) => {
        const n = words.find((w) => w.id === h.id);
        const color =
          h.interpretation === "governing-purpose"
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
            className={`cloud-position ${h.interpretation === "governing-purpose" ? "cloud-center" : ""}`}
            style={
              dense
                ? undefined
                : {
                    left: n?.x ?? size.width / 2,
                    top: n?.y ?? size.height / 2,
                    fontSize: n?.font ?? 18,
                    color,
                    maxWidth: size.width - 12,
                    animationDelay: `${i * -0.6}s`,
                  }
            }
          >
            <HoverCard
              content={
                <>
                  <strong>{h.label}</strong>
                  <p>{h.description}</p>
                  <p className="muted">
                    {supportText(h)}. {h.support?.meaning}
                  </p>
                </>
              }
            >
              <button onClick={() => onInspect(h)}>{h.label}</button>
            </HoverCard>
          </div>
        );
      })}
      {!goals.length && <span className="quiet-empty">No goals supplied</span>}
    </div>
  );
}
