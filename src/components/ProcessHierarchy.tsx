import { useEffect, useId, useMemo, useRef, useState } from "react";
import {
  goalAt,
  goalGraph,
  hierarchyLayout,
  reelCandidates,
  type GoalNode,
  type GraphNode,
  type GoalGraph,
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
}: {
  column: GraphNode[];
  candidates: GraphNode[];
  ended: boolean;
  level: number;
  onSelect: (n: GoalNode) => void;
  active: boolean;
  emphasized: boolean;
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
      className={`spool ${ambiguous || !active ? "ambiguous" : ""} ${emphasized ? "spool-emphasis" : ""}`}
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
      <div className="spool-window">
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
  const ancestors = graph.ancestors(selected),
    descendants = graph.descendants(selected);
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
    <div className="goal-process" data-testid="process">
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
            {expanded && canExpand && selected && (
              <ReelBranches
                graph={graph}
                selected={selected}
                onSelect={choose}
              />
            )}
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
                    emphasized={graph.byId.get(hovered ?? "")?.rank === rank}
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

function ReelBranches({
  graph,
  selected,
  onSelect,
}: {
  graph: GoalGraph;
  selected: GraphNode;
  onSelect: (node: GoalNode) => void;
}) {
  const columns = Array.from({ length: graph.depth + 1 }, (_, rank) =>
    reelCandidates(graph, selected, rank),
  );
  const rows = Math.max(
    2,
    ...columns.map((c) => c.nodes.length + Number(c.ended)),
  );
  const height = rows * 43 + 12,
    width = columns.length * 82;
  const positions = new Map<string, { x: number; y: number }>();
  columns.forEach((c, rank) =>
    c.nodes.forEach((n, i) =>
      positions.set(n.id, {
        x: rank * 82 + 41,
        y: 6 + ((i + 0.5) * (height - 12)) / (c.nodes.length + Number(c.ended)),
      }),
    ),
  );
  return (
    <div
      className="reel-branches"
      role="group"
      aria-label="Possible connected goals"
    >
      <div
        className="branch-canvas"
        style={{ height, width, minWidth: "100%" }}
      >
        <svg
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          {[...positions].flatMap(([id, p]) =>
            graph.byId.get(id)!.parents.flatMap((parent) => {
              const end = positions.get(parent.id);
              if (!end) return [];
              return (
                <path
                  key={`${id}:${parent.id}`}
                  data-edge={`${id}:${parent.id}`}
                  d={`M${p.x + 32} ${p.y} C${(p.x + end.x) / 2} ${p.y},${(p.x + end.x) / 2} ${end.y},${end.x - 32} ${end.y}`}
                />
              );
            }),
          )}
        </svg>
        {[...positions].map(([id, p]) => (
          <button
            key={id}
            className={`branch-choice ${id === selected.id ? "anchor-choice" : ""}`}
            style={{
              left: `${(p.x / width) * 100}%`,
              top: p.y,
              width: `${(67 / width) * 100}%`,
            }}
            title={`${graph.byId.get(id)!.data.label}. ${graph.byId.get(id)!.data.description}`}
            onClick={() => onSelect(graph.byId.get(id)!.data)}
          >
            {graph.byId.get(id)!.data.label}
          </button>
        ))}
        {columns.map(
          (c, rank) =>
            c.ended && (
              <span
                className="branch-ending"
                key={rank}
                style={{
                  left: `${((rank + 0.5) / columns.length) * 100}%`,
                  top:
                    6 +
                    ((c.nodes.length + 0.5) * (height - 12)) /
                      (c.nodes.length + 1),
                }}
              >
                Earlier end
              </span>
            ),
        )}
      </div>
    </div>
  );
}
