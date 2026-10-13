import { useEffect, useRef, useState, type RefObject } from "react";
import { select } from "d3-selection";
import {
  zoom,
  zoomIdentity,
  type ZoomTransform,
  type ZoomBehavior,
} from "d3-zoom";

/** Only the SVG receives gestures; reels and page scrolling retain their own controls. */
export function useHierarchyZoom(
  ref: RefObject<SVGSVGElement | null>,
  width: number,
  height: number,
  enabled: boolean,
  maxZoom = 32,
) {
  const [transform, setTransform] = useState(zoomIdentity);
  const behavior = useRef<ZoomBehavior<SVGSVGElement, unknown> | null>(null);
  const dragging = useRef(false);
  const displayed = useRef(zoomIdentity),
    animation = useRef(0);
  const reduced = useRef(false);
  const render = (target: ZoomTransform, smooth: boolean) => {
    cancelAnimationFrame(animation.current);
    const from = displayed.current,
      start = performance.now();
    const draw = (t: ZoomTransform) => {
      displayed.current = t;
      setTransform(t);
    };
    if (!smooth || reduced.current) return draw(target);
    const tick = (now: number) => {
      const progress = Math.min(1, (now - start) / 190),
        ease = 1 - (1 - progress) ** 3;
      draw(
        zoomIdentity
          .translate(
            from.x + (target.x - from.x) * ease,
            from.y + (target.y - from.y) * ease,
          )
          .scale(from.k + (target.k - from.k) * ease),
      );
      if (progress < 1) animation.current = requestAnimationFrame(tick);
    };
    animation.current = requestAnimationFrame(tick);
  };
  useEffect(() => {
    const svg = ref.current;
    if (!svg || !enabled) return;
    reduced.current = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const control = zoom<SVGSVGElement, unknown>()
      .extent([
        [0, 0],
        [width, height],
      ])
      .scaleExtent([1, maxZoom])
      .translateExtent([
        [-width / 2, -height / 2],
        [width * 1.5, height * 1.5],
      ])
      .clickDistance(5)
      .filter((e) => e.type !== "dblclick" && (!e.button || e.type === "wheel"))
      .on("start", (e) => {
        dragging.current =
          e.sourceEvent?.type === "mousedown" ||
          e.sourceEvent?.type === "touchstart";
      })
      .on("zoom", (e) => render(e.transform, !dragging.current))
      .on("end", () => {
        dragging.current = false;
      });
    const constrain = control.constrain();
    control.constrain((t, extent, translate) =>
      t.k <= 1.00001 ? zoomIdentity : constrain(t, extent, translate),
    );
    behavior.current = control;
    select(svg).call(control).on("dblclick.zoom", null);
    // Resizing keeps the selected area; a fresh dataset mounts a new component.
    return () => {
      select(svg).on(".zoom", null);
      behavior.current = null;
      cancelAnimationFrame(animation.current);
    };
  }, [ref, width, height, enabled, maxZoom]);
  const reset = () => {
    if (ref.current && behavior.current)
      select(ref.current).call(behavior.current.transform, zoomIdentity);
  };
  const key = (e: React.KeyboardEvent<SVGSVGElement>) => {
    const svg = ref.current,
      control = behavior.current;
    if (!svg || !control || e.target !== e.currentTarget) return;
    if (
      [
        "+",
        "=",
        "-",
        "0",
        "Home",
        "ArrowLeft",
        "ArrowRight",
        "ArrowUp",
        "ArrowDown",
      ].includes(e.key)
    ) {
      e.preventDefault();
      if (e.key === "0" || e.key === "Home") reset();
      else if (["+", "=", "-"].includes(e.key))
        select(svg).call(control.scaleBy, e.key === "-" ? 1 / 1.35 : 1.35);
      else
        select(svg).call(
          control.translateBy,
          (e.key === "ArrowLeft" ? 35 : e.key === "ArrowRight" ? -35 : 0) /
            transform.k,
          (e.key === "ArrowUp" ? 35 : e.key === "ArrowDown" ? -35 : 0) /
            transform.k,
        );
    }
  };
  const reveal = (x: number, y: number) => {
    const svg = ref.current,
      control = behavior.current;
    if (!svg || !control || transform.k <= 1) return;
    const px = transform.applyX(x),
      py = transform.applyY(y);
    if (px >= 15 && px <= width - 15 && py >= 15 && py <= height - 15) return;
    select(svg).call(
      control.transform,
      zoomIdentity
        .translate(width / 2 - x * transform.k, height / 2 - y * transform.k)
        .scale(transform.k),
    );
  };
  return { transform, reset, key, dragging, reveal };
}
