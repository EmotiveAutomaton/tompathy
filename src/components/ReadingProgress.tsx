import { Check, CircleAlert, Pause } from "lucide-react";
import { useEffect, useState, type CSSProperties } from "react";
import type { Packet } from "../core/model";
import type { ContextWork } from "./ContextProgress";

type Work = { id: string; label: string; status: string; completed?: number | null; total?: number | null; detail: string };
const names: Record<string, string> = { habits: "Text", deviation: "Attention", agreement: "Readers", techniques: "Techniques", goals: "Goals", payoff: "Payoff", corrections: "Edits" };

function Indicator({ work }: { work: Work }) {
  const [hidden, setHidden] = useState(false);
  useEffect(() => {
    setHidden(false);
    if (work.status !== "complete") return;
    const timer = window.setTimeout(() => setHidden(true), 2600);
    return () => window.clearTimeout(timer);
  }, [work.status]);
  if (hidden) return null;
  const done = work.status === "complete", failed = work.status === "failed", paused = work.status === "skipped";
  const known = work.total != null && work.total > 0 && work.completed != null;
  const fraction = done ? 1 : known ? Math.min(.995, work.completed! / work.total!) : 0;
  const detail = `${work.label}: ${done ? "complete" : paused ? "paused" : failed ? "failed" : known ? `${work.completed} of ${work.total}` : "working"}. ${work.detail}`;
  return <span className={`reading-progress-item ${done ? "is-complete" : ""} ${failed ? "is-failed" : ""}`} role="status" aria-label={detail} title={detail}>
    <span>{work.label}</span>
    {done ? <Check size={13} className="reading-progress-check" /> : failed ? <CircleAlert size={13} /> : paused ? <Pause size={12} /> :
      <span className={`reading-progress-pie ${known ? "" : "is-indeterminate"}`} style={{ "--progress": `${fraction * 360}deg` } as CSSProperties}
        role="progressbar" aria-label={work.label} aria-valuemin={known ? 0 : undefined} aria-valuemax={known ? work.total! : undefined} aria-valuenow={known ? work.completed! : undefined} />}
  </span>;
}

export function ReadingProgress({ packet, active, phase, context, capturing, onContinue }: {
  packet: Packet | null; active: boolean; phase: string; context: ContextWork | null; capturing: boolean; onContinue: () => void;
}) {
  const work: Work[] = (packet?.preview?.modules ?? [])
    .filter(m => m.status !== "pending" && m.status !== "unavailable")
    .map(m => ({ ...m, label: names[m.id] ?? m.title }));
  if (active && !work.some(m => m.status === "running")) work.unshift({ id: "analysis", label: "Reading", status: "running", detail: phase });
  if (capturing) work.unshift({ id: "capture", label: "Capture", status: "running", detail: "Reading the current page" });
  if (context) work.push({ id: "context", label: "Context", status: context.phase === "done" ? "complete" : context.phase === "error" ? "failed" : "running", completed: context.completed, total: context.total, detail: context.label });
  // A cancelled request is paused, not a successful completion.
  if (!active) for (const item of work) if (item.status === "running" && !["context", "capture"].includes(item.id)) item.status = "skipped";
  return <div className="reading-progress" aria-label="Reading progress">
    {work.map(item => <Indicator key={item.id} work={item} />)}
    {!active && packet?.preview?.resumable && <button type="button" className="reading-continue" onClick={onContinue}>Continue reading</button>}
  </div>;
}
