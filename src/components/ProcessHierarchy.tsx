import { useMemo, useState } from "react";
import { LockKeyhole, LockKeyholeOpen } from "lucide-react";
import { goalAt, goalTree, type GoalNode } from "../core/hierarchy";
import type { HierarchyNode } from "d3-hierarchy";

export function ProcessHierarchy({
  nodes,
  region,
  offset,
  sourceHover,
  pinned,
  onHighlight,
  onLock,
  list = false,
}: {
  nodes: GoalNode[];
  region: string;
  offset: number;
  sourceHover: boolean;
  pinned: boolean;
  onHighlight: (node: GoalNode | null) => void;
  onLock: () => void;
  list?: boolean;
}) {
  const tree = useMemo(() => goalTree(nodes), [nodes]);
  const [hovered, setHovered] = useState<string | null>(null);
  const [exploring, setExploring] = useState(false);
  const all = tree?.descendants() ?? [],
    depth = tree?.height ?? 0;
  const selected = all.find(
    (n) => n.id === (hovered ?? goalAt(nodes, region, offset)?.id),
  );
  const ancestors = new Set(selected?.ancestors().map((n) => n.id));
  const descendants = new Set(selected?.descendants().map((n) => n.id));
  const reading = (sourceHover || pinned) && !hovered && !exploring;
  const columns = Array.from({ length: depth + 1 }, (_, d) =>
    all.filter((n) => n.depth === depth - d),
  );
  const showList = list || nodes.length > 120 || depth > 5;
  const highlight = (node: HierarchyNode<GoalNode> | null) => {
    setHovered(node?.data.id ?? null);
    onHighlight(node?.data ?? null);
  };
  return (
    <div
      className={`goal-process ${reading ? "reading-spools" : "overview"}`}
      data-testid="process"
      onMouseEnter={() => setExploring(true)}
      onFocus={() => setExploring(true)}
      onMouseLeave={() => {
        setExploring(false);
        highlight(null);
      }}
    >
      {!nodes.length ? (
        <span className="quiet-empty">No goal hierarchy supplied</span>
      ) : (
        <>
          <div
            className={`pyramid ${showList ? "pyramid-list" : ""}`}
            aria-label="Goal hierarchy, sentences on the left, purpose on the right"
            onBlur={(e) => {
              if (!e.currentTarget.contains(e.relatedTarget)) highlight(null);
            }}
          >
            {columns.map((column, c) => (
              <div
                className="pyramid-column"
                key={c}
                style={{ height: `${100 - c * (72 / Math.max(1, depth))}%` }}
              >
                {column.map((n) => (
                  <button
                    key={n.id}
                    data-node={n.id}
                    aria-label={`${n.data.level} goal: ${n.data.label}`}
                    className={`pyramid-node ${hovered && ancestors.has(n.id) ? "ancestor" : ""} ${hovered && descendants.has(n.id) ? "descendant" : ""} ${hovered === n.id ? "chosen" : ""}`}
                    onMouseEnter={() => highlight(n)}
                    onFocus={() => highlight(n)}
                    onClick={() => highlight(n)}
                  >
                    {showList ? n.data.label : <span aria-hidden="true" />}
                  </button>
                ))}
              </div>
            ))}
          </div>
          <div
            className={`spool-area ${reading || hovered ? "is-visible" : ""}`}
            aria-hidden={!reading && !hovered}
          >
            {hovered && selected && (
              <div className="node-explanation" role="status">
                <strong>{selected.data.label}</strong>
                <p>{selected.data.description}</p>
              </div>
            )}
            <div
              className="odometer"
              aria-label="Selected goal path"
              data-testid="odometer"
            >
              {columns.map((column, c) => {
                const exact = column.find((n) => ancestors.has(n.id));
                const candidates = column.filter((n) => descendants.has(n.id));
                const choice = exact ?? candidates[0];
                const ambiguous = !exact && candidates.length > 1;
                const index = Math.max(
                  0,
                  column.findIndex((n) => n.id === choice?.id),
                );
                return (
                  <div
                    key={c}
                    className={`spool ${ambiguous ? "ambiguous" : ""}`}
                    data-level={depth - c}
                    data-selected={exact?.id ?? ""}
                    aria-label={
                      ambiguous
                        ? `${candidates.length} possible subordinate goals; none selected`
                        : (choice?.data.label ?? "No goal at this level")
                    }
                  >
                    <div className="spool-window">
                      <div
                        className="spool-strip"
                        style={{ transform: `translateY(${-index * 112}px)` }}
                      >
                        {(choice ? column : []).map((n) => (
                          <div
                            key={n.id}
                            className="spool-item"
                            aria-hidden="true"
                          >
                            <span>{n.data.label}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <small>
                      {ambiguous
                        ? `${candidates.length} possibilities`
                        : (choice?.data.level ?? "Unspecified")}
                    </small>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
      {nodes.length > 0 && (
        <button
          className={`process-lock ${pinned ? "is-locked" : ""}`}
          aria-label={pinned ? "Unlock sentence" : "Lock sentence"}
          aria-pressed={pinned}
          title={
            pinned
              ? "Unlock sentence · Escape"
              : "Lock this sentence · double-click page text"
          }
          onClick={onLock}
        >
          {pinned ? <LockKeyhole size={15} /> : <LockKeyholeOpen size={15} />}
        </button>
      )}
    </div>
  );
}
