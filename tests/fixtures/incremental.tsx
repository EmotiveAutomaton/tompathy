import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import { ProcessHierarchy } from "../../src/components/ProcessHierarchy";
import { ReadingProgress } from "../../src/components/ReadingProgress";
import { ValueTabs } from "../../src/components/ValueTabs";
import { MoreHorizontal } from "lucide-react";
import type { Packet } from "../../src/core/model";
import type { GoalNode } from "../../src/core/hierarchy";
import "../../src/styles.css";
import "../../src/reader.css";
import "../../src/mind.css";

const groups = Array.from({ length: 12 }, (_, i) => [`p${i}`]);
const nodes: GoalNode[] = groups.map((regions, i) => ({ id: `goal-${i}`, maker: "fixture", label: `Constructed goal ${i + 1}`, description: "Software fixture, not inferred from a writer", regions, evidence: [], level: "paragraph", evidenceStatus: "unvalidated", basis: "model-judgment" }));
function Fixture() {
  const [count, setCount] = useState(0), [complete, setComplete] = useState(false), [paused, setPaused] = useState(false);
  const [selected, setSelected] = useState<GoalNode | null>(null);
  const status = complete ? "complete" : paused ? "skipped" : "running";
  const packet = { preview: { modules: ["deviation", "goals"].map(id => ({ id, title: id, status, completed: count, total: 12, detail: "Constructed progress verification" })), resumable: paused } } as unknown as Packet;
  return <div className="reader" style={{ width: "min(100vw, 420px)", height: 720, margin: "auto", padding: 12, boxSizing: "border-box" }}>
    <p>Constructed UI check</p>
    <button onClick={() => setCount(n => Math.min(12, n + 1))}>Advance</button>
    <button onClick={() => { setCount(12); setComplete(true); }}>Finish</button>
    <button onClick={() => setPaused(true)}>Pause</button>
    <section className="region process-region" style={{ height: 460, position: "relative" }}>
      <ProcessHierarchy nodes={nodes.slice(0, count)} previewGroups={groups} region="p0" offset={0} sourceHover={false} pinned={!!selected} lockedNodeId={selected?.id} onSelect={setSelected} onHighlight={() => {}} onLock={() => setSelected(null)} onFind={() => {}} />
    </section>
    <div className="values-bottom" style={{ width: "100%" }}><ValueTabs tab="work" onTab={() => {}} /><div className="reading-tools"><ReadingProgress packet={packet} active={!paused && !complete} phase="Reading" context={null} capturing={false} onContinue={() => setPaused(false)} /><button className="icon-button" aria-label="Reader menu"><MoreHorizontal size={18} /></button></div></div>
  </div>;
}
createRoot(document.getElementById("root")!).render(<Fixture />);
