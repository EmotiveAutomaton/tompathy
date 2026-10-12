import { useEffect, useId, useMemo, useRef, useState } from "react";
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
  onExpand,
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
      className={`spool ${ambiguous || !active ? "ambiguous" : ""} ${active && ended && !candidates.length ? "path-ended" : ""} ${emphasized ? "spool-emphasis" : ""} ${expanded && ambiguous ? "is-expanded" : ""}`}
      onMouseEnter={onExpand}
      onFocus={onExpand}
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
  orderUncertainGroups = [],
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
  orderUncertainGroups?: { id: string; nodes: string[]; explanation: string }[];
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
  const [hovered, setHovered] = useState<{ id: string; key?: string } | null>(
      null,
    ),
    [heldInstance, setHeldInstance] = useState<{
      id: string;
      key?: string;
    } | null>(null),
    [height, setHeight] = useState(300),
    [expanded, setExpanded] = useState(false);
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
    if (!expanded) return;
    const move = (e: PointerEvent) => {
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
    const observer = new ResizeObserver(([entry]) =>
      setHeight(Math.max(160, entry.contentRect.height)),
    );
    if (host.current) observer.observe(host.current);
    return () => observer.disconnect();
  }, [nodes.length]);
  const sourceId = goalAt(nodes, region, offset)?.id;
  const selected = graph.byId.get(
    (pinned ? (lockedNodeId ?? sourceId) : (hovered?.id ?? sourceId)) ?? "",
  );
  const inspected = expanded
    ? (graph.byId.get(hovered?.id ?? "") ?? selected)
    : selected;
  const ancestors = graph.ancestors(inspected),
    descendants = graph.descendants(inspected);
  const visible = !!selected && (sourceHover || pinned || !!hovered);
  const layout = useMemo(() => hierarchyLayout(graph, height), [graph, height]);
  const selectedKey = pinned
    ? lockedNodeId && heldInstance?.id === selected?.id
      ? heldInstance?.key
      : undefined
    : hovered?.key;
  const branch = instanceNeighborhood(
    layout,
    expanded ? (hovered?.key ?? selectedKey) : selectedKey,
  );
  const candidatesAt = (rank: number) =>
    instanceReelCandidates(graph, layout, selected, rank, selectedKey);
  const columns = Array.from({ length: graph.depth + 1 }, (_, rank) =>
    graph.all.filter((n) => n.rank === rank),
  );
  const showList = nodes.length > 120 || graph.roots.length > 4 || layout.dense;
  const canExpand =
    pinned && columns.some((_, rank) => candidatesAt(rank).ambiguous);
  const highlight = (node: GraphNode | null, key?: string) => {
    setHovered(node ? { id: node.id, key } : null);
    if (!pinned) onHighlight(node?.data ?? null);
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
      return [{ ...group, root: root.id, d }];
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
                      className={classes(t.node, t.key)}
                      aria-label={`${t.node.data.level ?? "Hierarchy"} goal: ${t.node.data.label}`}
                      aria-pressed={pinned && selected?.id === t.node.id}
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
                      <circle
                        cx={t.dotX}
                        cy={t.dotY}
                        r={t.node.parents.length ? 1.6 : 2.7}
                      />
                    </g>
                  ))}
                </g>
                {orderMarks.map((m) => (
                  <g
                    key={`${m.id}:${m.root}`}
                    className="order-uncertain"
                    tabIndex={0}
                    role="img"
                    aria-label={`Order uncertain. ${m.explanation}`}
                  >
                    <title>{`Order uncertain — ${m.explanation}`}</title>
                    <path d={m.d} className="order-hit" />
                    <path d={m.d} className="order-line" />
                  </g>
                ))}
              </svg>
            )}
          </div>
          <div
            ref={spools}
            className={`spool-area ${visible ? "is-visible" : "is-idle"}`}
            onMouseLeave={() => {
              setExpanded(false);
              setHovered(null);
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
                    onSelect={choose}
                    active={visible}
                    emphasized={
                      (expanded && selected?.rank === rank) ||
                      graph.byId.get(hovered?.id ?? "")?.rank === rank
                    }
                    expanded={expanded && canExpand}
                    onExpand={() => {
                      if (canExpand) setExpanded(true);
                    }}
                    onInspect={(n) => {
                      const match = layout.tiles.find(
                        (t) =>
                          t.node.id === n?.id &&
                          (!branch.tile ||
                            branch.ancestors.has(t.key) ||
                            branch.descendants.has(t.key)),
                      );
                      setHovered(n ? { id: n.id, key: match?.key } : null);
                    }}
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
