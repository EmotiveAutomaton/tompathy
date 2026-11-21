import type { PageReading } from "./bottom-box";
import filed from "./worry-lift-decision.json";

type Decision = { pack: string | null; sourceReceiptPin: string | null };

/** null keeps the level view; an empty selection hides the study's reading on this page. */
export function worryLift(reading: PageReading, decision: Decision = filed) {
  if (reading.id !== "S1" || reading.status !== "research" || reading.pack !== decision.pack ||
      !decision.sourceReceiptPin || !/^[a-f0-9]{64}$/.test(decision.sourceReceiptPin)) return null;
  const values = reading.series.map(s => s.value).sort((a, b) => a - b);
  if (!values.length) return [];
  const mid = Math.floor(values.length / 2);
  const median = values.length % 2 ? values[mid] : (values[mid - 1] + values[mid]) / 2;
  return reading.series.map(s => ({ from: s.from, to: s.to, lift: 8 * (s.value - median) }))
    .filter(s => s.lift >= 1);
}
