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
  instanceNeighborhood,
  instanceReelCandidates,
  type GoalNode,
  type GraphNode,
} from "../core/hierarchy";
import { SelectionLock } from "./SelectionLock";
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
  useEffect(() => {
    const el = host.current;
    if (!el) return;
    let delta = 0,
      last = 0;
    const wheel = (e: WheelEvent) => {
      if (!active || e.ctrlKey || !column.length) return;
      if (expanded && ambiguous && candidates.length + Number(ended) > 7)
        return;
      e.preventDefault();
      delta +=
        e.deltaY * (e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? 100 : 1);
      if (Math.abs(delta) < 28 || performance.now() - last < 130) return;
      action.current(currentIndex.current + Math.sign(delta));
      delta = 0;
      last = performance.now();
    };
    el.addEventListener("wheel", wheel, { passive: false });
    return () => el.removeEventListener("wheel", wheel);
  }, [active, column.length, expanded, ambiguous, candidates.length, ended]);
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
                  <span>{n.data.label}</span>
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
}) {
  const graph = useMemo(() => goalGraph(nodes), [nodes]);
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
  const sourceId = goalAt(nodes, region, offset)?.id;
  const selected = graph.byId.get(
    (pinned ? (lockedNodeId ?? sourceId) : (softNodeId ?? sourceId)) ?? "",
  );
  const inspected = expanded
    ? (graph.byId.get(hovered?.id ?? "") ?? selected)
    : selected;
  const ancestors = graph.ancestors(inspected),
    descendants = graph.descendants(inspected);
  const visible = !!selected && (sourceHover || pinned || !!softNodeId);
  const layout = useMemo(() => hierarchyLayout(graph, height), [graph, height]);
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
  const reveal = Math.max(
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
    if (navigation.dragging.current) return;
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
  const classes = (n: GraphNode, key?: string) =>
    `pyramid-node ${visible && (branch.tile ? branch.ancestors.has(key ?? "") : ancestors.has(n.id)) ? "ancestor" : ""} ${visible && (branch.tile ? branch.descendants.has(key ?? "") : descendants.has(n.id)) ? "descendant" : ""} ${visible && selected?.id === n.id && (!selectedKey || key === selectedKey) ? "chosen" : ""}`;
  const orderMarks = orderUncertainGroups.flatMap((group) =>
    graph.roots.flatMap((root) => {
      const tiles = layout.tiles.filter(
        (t) => t.rootId === root.id && group.nodes.includes(t.node.id),
      );
      if (tiles.length < 2) return [];
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
      const parent = layout.tiles.find((t) => t.key === tiles[0].parentKey);
      if (!parent || !tiles.every((t) => t.parentKey === parent.key)) return [];
      return [{ ...group, root: root.id, d, parent }];
    }),
  );
  return (
    <div
      className={`goal-process ${expanded && canExpand ? "reels-open" : ""}`}
      data-testid="process"
    >
      {!nodes.length ? (
        <span className="quiet-empty">No goal hierarchy supplied</span>
      ) : (
        <>
          <div
            ref={host}
            className={`pyramid ${showList ? "pyramid-list" : ""}`}
            aria-label="Goal hierarchy, local choices on the left, possible broader ends on the right"
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
                      className={classes(n)}
                      onMouseEnter={() => highlight(n)}
                      onFocus={() => highlight(n)}
                      onClick={() => choose(n.data)}
                    >
                      {n.data.label}
                    </button>
                  ))}
                </div>
              ))
            ) : (
              <svg
                ref={svg}
                tabIndex={0}
                role="group"
                onKeyDown={navigation.key}
                onClick={(e) => {
                  if (
                    !(e.target as Element).closest(
                      ".pyramid-node,.order-uncertain",
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
                aria-label="Continuous hierarchy. Wheel or pinch to zoom, drag to pan. Keyboard: plus, minus, arrows; Home to fit."
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
                      return (
                        <g
                          key={t.key}
                          role="button"
                          tabIndex={0}
                          data-node={t.node.id}
                          data-label-x={box.x}
                          data-label-y={box.y}
                          data-instance={t.key}
                          data-parent-instance={t.parentKey}
                          data-root={t.rootId}
                          data-exposure={t.exposure}
                          data-rank={t.node.rank}
                          className={classes(t.node, t.key)}
                          aria-label={`${t.node.data.level ?? "Hierarchy"} goal: ${t.node.data.label}`}
                          aria-pressed={
                            pinned &&
                            selected?.id === t.node.id &&
                            (!selectedKey || selectedKey === t.key)
                          }
                          onMouseEnter={() => highlight(t.node, t.key)}
                          onFocus={() => highlight(t.node, t.key)}
                          onClick={() => choose(t.node.data, t.key)}
                          onKeyDown={(e) => {
                            if (e.key === " " || e.key === "Enter") {
                              e.preventDefault();
                              choose(t.node.data, t.key);
                            }
                          }}
                        >
                          <path d={t.path} className="brick-face" />
                          <g
                            pointerEvents="none"
                            transform={`translate(${waveX},${waveY}) scale(${1 / scaleX},${1 / scaleY})`}
                            opacity={
                              t.dotHeight * scaleY < 3 ? 0 : (1 - reveal) * 0.5
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
                          {reveal > 0 && (
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
                                      6,
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
                                    6,
                                  availableHeight,
                                )}
                                style={{ opacity: reveal }}
                              >
                                <div className="hierarchy-label">
                                  {t.node.data.label}
                                </div>
                              </foreignObject>
                            </g>
                          )}
                        </g>
                      );
                    })}
                  </g>
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
            {pinned &&
              selected?.data.span &&
              columns.every((_, rank) => !candidatesAt(rank).ambiguous) && (
                <button
                  className={`process-find ${found ? "was-found" : ""}`}
                  aria-label="Find locked sentence in page"
                  title="Find locked sentence in page"
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
