import { useEffect, useId, useMemo, useRef, useState } from "react";
import {
  goalAt,
  goalGraph,
  hierarchyLayout,
  reelCandidates,
  type GoalNode,
  type GraphNode,
} from "../core/hierarchy";
import { SelectionLock } from "./SelectionLock";
const REEL_HEIGHT = 42;
function Reel({
  column,
  candidates,
  ended,
  level,
  onSelect,
  active,
  emphasized,
  expanded,
  onInspect,
}: {
  column: GraphNode[];
  candidates: GraphNode[];
  ended: boolean;
  level: number;
  onSelect: (n: GoalNode) => void;
  active: boolean;
  emphasized: boolean;
  expanded: boolean;
  onInspect: (node: GraphNode | null) => void;
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
  }, [active, column.length]);
  return (
    <div
      ref={host}
      role="group"
      tabIndex={active ? 0 : -1}
      className={`spool ${ambiguous || !active ? "ambiguous" : ""} ${emphasized ? "spool-emphasis" : ""} ${expanded && ambiguous ? "is-expanded" : ""}`}
      data-level={level}
      data-selected={exact?.id ?? ""}
      data-candidates={[
        ...candidates.map((n) => n.id),
        ...(ended ? ["end"] : []),
      ].join(",")}
      aria-label={
        !active
          ? "No goal selected"
          : `${ambiguous ? `${candidates.length + Number(ended)} possible goals or endings; none selected` : (choice?.data.label ?? "This path ends before this level")}. Scroll or use arrow keys to choose.`
      }
      onKeyDown={(e) => {
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
            expanded && ambiguous
              ? Math.min(7, candidates.length + Number(ended)) * REEL_HEIGHT + 2
              : REEL_HEIGHT,
        }}
      >
        {expanded && ambiguous ? (
          <div
            className="reel-options"
            role="group"
            aria-label="Possible goals"
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
              <div className="spool-item spool-ending" aria-hidden="true">
                —
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
export function ProcessHierarchy({
  nodes,
  region,
  offset,
  sourceHover,
  pinned,
  lockedNodeId,
  onHighlight,
  onLock,
  onSelect,
}: {
  nodes: GoalNode[];
  region: string;
  offset: number;
  sourceHover: boolean;
  pinned: boolean;
  lockedNodeId?: string;
  onHighlight: (node: GoalNode | null) => void;
  onLock: () => void;
  onSelect: (node: GoalNode) => void;
}) {
  const graph = useMemo(() => goalGraph(nodes), [nodes]);
  const [hovered, setHovered] = useState<string | null>(null),
    [height, setHeight] = useState(300),
    [expanded, setExpanded] = useState(false);
  const host = useRef<HTMLDivElement>(null),
    clip = useId().replace(/:/g, "");
  useEffect(() => {
    if (!pinned) {
      setHovered(null);
      setExpanded(false);
    }
  }, [pinned]);
  useEffect(() => {
    const observer = new ResizeObserver(([entry]) =>
      setHeight(Math.max(160, entry.contentRect.height)),
    );
    if (host.current) observer.observe(host.current);
    return () => observer.disconnect();
  }, [nodes.length]);
  const sourceId = goalAt(nodes, region, offset)?.id;
  const selected = graph.byId.get(
    (pinned ? (lockedNodeId ?? sourceId) : (hovered ?? sourceId)) ?? "",
  );
  const inspected = expanded
    ? (graph.byId.get(hovered ?? "") ?? selected)
    : selected;
  const ancestors = graph.ancestors(inspected),
    descendants = graph.descendants(inspected);
  const visible = !!selected && (sourceHover || pinned || !!hovered);
  const layout = useMemo(() => hierarchyLayout(graph, height), [graph, height]);
  const columns = Array.from({ length: graph.depth + 1 }, (_, rank) =>
    graph.all.filter((n) => n.rank === rank),
  );
  const showList = nodes.length > 120 || graph.roots.length > 4 || layout.dense;
  const canExpand =
    pinned &&
    columns.some((_, rank) => reelCandidates(graph, selected, rank).ambiguous);
  const highlight = (node: GraphNode | null) => {
    setHovered(node?.id ?? null);
    if (!pinned) onHighlight(node?.data ?? null);
  };
  const choose = (node: GoalNode) => {
    setHovered(null);
    setExpanded(false);
    onSelect(node);
  };
  const classes = (n: GraphNode) =>
    `pyramid-node ${visible && ancestors.has(n.id) ? "ancestor" : ""} ${visible && descendants.has(n.id) ? "descendant" : ""} ${visible && selected?.id === n.id ? "chosen" : ""}`;
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
                viewBox={`0 0 ${layout.width} ${layout.height}`}
                preserveAspectRatio="none"
                aria-label="Continuous hierarchy"
                data-peaks={graph.roots.length}
              >
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
                  {layout.tiles.map((t) => (
                    <g
                      key={t.key}
                      role="button"
                      tabIndex={0}
                      data-node={t.node.id}
                      data-instance={t.key}
                      data-parent-instance={t.parentKey}
                      data-root={t.rootId}
                      data-exposure={t.exposure}
                      data-rank={t.node.rank}
                      className={classes(t.node)}
                      aria-label={`${t.node.data.level ?? "Hierarchy"} goal: ${t.node.data.label}`}
                      aria-pressed={pinned && selected?.id === t.node.id}
                      onMouseEnter={() => highlight(t.node)}
                      onFocus={() => highlight(t.node)}
                      onClick={() => choose(t.node.data)}
                      onKeyDown={(e) => {
                        if (e.key === " " || e.key === "Enter") {
                          e.preventDefault();
                          choose(t.node.data);
                        }
                      }}
                    >
                      <path d={t.path} className="brick-face" />
                      <circle
                        cx={t.dotX}
                        cy={t.dotY}
                        r={t.node.parents.length ? 1.6 : 2.7}
                      />
                    </g>
                  ))}
                </g>
              </svg>
            )}
          </div>
          <div
            className={`spool-area ${visible ? "is-visible" : "is-idle"}`}
            onMouseLeave={() => setExpanded(false)}
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
              onMouseEnter={() => {
                if (canExpand) setExpanded(true);
              }}
              onFocus={() => {
                if (canExpand) setExpanded(true);
              }}
              aria-label="Selected goal path"
              data-testid="odometer"
            >
              {columns.map((column, rank) => {
                const candidates = reelCandidates(graph, selected, rank);
                return (
                  <Reel
                    key={rank}
                    column={column}
                    candidates={candidates.nodes}
                    ended={candidates.ended}
                    level={graph.depth - rank}
                    onSelect={choose}
                    active={visible}
                    emphasized={
                      (expanded && selected?.rank === rank) ||
                      graph.byId.get(hovered ?? "")?.rank === rank
                    }
                    expanded={expanded && canExpand}
                    onInspect={(n) => setHovered(n?.id ?? null)}
                  />
                );
              })}
            </div>
            {pinned && (
              <SelectionLock
                className="process-lock"
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
