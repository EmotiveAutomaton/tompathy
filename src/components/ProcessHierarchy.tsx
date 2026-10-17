import { Scan, ArrowLeft, Search } from "lucide-react";
import { useHierarchyZoom } from "./useHierarchyZoom";
import {
  useEffect,
  useLayoutEffect,
  useId,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  goalAt,
  goalGraph,
  hierarchyLayout,
  previewHierarchyLayout,
  instanceNeighborhood,
  instanceReelCandidates,
  type GoalNode,
  type GraphNode,
} from "../core/hierarchy";
import { SelectionLock } from "./SelectionLock";
import { EvidenceBadge } from "./PreviewStatus";
import type { AIMark } from "../core/ai-attribution";
import { AIOutlines } from "./AIOutlines";
const REEL_HEIGHT = 42;
// Measure the same system font used by the cells, so short labels can appear early.
const labelMeasure = document.createElement("canvas").getContext("2d")!;
labelMeasure.font = "12px system-ui";
function labelLines(text: string, width: number) {
  const capacity = Math.max(1, width - 4);
  let lines = 1,
    used = 0;
  for (const word of text.split(/\s+/)) {
    const space = used ? labelMeasure.measureText(" ").width : 0;
    const length = labelMeasure.measureText(word).width;
    if (used && used + space + length > capacity) {
      lines++;
      used = 0;
    }
    if (length <= capacity) used += (used ? space : 0) + length;
    else {
      for (const letter of word) {
        const size = labelMeasure.measureText(letter).width;
        if (used && used + size > capacity) {
          lines++;
          used = 0;
        }
        used += size;
      }
    }
  }
  return lines;
}
function Reel({
  column,
  candidates,
  ended,
  level,
  rank,
  onSelect,
  active,
  emphasized,
  expanded,
  onInspect,
  onExpand,
}: {
  column: GraphNode[];
  candidates: GraphNode[];
  ended: boolean;
  level: number;
  rank: number;
  onSelect: (n: GoalNode) => void;
  active: boolean;
  emphasized: boolean;
  expanded: boolean;
  onInspect: (node: GraphNode | null) => void;
  onExpand: () => void;
}) {
  const host = useRef<HTMLDivElement>(null);
  const ambiguous = candidates.length + Number(ended) > 1,
    exact = !ambiguous ? candidates[0] : undefined;
  const choice = candidates[0];
  const index = !active
    ? 0
    : choice
      ? Math.max(
          0,
          column.findIndex((n) => n.id === choice.id),
        )
      : column.length;
  const select = (next: number) => {
    const n = column[Math.max(0, Math.min(column.length - 1, next))];
    if (n && n.id !== exact?.id) onSelect(n.data);
  };
  const action = useRef(select),
    currentIndex = useRef(index);
  action.current = select;
  currentIndex.current = index;
  const wheelState = useRef({
    active,
    expanded,
    ambiguous,
    candidates: candidates.length,
    ended,
    length: column.length,
  });
  wheelState.current = {
    active,
    expanded,
    ambiguous,
    candidates: candidates.length,
    ended,
    length: column.length,
  };
  useEffect(() => {
    const el = host.current;
    if (!el) return;
    let delta = 0,
      last = 0;
    const wheel = (e: WheelEvent) => {
      const state = wheelState.current;
      if (!state.active || e.ctrlKey || !state.length || !state.candidates)
        return;
      // Long unresolved lists keep native scrolling. A resolved position always
      // advances this tier and pins the new node, even while its neighbors expand.
      if (
        state.expanded &&
        state.ambiguous &&
        state.candidates + Number(state.ended) > 7
      )
        return;
      e.preventDefault();
      e.stopPropagation();
      if (Math.sign(delta) !== Math.sign(e.deltaY)) delta = 0;
      delta +=
        e.deltaY * (e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? 100 : 1);
      if (Math.abs(delta) < 28 || performance.now() - last < 130) return;
      action.current(currentIndex.current + Math.sign(delta));
      delta = 0;
      last = performance.now();
    };
    const leave = () => {
      delta = 0;
    };
    el.addEventListener("wheel", wheel, { passive: false });
    el.addEventListener("mouseleave", leave);
    return () => {
      el.removeEventListener("wheel", wheel);
      el.removeEventListener("mouseleave", leave);
    };
    // Keep the wheel accumulator/cooldown across pinning and reel expansion.
  }, []);
  return (
    <div
      ref={host}
      role="group"
      tabIndex={active ? 0 : -1}
      className={`spool ${ambiguous || !active ? "ambiguous" : ""} ${active && !candidates.length ? "aperture-closed" : ""} ${emphasized ? "spool-emphasis" : ""} ${expanded && ambiguous ? "is-expanded" : ""}`}
      onMouseEnter={onExpand}
      onFocus={onExpand}
      data-level={level}
      data-rank={rank}
      data-selected={exact?.id ?? ""}
      data-candidates={[
        ...candidates.map((n) => n.id),
        ...(ended ? ["end"] : []),
      ].join(",")}
      aria-label={
        !active
          ? "No goal selected"
          : `${ambiguous ? `${candidates.length + Number(ended)} possible goals or endings; none selected` : (choice?.data.label ?? (ended ? "This path ends before this level" : "No supplied goal at this level"))}. Scroll or use arrow keys to choose.`
      }
      onKeyDown={(e) => {
        if (e.target !== e.currentTarget) return;
        if (["ArrowUp", "ArrowDown", "Home", "End"].includes(e.key)) {
          e.preventDefault();
          select(
            e.key === "Home"
              ? 0
              : e.key === "End"
                ? column.length - 1
                : index + (e.key === "ArrowDown" ? 1 : -1),
          );
        }
      }}
    >
      <div
        className="spool-window"
        style={{
          height:
            active && !candidates.length
              ? 2
              : expanded && ambiguous
                ? Math.min(7, candidates.length + Number(ended)) * REEL_HEIGHT +
                  2
                : REEL_HEIGHT,
        }}
      >
        {expanded && ambiguous ? (
          <div
            className="reel-options"
            role="group"
            aria-label="Possible goals"
            onMouseLeave={() => onInspect(null)}
            onKeyDown={(e) => {
              if (!["ArrowUp", "ArrowDown", "Home", "End"].includes(e.key))
                return;
              e.preventDefault();
              e.stopPropagation();
              const buttons = Array.from(
                e.currentTarget.querySelectorAll("button"),
              );
              const index = buttons.indexOf(e.target as HTMLButtonElement);
              const next =
                e.key === "Home"
                  ? 0
                  : e.key === "End"
                    ? buttons.length - 1
                    : Math.max(
                        0,
                        Math.min(
                          buttons.length - 1,
                          index + (e.key === "ArrowDown" ? 1 : -1),
                        ),
                      );
              buttons[next]?.focus();
            }}
          >
            {candidates.map((n) => (
              <button
                key={n.id}
                title={n.data.description}
                onMouseEnter={() => onInspect(n)}
                onFocus={() => onInspect(n)}
                onClick={() => onSelect(n.data)}
              >
                {n.data.label}
                <EvidenceBadge item={n.data} />
              </button>
            ))}
            {ended && <span className="reel-ending">Earlier end</span>}
          </div>
        ) : (
          <>
            <div
              className="spool-strip"
              style={{ transform: `translateY(${-index * REEL_HEIGHT}px)` }}
            >
              {column.map((n) => (
                <div key={n.id} className="spool-item" aria-hidden="true">
                  <span>{n.data.label}<EvidenceBadge item={n.data} /></span>
                </div>
              ))}
              <div className="spool-item spool-ending" aria-hidden="true" />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
export function ProcessHierarchy({
  nodes,
  orderUncertainGroups = [],
  region,
  offset,
  sourceHover,
  softNodeId,
  pinned,
  lockedNodeId,
  onHighlight,
  onLock,
  onFind,
  found = false,
  onSelect,
  lockReminder = 0,
  onBlockedFocus = () => {},
  previewGroups,
  markedAI,
}: {
  nodes: GoalNode[];
  orderUncertainGroups?: { id: string; nodes: string[]; explanation: string }[];
  region: string;
  offset: number;
  sourceHover: boolean;
  softNodeId?: string;
  pinned: boolean;
  lockedNodeId?: string;
  onHighlight: (node: GoalNode | null) => void;
  onLock: () => void;
  onFind: () => void;
  found?: boolean;
  onSelect: (node: GoalNode) => void;
  lockReminder?: number;
  onBlockedFocus?: (key: string) => void;
  previewGroups?: string[][];
  markedAI?: Map<string, AIMark>;
}) {
  const graph = useMemo(() => {
    const result = goalGraph(nodes);
    if (previewGroups) {
      for (const node of result.all) node.rank = node.data.level === "document" ? 1 : 0;
      result.depth = 1;
    }
    return result;
  }, [nodes, previewGroups]);
  const [entryId, setEntryId] = useState<string>();
  const tabEntry = graph.byId.has(entryId ?? "")
    ? entryId
    : (graph.all.find((n) => n.rank === 0) ?? graph.all[0])?.id;
  const [hovered, setHovered] = useState<{ id: string; key?: string } | null>(
      null,
    ),
    [heldInstance, setHeldInstance] = useState<{
      id: string;
      key?: string;
    } | null>(null),
    [height, setHeight] = useState(300),
    [width, setWidth] = useState(320),
    [expanded, setExpanded] = useState(false);
  const svg = useRef<SVGSVGElement>(null);
  const host = useRef<HTMLDivElement>(null),
    spools = useRef<HTMLDivElement>(null),
    clip = useId().replace(/:/g, "");
  useEffect(() => {
    if (!pinned) {
      setHovered(null);
      setExpanded(false);
      setHeldInstance(null);
    }
  }, [pinned]);
  useEffect(() => {
    if (!pinned && !softNodeId) setHovered(null);
  }, [pinned, softNodeId, region, offset]);
  useEffect(() => {
    if (!expanded) return;
    const move = (e: PointerEvent) => {
      if ((e.target as Element).closest(".process-lock")) return;
      const boxes = spools.current?.querySelectorAll(".spool-window");
      const inside = Array.from(boxes ?? []).some((el) => {
        const r = el.getBoundingClientRect();
        return (
          e.clientX >= r.left - 4 &&
          e.clientX <= r.right + 4 &&
          e.clientY >= r.top - 3 &&
          e.clientY <= r.bottom + 3
        );
      });
      if (!inside) {
        setExpanded(false);
        setHovered(null);
      }
    };
    document.addEventListener("pointermove", move, { passive: true });
    return () => document.removeEventListener("pointermove", move);
  }, [expanded]);
  useEffect(() => {
    const first = spools.current?.querySelector(".spool-window");
    if (!first) return;
    const observer = new ResizeObserver(([entry]) => {
      spools.current?.style.setProperty(
        "--first-reel-rise",
        `${Math.max(0, (entry.borderBoxSize[0]?.blockSize ?? entry.contentRect.height) - REEL_HEIGHT)}px`,
      );
    });
    observer.observe(first);
    return () => observer.disconnect();
  }, [nodes.length]);
  useEffect(() => {
    const observer = new ResizeObserver(([entry]) => {
      setHeight(Math.max(160, entry.contentRect.height));
      setWidth(entry.contentRect.width);
    });
    if (host.current) observer.observe(host.current);
    return () => observer.disconnect();
  }, [nodes.length]);
  const sourceId = goalAt(nodes, region, offset, graph)?.id;
  const selected = graph.byId.get(
    (pinned ? (lockedNodeId ?? sourceId) : (softNodeId ?? sourceId)) ?? "",
  );
  const inspected = expanded
    ? (graph.byId.get(hovered?.id ?? "") ?? selected)
    : selected;
  const ancestors = graph.ancestors(inspected),
    descendants = graph.descendants(inspected);
  const visible = !!selected && (sourceHover || pinned || !!softNodeId);
  const [tierShares, setTierShares] = useState<number[]>();
  const dividerDrag = useRef<{
    index: number;
    clientX: number;
    edges: number[];
    units: number;
  } | null>(null);
  const layout = useMemo(
    () => previewGroups ? previewHierarchyLayout(graph, previewGroups, height, 320, tierShares) : hierarchyLayout(graph, height, 320, tierShares),
    [graph, height, tierShares, previewGroups],
  );
  const resizeTier = (index: number, x: number, edges = layout.edges) => {
    const next = [...edges];
    const min = Math.min(24, (edges[index + 1] - edges[index - 1]) / 3);
    next[index] = Math.max(
      edges[index - 1] + min,
      Math.min(edges[index + 1] - min, x),
    );
    setTierShares(next.slice(1).map((edge, i) => edge - next[i]));
  };
  useLayoutEffect(() => {
    const el = host.current;
    const heading = el
      ?.closest(".region")
      ?.querySelector(".section-heading h2");
    if (!el || !heading) return;
    const fit = () => {
      const box = el.getBoundingClientRect(),
        label = heading.getBoundingClientRect();
      if (!box.width || !box.height) return;
      let clearance = 0;
      for (const tile of layout.tiles) {
        const radius = tile.node.parents.length ? 1.6 : 2.7;
        const left =
          box.left + ((tile.dotX - radius) / layout.width) * box.width;
        const right =
          box.left + ((tile.dotX + radius) / layout.width) * box.width;
        if (right < label.left - 2 || left > label.right + 2) continue;
        const fraction = (tile.dotY - radius) / layout.height;
        // Inset only when actual font metrics put the corner heading over a dot.
        // Shrinking the SVG by the same amount keeps its bottom and reels fixed.
        clearance = Math.max(
          clearance,
          (label.bottom + 2 - box.top - fraction * box.height) / (1 - fraction),
        );
      }
      el.style.setProperty(
        "--hierarchy-heading-clearance",
        `${Math.max(0, Math.ceil((clearance * height) / box.height))}px`,
      );
    };
    fit();
    const observer = new ResizeObserver(fit);
    observer.observe(el);
    observer.observe(heading);
    return () => observer.disconnect();
  }, [layout, height]);
  const labelBoxes = useMemo(
    () =>
      layout.tiles.map((t) =>
        layout.labelBox(
          t,
          { left: 0, top: 0, right: layout.width, bottom: layout.height },
          layout.width,
          layout.height,
        ),
      ),
    [layout],
  );
  const labelZoom = useMemo(() => {
    // One threshold, set by the hardest label. It depends on cell geometry,
    // never on which part of the graph happens to be inside the viewport.
    const fits = (k: number) =>
      layout.tiles.every((t, i) => {
        const box = labelBoxes[i],
          w = Math.min(240, ((box.width * width) / layout.width) * k - 4);
        const h = box.height * k - 4;
        return w >= 28 && h >= labelLines(t.node.data.label, w) * 15 + 4;
      });
    let low = 0,
      high = 1;
    while (!fits(high) && high < 2048) high *= 2;
    for (let i = 0; i < 18; i++) {
      const mid = (low + high) / 2;
      if (fits(mid)) high = mid;
      else low = mid;
    }
    return high;
  }, [layout, labelBoxes, width]);
  const navigation = useHierarchyZoom(
    svg,
    layout.width,
    layout.height,
    !layout.dense,
    Math.max(32, labelZoom * 1.5),
  );
  const reveal = graph.all.length === 1 ? 1 : Math.max(
    0,
    Math.min(1, (navigation.transform.k / labelZoom - 1) / 0.045),
  );
  const stretch = Math.max(
    0,
    Math.min(1, (navigation.transform.k / labelZoom - 0.35) / 0.65),
  );
  const scaleX = (width / layout.width) * navigation.transform.k;
  const scaleY =
    ((height -
      (parseFloat(
        host.current?.style.getPropertyValue("--hierarchy-heading-clearance") ??
          "0",
      ) || 0)) /
      layout.height) *
    navigation.transform.k;
  const selectedKey = pinned
    ? lockedNodeId && heldInstance?.id === selected?.id
      ? heldInstance?.key
      : undefined
    : softNodeId === hovered?.id
      ? hovered?.key
      : undefined;
  const branch = instanceNeighborhood(
    layout,
    expanded ? (hovered?.key ?? selectedKey) : selectedKey,
  );
  const lockedBranch = instanceNeighborhood(layout, selectedKey);
  const candidatesAt = (rank: number) =>
    instanceReelCandidates(graph, layout, selected, rank, selectedKey);
  const columns = Array.from({ length: graph.depth + 1 }, (_, rank) =>
    graph.all.filter((n) => n.rank === rank),
  );
  const showList = layout.dense;
  const canExpand =
    pinned && columns.some((_, rank) => candidatesAt(rank).ambiguous);
  const highlight = (node: GraphNode | null, key?: string) => {
    if (navigation.dragging.current || dividerDrag.current) return;
    if (pinned && node && node.id !== selected?.id)
      onBlockedFocus(key ?? node.id);
    if (node || pinned) setHovered(node ? { id: node.id, key } : null);
    if (!pinned && node) onHighlight(node.data);
  };
  const choose = (node: GoalNode, key?: string) => {
    const related = instanceNeighborhood(layout, selectedKey);
    const candidate = layout.tiles.find(
      (t) =>
        t.node.id === node.id &&
        (related.ancestors.has(t.key) || related.descendants.has(t.key)),
    );
    setHeldInstance({ id: node.id, key: key ?? candidate?.key });
    setHovered(null);
    setExpanded(false);
    onSelect(node);
  };
  const moveCell = (e: React.KeyboardEvent, node: GraphNode) => {
    if (!e.key.startsWith("Arrow")) return;
    e.preventDefault();
    e.stopPropagation();
    const origin = layout.tiles.find((t) => t.node.id === node.id);
    if (!origin) {
      const column = columns[node.rank];
      const adjacent =
        e.key === "ArrowUp"
          ? column[column.indexOf(node) - 1]
          : e.key === "ArrowDown"
            ? column[column.indexOf(node) + 1]
            : (e.key === "ArrowRight" ? node.parents : node.children)[0];
      if (adjacent) {
        choose(adjacent.data);
        host.current
          ?.querySelector<HTMLElement>(
            `[data-node="${CSS.escape(adjacent.id)}"]`,
          )
          ?.focus({ preventScroll: true });
      }
      return;
    }
    const vertical = e.key === "ArrowUp" || e.key === "ArrowDown";
    const candidates = layout.tiles.filter((t) =>
      vertical
        ? t.node.rank === node.rank &&
          (e.key === "ArrowUp" ? t.dotY < origin.dotY : t.dotY > origin.dotY)
        : (e.key === "ArrowRight" ? node.parents : node.children).some(
            (n) => n.id === t.node.id,
          ),
    );
    const next = candidates.sort(
      (a, b) => Math.abs(a.dotY - origin.dotY) - Math.abs(b.dotY - origin.dotY),
    )[0];
    if (!next) return;
    choose(next.node.data, next.key);
    host.current
      ?.querySelector<SVGElement>(`[data-node="${CSS.escape(next.node.id)}"]`)
      ?.focus({ preventScroll: true });
    navigation.reveal(next.dotX, next.dotY);
  };
  const classes = (n: GraphNode, key?: string) =>
    `pyramid-node ${visible && (branch.tile ? branch.ancestors.has(key ?? "") : ancestors.has(n.id)) ? "ancestor" : ""} ${visible && (branch.tile ? branch.descendants.has(key ?? "") : descendants.has(n.id)) ? "descendant" : ""} ${visible && selected?.id === n.id && (!selectedKey || key === selectedKey) ? "chosen" : ""}`;
  const orderMarks = orderUncertainGroups.flatMap((group) => {
    const tiles = layout.tiles.filter((t) => group.nodes.includes(t.node.id));
    if (tiles.length < 2) return [];
    // Membership is semantic: packing shared siblings under different parents
    // must not silently remove a supplied order-uncertainty mark.
    const common = tiles[0].node.parents.find((parent) =>
      tiles.every((t) => t.node.parents.some((p) => p.id === parent.id)),
    );
    const parent = layout.tiles.find((t) => t.node.id === common?.id);
    if (!parent) return [];
    const x = Math.max(...tiles.map((t) => t.x + t.width)) - 4;
    const top = Math.min(...tiles.map((t) => t.dotY)),
      bottom = Math.max(...tiles.map((t) => t.dotY));
    const steps = Math.max(2, Math.round((bottom - top) / 9));
    const d =
      `M${x},${top}` +
      Array.from({ length: steps }, (_, i) => {
        const y = top + ((bottom - top) * i) / steps,
          end = top + ((bottom - top) * (i + 1)) / steps;
        return ` Q${x + (i % 2 ? -2.8 : 2.8)},${(y + end) / 2} ${x},${end}`;
      }).join("");
    return [{ ...group, root: parent.rootId, d, parent }];
  });
  return (
    <div
      className={`goal-process ${expanded && canExpand ? "reels-open" : ""}`}
      data-testid="process"
    >
      {!nodes.length && !previewGroups ? (
        <span className="quiet-empty">No goal hierarchy supplied</span>
      ) : (
        <>
          <div
            ref={host}
            className={`pyramid ${showList ? "pyramid-list" : ""}`}
            aria-label={previewGroups?.length ? "Goal hierarchy. The outline reserves space for captured passages; empty space is still awaiting judgments." : "Goal hierarchy, local choices on the left, possible broader ends on the right"}
            onMouseLeave={() => highlight(null)}
            onBlur={(e) => {
              if (!e.currentTarget.contains(e.relatedTarget)) highlight(null);
            }}
          >
            {showList ? (
              columns.map((column, c) => (
                <div className="pyramid-column" key={c}>
                  {column.map((n) => (
                    <button
                      key={n.id}
                      data-node={n.id}
                      tabIndex={n.id === tabEntry ? 0 : -1}
                      className={classes(n)}
                      onMouseEnter={() => highlight(n)}
                      onFocus={() => {
                        setEntryId(n.id);
                        highlight(n);
                      }}
                      onClick={() => choose(n.data)}
                      onKeyDown={(e) => moveCell(e, n)}
                    >
                      {n.data.label}
                      <EvidenceBadge item={n.data} />
                    </button>
                  ))}
                </div>
              ))
            ) : (
              <svg
                ref={svg}
                tabIndex={-1}
                role="group"
                onPointerDown={(e) => {
                  e.currentTarget.dataset.pointerFocus = "true";
                }}
                onKeyDown={(e) => {
                  delete e.currentTarget.dataset.pointerFocus;
                  navigation.key(e);
                }}
                onBlur={(e) => {
                  delete e.currentTarget.dataset.pointerFocus;
                }}
                onClick={(e) => {
                  if (
                    !(e.target as Element).closest(
                      ".pyramid-node,.order-uncertain,.tier-divider",
                    )
                  ) {
                    setHovered(null);
                    onLock();
                  }
                }}
                onDoubleClick={onLock}
                data-zoom={navigation.transform.k.toFixed(3)}
                data-label-zoom={labelZoom.toFixed(3)}
                data-label-reveal={reveal.toFixed(3)}
                viewBox={`0 0 ${layout.width} ${layout.height}`}
                preserveAspectRatio="none"
                aria-label="Continuous hierarchy. Wheel or pinch to zoom, drag to pan. Drag a vertical divider to resize tiers. Keyboard: plus, minus, arrows; Home to fit."
                data-peaks={graph.roots.length}
              >
                <g transform={navigation.transform.toString()}>
                  <defs>
                    <clipPath id={clip}>
                      {layout.outline.map((d, i) => (
                        <path key={i} d={d} />
                      ))}
                    </clipPath>
                  </defs>
                  {layout.outline.map((d, i) => (
                    <path key={i} d={d} className="pyramid-silhouette" />
                  ))}
                  <g clipPath={`url(#${clip})`}>
                    {layout.tiles.map((t, i) => {
                      const box = labelBoxes[i];
                      const camera = navigation.transform;
                      const inView =
                        graph.all.length <= 600 ||
                        (camera.applyX(t.x + t.width) >= 0 &&
                          camera.applyX(t.x) <= layout.width &&
                          camera.applyY(t.dotY + t.dotHeight) >= 0 &&
                          camera.applyY(t.dotY - t.dotHeight) <= layout.height);
                      const availableWidth = Math.max(
                          0,
                          box.width * scaleX - 4,
                        ),
                        availableHeight = Math.max(0, box.height * scaleY - 4);
                      const lineWidth =
                        Math.min(
                          230,
                          t.node.data.label.length * 6.6,
                          availableWidth,
                        ) * stretch;
                      const waveX = t.dotX + (box.x - t.dotX) * stretch,
                        waveY = t.dotY + (box.y - t.dotY) * stretch;
                      const aiMark = markedAI?.get(t.node.id);
                      return (
                        <g
                          key={t.key}
                          role="button"
                          tabIndex={t.node.id === tabEntry ? 0 : -1}
                          data-node={t.node.id}
                          data-label-x={box.x}
                          data-label-y={box.y}
                          data-instance={t.key}
                          data-parent-instance={t.parentKey}
                          data-root={t.rootId}
                          data-exposure={t.exposure}
                          data-rank={t.node.rank}
                          className={`${classes(t.node, t.key)} ${markedAI?.has(t.node.id) ? "ai-marked" : ""}`}
                          aria-label={`${t.node.data.level ?? "Hierarchy"} goal: ${t.node.data.label}${aiMark ? ` · ${aiMark.description}` : ""}`}
                          aria-pressed={
                            pinned &&
                            selected?.id === t.node.id &&
                            (!selectedKey || selectedKey === t.key)
                          }
                          onMouseEnter={() => highlight(t.node, t.key)}
                          onFocus={() => {
                            setEntryId(t.node.id);
                            highlight(t.node, t.key);
                          }}
                          onClick={(e) => {
                            e.currentTarget.focus({ preventScroll: true });
                            choose(t.node.data, t.key);
                          }}
                          onKeyDown={(e) => {
                            moveCell(e, t.node);
                            if (e.key === " " || e.key === "Enter") {
                              e.preventDefault();
                              choose(t.node.data, t.key);
                            }
                          }}
                        >
                          <title>{t.node.data.label}{aiMark ? ` · ${aiMark.description}` : ""}{t.node.data.evidenceStatus ? ` · ${t.node.data.evidenceStatus} · ${t.node.data.basis}` : ""}</title>
                          <path
                            d={t.path}
                            className="brick-face"
                            style={{
                              strokeWidth: Math.min(
                                1.6,
                                Math.max(0.025, t.dotHeight * scaleY * 0.14),
                              ),
                            }}
                          />
                          {inView && (
                            <g
                              pointerEvents="none"
                              transform={`translate(${waveX},${waveY}) scale(${1 / scaleX},${1 / scaleY})`}
                              opacity={
                                t.dotHeight * scaleY < 3
                                  ? 0
                                  : (1 - reveal) * 0.5
                              }
                            >
                              <path
                                className="hierarchy-wave"
                                d={Array.from(
                                  { length: 17 },
                                  (_, j) =>
                                    `${j ? "L" : "M"}${(j / 16 - 0.5) * Math.max(1.3, lineWidth)},${j && j < 16 ? Math.sin(j * 2.7) * Math.sin((j * Math.PI) / 16) * stretch * 1.8 : 0}`,
                                ).join(" ")}
                              />
                              <circle
                                r={
                                  Math.min(1.05, (t.dotHeight * scaleY) / 5) *
                                  (1 - stretch)
                                }
                                pointerEvents="auto"
                              />
                            </g>
                          )}
                          {inView && reveal > 0 && (
                            <g
                              transform={`translate(${box.x},${box.y}) scale(${1 / scaleX},${1 / scaleY})`}
                              pointerEvents="none"
                            >
                              <foreignObject
                                x={-Math.min(240, availableWidth) / 2}
                                y={
                                  -Math.min(
                                    labelLines(
                                      t.node.data.label,
                                      Math.min(240, availableWidth),
                                    ) *
                                      15 +
                                      (t.node.data.evidenceStatus ? 21 : 6),
                                    availableHeight,
                                  ) / 2
                                }
                                width={Math.min(240, availableWidth)}
                                height={Math.min(
                                  labelLines(
                                    t.node.data.label,
                                    Math.min(240, availableWidth),
                                  ) *
                                    15 +
                                    (t.node.data.evidenceStatus ? 21 : 6),
                                  availableHeight,
                                )}
                                style={{ opacity: reveal }}
                              >
                                <div className="hierarchy-label">
                                  {t.node.data.label}
                                  <EvidenceBadge item={t.node.data} />
                                </div>
                              </foreignObject>
                            </g>
                          )}
                        </g>
                      );
                    })}
                  </g>
                  {visible &&
                    layout.links
                      .filter(
                        (link) =>
                          (ancestors.has(link.child) &&
                            ancestors.has(link.parent)) ||
                          (descendants.has(link.child) &&
                            descendants.has(link.parent)),
                      )
                      .map((link) => (
                        <g
                          key={`${link.child}:${link.parent}`}
                          pointerEvents="none"
                        >
                          <path
                            d={link.path}
                            className="hierarchy-crosslink"
                            data-child={link.child}
                            data-parent={link.parent}
                          />
                          {[link.from, link.to].map((point, i) => (
                            <ellipse
                              key={i}
                              className="hierarchy-link-end"
                              cx={point.x}
                              cy={point.y}
                              rx={1.3 / scaleX}
                              ry={1.3 / scaleY}
                            />
                          ))}
                        </g>
                      ))}
                  {orderMarks.map((m) => (
                    <g
                      key={`${m.id}:${m.root}`}
                      className="order-uncertain"
                      tabIndex={0}
                      role="button"
                      aria-label="Order uncertain"
                      onMouseEnter={() =>
                        highlight(m.parent.node, m.parent.key)
                      }
                      onFocus={() => highlight(m.parent.node, m.parent.key)}
                      onClick={() => choose(m.parent.node.data, m.parent.key)}
                      onKeyDown={(e) => {
                        if (["Enter", " "].includes(e.key)) {
                          e.preventDefault();
                          choose(m.parent.node.data, m.parent.key);
                        }
                      }}
                    >
                      <title>Order uncertain</title>
                      <path d={m.d} className="order-hit" />
                      <path d={m.d} className="order-line" />
                    </g>
                  ))}
                  {layout.edges.slice(1, -1).map((x, i) => {
                    const index = i + 1;
                    const d = layout
                      .slices(x)
                      .map(([a, b]) => `M${x},${a} V${b}`)
                      .join(" ");
                    return (
                      <g
                        key={index}
                        className="tier-divider"
                        role="separator"
                        tabIndex={0}
                        aria-label={`Resize tiers ${index} and ${index + 1}`}
                        aria-orientation="vertical"
                        aria-valuemin={Math.round(
                          (layout.edges[index - 1] / layout.width) * 100,
                        )}
                        aria-valuemax={Math.round(
                          (layout.edges[index + 1] / layout.width) * 100,
                        )}
                        aria-valuenow={Math.round((x / layout.width) * 100)}
                        data-boundary={index}
                        data-x={x}
                        onPointerDown={(e) => {
                          if (e.button !== 0) return;
                          e.preventDefault();
                          e.stopPropagation();
                          e.currentTarget.setPointerCapture(e.pointerId);
                          dividerDrag.current = {
                            index,
                            clientX: e.clientX,
                            edges: [...layout.edges],
                            units:
                              layout.width /
                              (svg.current!.getBoundingClientRect().width *
                                navigation.transform.k),
                          };
                        }}
                        onPointerMove={(e) => {
                          const drag = dividerDrag.current;
                          if (drag?.index === index) {
                            e.stopPropagation();
                            resizeTier(
                              index,
                              drag.edges[index] +
                                (e.clientX - drag.clientX) * drag.units,
                              drag.edges,
                            );
                          }
                        }}
                        onPointerUp={(e) => {
                          e.stopPropagation();
                          dividerDrag.current = null;
                          if (e.currentTarget.hasPointerCapture(e.pointerId))
                            e.currentTarget.releasePointerCapture(e.pointerId);
                        }}
                        onLostPointerCapture={() => {
                          dividerDrag.current = null;
                        }}
                        onClick={(e) => e.stopPropagation()}
                        onDoubleClick={(e) => {
                          e.stopPropagation();
                          setTierShares(undefined);
                        }}
                        onKeyDown={(e) => {
                          if (
                            ["ArrowLeft", "ArrowRight", "Home"].includes(e.key)
                          ) {
                            e.preventDefault();
                            e.stopPropagation();
                            if (e.key === "Home") setTierShares(undefined);
                            else
                              resizeTier(
                                index,
                                x + (e.key === "ArrowLeft" ? -4 : 4),
                              );
                          }
                        }}
                      >
                        <title>
                          Drag to resize tiers · double-click to reset widths
                        </title>
                        <path
                          d={d}
                          className="tier-divider-hit"
                          style={{ strokeWidth: 10 / scaleX }}
                        />
                        <path d={d} className="tier-divider-line" />
                      </g>
                    );
                  })}
                  <AIOutlines tiles={layout.tiles} marks={markedAI} width={layout.width} height={layout.height} />
                </g>
              </svg>
            )}
            {navigation.transform.k > 1.005 && !showList && (
              <button
                className="hierarchy-fit"
                aria-label="Fit whole hierarchy"
                title="Fit whole hierarchy (Home)"
                onClick={navigation.reset}
              >
                <Scan size={16} />
              </button>
            )}
          </div>
          <div
            ref={spools}
            className={`spool-area ${visible ? "is-visible" : "is-idle"}`}
            onMouseLeave={() => {
              setExpanded(false);
              if (pinned) setHovered(null);
            }}
            onBlur={(e) => {
              if (!e.currentTarget.contains(e.relatedTarget))
                setExpanded(false);
            }}
            onKeyDown={(e) => {
              if (e.key === "Escape" && expanded) {
                e.stopPropagation();
                setExpanded(false);
              }
            }}
          >
            <div
              className="odometer"
              aria-label="Selected goal path"
              data-testid="odometer"
            >
              {columns.map((column, rank) => {
                const candidates = candidatesAt(rank);
                return (
                  <Reel
                    key={rank}
                    column={column}
                    candidates={candidates.nodes}
                    ended={candidates.ended}
                    level={graph.depth - rank}
                    rank={rank}
                    onSelect={choose}
                    active={visible}
                    emphasized={
                      visible &&
                      ((expanded && selected?.rank === rank) ||
                        graph.byId.get(hovered?.id ?? "")?.rank === rank)
                    }
                    expanded={expanded && canExpand}
                    onExpand={() => {
                      if (canExpand) setExpanded(true);
                    }}
                    onInspect={(n) => {
                      const match = layout.tiles.find(
                        (t) =>
                          t.node.id === n?.id &&
                          (!lockedBranch.tile ||
                            lockedBranch.ancestors.has(t.key) ||
                            lockedBranch.descendants.has(t.key)),
                      );
                      setHovered(n ? { id: n.id, key: match?.key } : null);
                    }}
                  />
                );
              })}
            </div>
            {pinned && !found && !!selected?.data.regions.length && (
              <button
                className={`process-find ${found ? "was-found" : ""}`}
                aria-label="Find highlighted text in page"
                title="Find highlighted text in page"
                onClick={onFind}
                aria-pressed={found}
              >
                <ArrowLeft size={10} />
                <Search size={12} />
              </button>
            )}
            {pinned && (
              <SelectionLock
                className="process-lock"
                reminder={lockReminder}
                onUnlock={() => {
                  setHovered(null);
                  onLock();
                }}
              />
            )}
          </div>
        </>
      )}
    </div>
  );
}
