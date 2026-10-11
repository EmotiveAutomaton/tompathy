import { useEffect, useId, useMemo, useRef, useState } from "react";
import { LockKeyhole, LockKeyholeOpen } from "lucide-react";
import { goalAt, goalTree, type GoalNode } from "../core/hierarchy";
import type { HierarchyNode } from "d3-hierarchy";

const REEL_HEIGHT = 56;
type Node = HierarchyNode<GoalNode>;
function Reel({
  column,
  exact,
  candidates,
  level,
  onSelect,
  active,
}: {
  column: Node[];
  exact?: Node;
  candidates: Node[];
  level: number;
  onSelect: (node: GoalNode) => void;
  active: boolean;
}) {
  const host = useRef<HTMLDivElement>(null);
  const choice = exact ?? candidates[0];
  const ambiguous = !exact && candidates.length > 1;
  const index = Math.max(
    0,
    column.findIndex((n) => n.id === choice?.id),
  );
  const select = (next: number) => {
    const n = column[Math.max(0, Math.min(column.length - 1, next))];
    if (n && n.id !== exact?.id) onSelect(n.data);
  };
  const action = useRef(select);
  action.current = select;
  const currentIndex = useRef(index);
  currentIndex.current = index;
  useEffect(() => {
    const el = host.current;
    if (!el) return;
    let delta = 0,
      last = 0;
    const wheel = (e: WheelEvent) => {
      if (!active || e.ctrlKey || column.length < 2) return;
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
      className={`spool ${ambiguous ? "ambiguous" : ""}`}
      role="group"
      tabIndex={active ? 0 : -1}
      data-level={level}
      data-selected={exact?.id ?? ""}
      aria-label={`${ambiguous ? `${candidates.length} possible subordinate goals; none selected` : (choice?.data.label ?? "No goal at this level")}. Scroll or use arrow keys to choose a goal.`}
      onKeyDown={(e) => {
        if (["ArrowDown", "ArrowUp", "Home", "End"].includes(e.key)) {
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
          {(choice ? column : []).map((n) => (
            <div key={n.id} className="spool-item" aria-hidden="true">
              <span>{n.data.label}</span>
            </div>
          ))}
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
  list = false,
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
  list?: boolean;
}) {
  const tree = useMemo(() => goalTree(nodes), [nodes]);
  const [hovered, setHovered] = useState<string | null>(null);
  const clip = useId().replace(/:/g, "");
  const all = tree?.descendants() ?? [],
    depth = tree?.height ?? 0;
  const leaves = tree?.leaves() ?? [];
  const selected = all.find(
    (n) =>
      n.id === (hovered ?? lockedNodeId ?? goalAt(nodes, region, offset)?.id),
  );
  const ancestors = new Set(selected?.ancestors().map((n) => n.id));
  const descendants = new Set(selected?.descendants().map((n) => n.id));
  const visible = !!selected && (sourceHover || pinned || !!hovered);
  const columns = Array.from({ length: depth + 1 }, (_, d) =>
    all.filter((n) => n.depth === depth - d),
  );
  const showList = list || nodes.length > 120;
  const highlight = (node: Node | null) => {
    setHovered(node?.data.id ?? null);
    onHighlight(node?.data ?? null);
  };
  const choose = (node: GoalNode) => {
    highlight(null);
    onSelect(node);
  };
  const classes = (n: Node) =>
    `pyramid-node ${visible && ancestors.has(n.id) ? "ancestor" : ""} ${visible && descendants.has(n.id) ? "descendant" : ""} ${visible && selected?.id === n.id ? "chosen" : ""}`;
  // Every brick spans its descendants, so adjacent columns share a single silhouette.
  const bounds = (n: Node) => {
    const indices = n
      .leaves()
      .map((l) => leaves.findIndex((a) => a.id === l.id));
    const y = (Math.min(...indices) / leaves.length) * 252;
    return {
      y,
      height: ((Math.max(...indices) + 1) / leaves.length) * 252 - y,
    };
  };
  const shape =
    "M4 0 Q180 0 320 126 Q180 252 4 252 Q0 252 0 248 L0 4 Q0 0 4 0 Z";
  return (
    <div className="goal-process" data-testid="process">
      {!nodes.length ? (
        <span className="quiet-empty">No goal hierarchy supplied</span>
      ) : (
        <>
          <div
            className={`pyramid ${showList ? "pyramid-list" : ""}`}
            aria-label="Goal hierarchy, local choices on the left, broader goals on the right"
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
                viewBox="0 0 320 252"
                preserveAspectRatio="none"
                aria-label="Continuous hierarchy"
              >
                <defs>
                  <clipPath id={clip}>
                    <path d={shape} />
                  </clipPath>
                </defs>
                <path className="pyramid-silhouette" d={shape} />
                <g clipPath={`url(#${clip})`}>
                  {columns.map((column, c) =>
                    column.map((n) => {
                      const { y, height } = bounds(n),
                        width = 320 / columns.length,
                        x = c * width;
                      return (
                        <g
                          key={n.id}
                          data-node={n.id}
                          role="button"
                          tabIndex={0}
                          className={classes(n)}
                          aria-label={`${n.data.level ? `${n.data.level} goal` : "Goal"}: ${n.data.label}`}
                          aria-pressed={pinned && lockedNodeId === n.id}
                          onMouseEnter={() => highlight(n)}
                          onFocus={() => highlight(n)}
                          onClick={() => choose(n.data)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" || e.key === " ") {
                              e.preventDefault();
                              choose(n.data);
                            }
                          }}
                        >
                          <rect x={x} y={y} width={width} height={height} />
                          <circle
                            cx={x + width / 2}
                            cy={y + height / 2}
                            r={c === columns.length - 1 ? 2.7 : 1.6}
                          />
                        </g>
                      );
                    }),
                  )}
                </g>
              </svg>
            )}
          </div>
          <div
            className={`spool-area ${visible ? "is-visible" : ""}`}
            aria-hidden={!visible}
            inert={!visible || undefined}
          >
            <div
              className="node-explanation"
              role="status"
              title={selected?.data.description}
            >
              {selected?.data.label}
            </div>
            <div
              className="odometer"
              aria-label="Selected goal path"
              data-testid="odometer"
            >
              {columns.map((column, c) => (
                <Reel
                  key={depth - c}
                  column={column}
                  exact={column.find((n) => ancestors.has(n.id))}
                  candidates={column.filter((n) => descendants.has(n.id))}
                  level={depth - c}
                  onSelect={choose}
                  active={visible}
                />
              ))}
            </div>
            <button
              className={`process-lock ${pinned ? "is-locked" : ""}`}
              aria-label={pinned ? "Unlock selection" : "Lock selection"}
              aria-pressed={pinned}
              title={
                pinned ? "Unlock selection · Escape" : "Hold this selection"
              }
              onClick={() =>
                pinned ? onLock() : selected && onSelect(selected.data)
              }
            >
              {pinned ? (
                <LockKeyhole size={12} />
              ) : (
                <LockKeyholeOpen size={12} />
              )}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
