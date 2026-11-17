import { useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from "react";
import type { ContextItem, Hypothesis, Packet } from "../core/model";
import type { GoalNode } from "../core/hierarchy";
import { authorNeedSources, bodyChannels, needs, pageNeedActivity, workNeedSources, type NeedDetailId, type NeedId, type NeedSource } from "../core/need-view";
import type { ValuesTab } from "./ValueTabs";

export const needDescriptions: Record<NeedDetailId, string> = {
  N1: "Knowledge concerns having a useful understanding of the situation and the possibilities within it.",
  N2: "Nest concerns a workable, dependable surrounding in which to act and return.",
  N3: "Belonging concerns connection and a place among others.",
  N4: "Visibly respectable concerns being seen as someone worthy of respect.",
  N5: "Visibly compassionate concerns being seen as responsive to the needs of others.",
  N6: "The body includes needs such as food, warmth and sleep. These are distinct from the emotional channels.",
  heat: "Heat concerns the body's thermal needs and a workable temperature.",
  food: "Food concerns nourishment and the body's energy needs.",
  sleep: "Sleep concerns rest and recovery.",
  S1: "Stress brings the need diagrams together in this view. The connecting lines do not calculate a person's stress from a text.",
};

export function NeedGraph({ large = false, stress = false }: { large?: boolean; stress?: boolean }) {
  const id = `band-${useId().replace(/:/g, "")}`;
  return <svg className={`need-graph ${large ? "large" : ""}`} viewBox="0 0 210 38" preserveAspectRatio="none" aria-label="Notional fluctuation band, not a measured need" role="img">
    <defs>
      <linearGradient id={id}><stop stopColor="currentColor" stopOpacity="0" /><stop offset=".18" stopColor="currentColor" stopOpacity=".1" /><stop offset=".76" stopColor="currentColor" stopOpacity=".1" /><stop offset="1" stopColor="currentColor" stopOpacity=".02" /></linearGradient>
      <linearGradient id={`${id}-line`}><stop stopColor="currentColor" stopOpacity="0" /><stop offset=".17" stopColor="currentColor" /><stop offset="1" stopColor="currentColor" /></linearGradient>
      <linearGradient id={`${id}-tail`} x1="182" x2="210" gradientUnits="userSpaceOnUse"><stop stopColor="currentColor" stopOpacity=".45" /><stop offset=".5" stopColor="currentColor" stopOpacity=".18" /><stop offset="1" stopColor="currentColor" stopOpacity="0" /></linearGradient>
    </defs>
    <path className="need-band" fill={`url(#${id})`} d="M0 2 C12 4 18 12 34 12 C70 9 106 16 146 12 C161 11 168 18 182 19 C168 20 161 27 146 28 C106 32 70 25 34 28 C18 28 12 34 0 36 Z" />
    <path className="need-trace" stroke={`url(#${id}-line)`} d="M0 24 C16 24 24 7 38 8 S58 36 73 30 S96 12 108 18 S132 30 145 19 S162 8 170 15 Q176 19 182 19" />
    {stress && <path className="need-pigtail" stroke={`url(#${id}-tail)`} d="M182 19 C193 19 197 31 205 29 C215 27 209 12 202 17 C196 22 203 26 208 23" />}
  </svg>;
}

// The same inward-curving shoulder as the terminal lobes in Expertise.
const tipEdge = Array.from({ length: 25 }, (_, i) => {
  const t = i / 24;
  return { x: 198 * t, half: 1.5 + 28.5 * (1 - t) ** 2.4 * (1 + 2.4 * t) };
});
const tipPath = `M${tipEdge.map(p => `${p.x},${32 - p.half}`).join(" L")} Q201 32 198 33.5 L${[...tipEdge].reverse().map(p => `${p.x},${32 + p.half}`).join(" L")}`;

export function NeedLandscape({ packet, nodes, values, tab, context, onSources, inspect, onNeed, onHighlight, research = false }: {
  packet: Packet; nodes: GoalNode[]; values: Hypothesis[]; tab: ValuesTab; context: ContextItem[];
  onSources: () => void; inspect: (h: Hypothesis) => void; onNeed: (id: NeedDetailId) => void;
  onHighlight: (sources: NeedSource[]) => void;
  research?: boolean;
}) {
  // Parent demo adapters recreate records. Depend on their contents to avoid
  // re-centering the author timeline and clearing hover on every parent render.
  const valueKey = JSON.stringify(values);
  const work = useMemo(() => workNeedSources(packet, nodes, values, research), [packet, nodes, valueKey, research]);
  const activity = research && tab === "work" ? pageNeedActivity(packet) : null;
  const sources = useMemo(() => tab === "creator" ? authorNeedSources(packet, context, work) : work, [tab, packet, context, work]);
  const [active, setActive] = useState<string | null>(null);
  const [links, setLinks] = useState<{ key: string; from: string; need: NeedId; x: number; y: number; tx: number; ty: number; direction: number }[]>([]);
  const [returns, setReturns] = useState<{ id: string; path: string }[]>([]);
  const [size, setSize] = useState({ width: 400, height: 300 });
  const host = useRef<HTMLDivElement>(null), scroll = useRef<HTMLDivElement>(null);
  const callback = useRef(onHighlight); callback.current = onHighlight;
  const marker = `need-${useId().replace(/:/g, "")}`;
  const connected = sources.filter(s => s.id === active || s.needs.some(n => n.id === active));
  const selectedNeeds = new Set(connected.flatMap(s => s.needs.map(n => n.id)));
  useEffect(() => { callback.current(active ? sources.filter(s => s.id === active || s.needs.some(n => n.id === active)) : []);
    return () => callback.current([]); }, [active, sources]);
  useLayoutEffect(() => {
    const root = host.current!, scroller = scroll.current!;
    let frame = 0;
    function measure() {
      const bounds = root.getBoundingClientRect(), viewport = scroller.getBoundingClientRect();
      setSize({ width: bounds.width, height: bounds.height });
      const result: typeof links = [];
      for (const source of sources) {
        const el = Array.from(scroller.querySelectorAll<HTMLElement>("[data-source]")).find(e => e.dataset.source === source.id);
        if (!el) continue;
        const rect = el.getBoundingClientRect(), y = rect.top + rect.height / 2;
        if (y < viewport.top || y > viewport.bottom) continue;
        for (const need of source.needs) {
          const target = root.querySelector(`[data-need="${need.id}"] .need-graph`)?.getBoundingClientRect();
          const incoming = sources.filter(s => s.needs.some(n => n.id === need.id));
          const slot = incoming.indexOf(source), fraction = (slot + 1) / (incoming.length + 1);
          if (target) result.push({ key: `${source.id}:${need.id}`, from: source.id, need: need.id,
            x: rect.right - bounds.left - 4, y: y - bounds.top,
            tx: target.left - bounds.left + target.width * (.35 + .4 * fraction),
            ty: target.top - bounds.top + target.height * (.28 + .35 * fraction) - need.direction * 3,
            direction: need.direction });
        }
      }
      setLinks(result);
      const stress = root.querySelector('[data-need="S1"] .need-graph')?.getBoundingClientRect();
      if (stress) {
        const sx = stress.left - bounds.left + stress.width * .16, sy = stress.top - bounds.top + stress.height * .5;
        const rail = stress.right - bounds.left - 2;
        const outlets = Array.from(root.querySelectorAll<HTMLElement>('[data-outlet]')).map(el => {
          const rect = el.querySelector('.need-graph')!.getBoundingClientRect();
          const x = rect.left - bounds.left + rect.width * 182 / 210, y = rect.top - bounds.top + rect.height / 2;
          return { id: el.dataset.outlet!, y, path: `M${x} ${y} C${rail} ${y} ${rail} ${y + 8} ${rail} ${y + 15}` };
        });
        setReturns([...outlets, { id: "all", path: `M${rail} ${Math.min(...outlets.map(o => o.y)) + 15} V${sy - 19} Q${rail} ${sy - 10} ${rail - 12} ${sy - 10} H${sx + 14} Q${sx} ${sy - 10} ${sx} ${sy}` }]);
      }
    }
    const queue = () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(measure); };
    const observer = new ResizeObserver(queue); observer.observe(root); observer.observe(scroller);
    scroller.addEventListener("scroll", queue, { passive: true });
    const current = scroller.querySelector<HTMLElement>('[data-current="true"]');
    if (current) scroller.scrollTop = current.offsetTop - scroller.clientHeight / 2 + current.offsetHeight / 2;
    measure();
    return () => { cancelAnimationFrame(frame); observer.disconnect(); scroller.removeEventListener("scroll", queue); };
  }, [sources]);
  return <div className="need-landscape" data-testid="needs-landscape" data-perspective={tab}>
    {tab === "creator" && <button className="need-sources-control" onClick={onSources}>Sources</button>}
    <div className="need-scene" ref={host}>
      <div className={`need-sources ${tab === "creator" ? "author-actions" : ""}`} ref={scroll} role="region" aria-label={tab === "creator" ? "Author actions around the current artifact" : "Top-level fluencies and channels"}>
        {sources.length === 0 && <p className="need-empty">No top-level readings supplied.</p>}
        {sources.map(source => <button key={source.id} data-source={source.id} data-current={source.current || undefined}
          className={`need-source ${source.type} ${active === source.id || connected.includes(source) ? "connected" : ""}`}
          onMouseEnter={() => setActive(source.id)} onMouseLeave={() => setActive(null)}
          onFocus={() => setActive(source.id)} onBlur={() => setActive(null)}
          onClick={() => source.hypothesis ? inspect(source.hypothesis) : tab === "creator" && !source.current ? onSources() : setActive(source.id)}
          title={`${source.label}. ${source.confidence === null ? "Reliability not supplied." : "Opacity and weight reflect supplied support, not calibrated confidence."}`}
          style={{ fontWeight: source.confidence === null ? 400 : 350 + 350 * source.confidence }}>
          <svg className="need-drop" viewBox="0 0 200 64" preserveAspectRatio="none" aria-hidden="true" style={{ opacity: source.confidence === null ? .14 : .08 + .28 * source.confidence }}>
            <path d={source.type === "action" ? "M5 32 C5 4 65 0 107 14 C146 28 171 32 198 32 C171 32 146 36 107 50 C65 64 5 60 5 32Z" : tipPath} />
          </svg>
          <span style={{ opacity: source.confidence === null ? .78 : .5 + .5 * source.confidence }}>{source.label}</span>
          {source.type === "action" && <small>{source.current ? "Current artifact" : source.date}</small>}
        </button>)}
      </div>
      <div className="need-targets" aria-label="Five needs, bodily needs and stress">
        {needs.map((need, i) => <div key={need.id} className={i === 5 ? "body-channels" : ""}><button data-need={need.id} data-outlet={need.id} aria-label={need.label}
          className={`need-target ${i === 5 ? "body-need" : ""} ${active === need.id || selectedNeeds.has(need.id) ? "connected" : ""}`}
          onMouseEnter={() => setActive(need.id)} onMouseLeave={() => setActive(null)}
          onFocus={() => setActive(need.id)} onBlur={() => setActive(null)} onClick={() => onNeed(need.id)}>
          <span>{need.label}{activity?.[need.id]?.length ? ` · ${activity[need.id].length}` : ""}</span><NeedGraph /></button>
          {i === 5 && <div className="body-subchannels">{bodyChannels.map(channel => <button key={channel.id} data-outlet={channel.id} className="body-subchannel" aria-label={channel.label}
            onMouseEnter={() => setActive("N6")} onMouseLeave={() => setActive(null)} onFocus={() => setActive("N6")} onBlur={() => setActive(null)} onClick={() => onNeed(channel.id)}>
            <NeedGraph /><span>{channel.label}</span></button>)}</div>}
          </div>)}
        <button className={`need-target stress-need ${active === "S1" ? "connected" : ""}`} data-need="S1" aria-label="Stress"
          onMouseEnter={() => setActive("S1")} onMouseLeave={() => setActive(null)} onFocus={() => setActive("S1")} onBlur={() => setActive(null)} onClick={() => onNeed("S1")}>
          <span>Stress</span><NeedGraph stress /></button>
      </div>
      <svg className="need-returns" width={size.width} height={size.height} aria-hidden="true">
        {returns.map(r => <path key={r.id} d={r.path} className={active === "S1" || active === r.id ? "lit" : ""} />)}
      </svg>
      <svg className="need-connections" width={size.width} height={size.height} aria-hidden="true">
        <defs><marker id={marker} viewBox="0 0 8 8" refX="7" refY="4" markerWidth="5" markerHeight="5" orient="auto"><path d="M1 1 L7 4 L1 7" /></marker></defs>
        {links.map(l => { const lit = active === l.from || active === l.need;
          return <g key={l.key} data-from={l.from} data-to={l.need} className={lit ? "lit" : ""}>
            <path d={`M${l.x} ${l.y} C${l.x + 48} ${l.y} ${l.tx - 70} ${l.ty + 25 * l.direction} ${l.tx - 16} ${l.ty + 5 * l.direction}`} />
            <path className="need-vector" markerEnd={`url(#${marker})`} d={`M${l.tx - 16} ${l.ty + 5 * l.direction} Q${l.tx - 8} ${l.ty + 4 * l.direction} ${l.tx} ${l.ty}`} />
          </g>; })}
      </svg>
    </div>
  </div>;
}
