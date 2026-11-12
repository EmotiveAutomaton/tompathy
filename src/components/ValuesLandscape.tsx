import { useMemo, useRef, useState } from "react";
import type { ContextItem, Hypothesis, Packet } from "../core/model";
import type { GoalNode, HierarchyLayout } from "../core/hierarchy";
import { valueTable, connectedValues } from "../core/value-table";
import type { ValuesTab } from "./ValueTabs";
import { confidenceWeight, supportText } from "./GoalCloud";

/** The table shares the supplied hierarchy, not the Expertise viewport geometry. */
export function ValuesLandscape({ packet, nodes, values, tab, context, onSources, inspect }: {
  packet: Packet; nodes: GoalNode[]; sourceLayout?: HierarchyLayout | null;
  values: Hypothesis[]; tab: ValuesTab; context: ContextItem[];
  onSources: () => void; inspect: (value: Hypothesis) => void;
}) {
  const illustration = packet.provider.id === "tompathy-example" && packet.origin === "synthetic example";
  const unavailable = !illustration && tab !== "work" && !values.length;
  const table = useMemo(() => valueTable(packet, unavailable ? [] : nodes, values), [packet, nodes, values, unavailable]);
  const [active, setActive] = useState<string>();
  const [held, setHeld] = useState<string>();
  const [entry, setEntry] = useState<string>();
  const host = useRef<HTMLDivElement>(null);
  const selected = active ?? held;
  const related = useMemo(() => connectedValues(table, selected), [table, selected]);
  const cells = table.rows.flat();
  const entryId = cells.some(c => c.id === entry) ? entry : cells[0]?.id;
  const width = Math.max(352, ...table.rows.map(r => r.length * 126 + 24));
  const height = Math.max(170, table.rows.length * 76 + 16);
  const positions = new Map(table.rows.flatMap((row, y) => row.map((cell, x) => [cell.id, { x: 12 + x * 126, y: 8 + y * 76 }] as const)));
  const history = packet.valueView?.evidenceTier === "production" || packet.process.interpretation === "historical-production";
  const missing = packet.valueView ? packet.valueView.firstMissingLink : history
    ? "No admitted comparison fit with conditional covariance."
    : "Final text only — no recorded choices or revisions.";
  function focus(id: string | undefined) {
    if (!id) return;
    setEntry(id);
    const button = Array.from(host.current?.querySelectorAll<HTMLButtonElement>("button[data-cell]") ?? []).find(b => b.dataset.cell === id);
    button?.focus({ preventScroll: true });
    button?.scrollIntoView({ block: "nearest", inline: "nearest" });
  }
  return <div className="values-landscape" data-perspective={tab} data-illustration={illustration}>
    <div className="landscape-meta">
      <span>{illustration ? "Illustration (authored)" : history ? "Production history" : "Final text only"}</span>
      {tab !== "work" && <button onClick={onSources}>Sources{context.length ? ` · ${context.length}` : ""}</button>}
      {held && <button onClick={() => { setHeld(undefined); setActive(undefined); }} aria-label="Release core values selection">Release</button>}
    </div>
    {cells.length ? <div className="values-table-scroll" ref={host} role="region" aria-label="Scrollable core values hierarchy">
      <div className="values-table" role="table" aria-label="Core values hierarchy" style={{ width, height }} data-testid="values">
        <svg className="values-table-links" width={width} height={height} aria-hidden="true">
          {table.edges.filter(e => related.has(e.from) && related.has(e.to)).map(edge => {
            const a = positions.get(edge.from)!, b = positions.get(edge.to)!;
            const x1 = a.x + 54, y1 = a.y, x2 = b.x + 54, y2 = b.y + 36;
            return <path key={`${edge.from}:${edge.to}`} data-from={edge.from} data-to={edge.to}
              d={`M${x1} ${y1} C${x1} ${(y1 + y2) / 2} ${x2} ${(y1 + y2) / 2} ${x2} ${y2}`}
              strokeWidth={edge.weight == null ? 1 : .7 + 2.3 * edge.weight}
              className={edge.illustrative ? "illustrative" : ""} />;
          })}
        </svg>
        {table.rows.map((row, y) => <div role="row" className="values-table-row" key={y} style={{ top: 8 + y * 76 }}>
          {row.map(cell => <div role="cell" key={cell.id} className={`values-table-cell ${related.has(cell.id) ? "related" : ""}`}>
              <button className="core-value-row" data-cell={cell.id} tabIndex={cell.id === entryId ? 0 : -1}
                title={`${cell.label}\n${cell.value ? supportText(cell.value) + ". Click or press Enter for the full diagram." : cell.node!.description}`}
                aria-label={`${cell.value?.valueCategory === "drive" ? "Drive " : ""}${cell.label}`}
                aria-pressed={held === cell.id} style={{ fontWeight: cell.value ? confidenceWeight(cell.value) : cell.confidence ? confidenceWeight(cell.confidence) : 400 }}
                onMouseEnter={() => setActive(cell.id)} onMouseLeave={() => setActive(undefined)}
                onFocus={() => { setEntry(cell.id); setActive(cell.id); }} onBlur={() => setActive(undefined)}
                onClick={() => { setHeld(held === cell.id ? undefined : cell.id); if (cell.value) inspect(cell.value); }}
                onKeyDown={event => {
                  const x = row.indexOf(cell);
                  let target: string | undefined;
                  if (event.key === "ArrowRight") target = row[x + 1]?.id;
                  if (event.key === "ArrowLeft") target = row[x - 1]?.id;
                  if (event.key === "ArrowUp") target = table.edges.find(e => e.from === cell.id)?.to ?? table.rows[y - 1]?.[Math.min(x, table.rows[y - 1].length - 1)]?.id;
                  if (event.key === "ArrowDown") target = table.edges.find(e => e.to === cell.id)?.from ?? table.rows[y + 1]?.[Math.min(x, table.rows[y + 1].length - 1)]?.id;
                  if (event.key === "Home") target = event.ctrlKey ? cells[0]?.id : row[0]?.id;
                  if (event.key === "End") target = event.ctrlKey ? cells.at(-1)?.id : row.at(-1)?.id;
                  if (event.key === "Escape") { setHeld(undefined); setActive(undefined); }
                  if (target) { event.preventDefault(); focus(target); }
                }}><span>{cell.shortLabel}</span></button>
          </div>)}
        </div>)}
      </div>
    </div> : <div className="landscape-unavailable"><p>{unavailable ? tab === "global" ? "No admitted population model." : "Author view awaits in-scope works and admitted readings." : "No values supplied"}</p>
      {tab === "creator" && <button onClick={onSources}>View context timeline</button>}
    </div>}
    <p className="landscape-inspection" aria-live="polite">{selected ? cells.find(c => c.id === selected)?.label : illustration ? "Broader goals above · boldness: confidence · line width: illustrative weight" : missing ?? "Boldness: supplied confidence · line width: supplied connection weight"}</p>
  </div>;
}
