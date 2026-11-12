import snapshot from "../../docs/claims/SNAPSHOT.json";
import type { Hypothesis, Packet } from "./model";

export type ClaimSnapshot = { rows: { ledgerId: string; wording: string; controlStatus: string; source: string; fieldEligible: boolean; supersededBy: string | null; definition?: string | null; reader: {id: string; revision: string; sha256: string; backend: string} | null }[] };
export function evidenceStatus(item: Pick<Hypothesis, "evidenceStatus" | "ledgerRows" | "finding"> & Partial<Pick<Hypothesis, "kind">>, preview?: Packet["preview"], claims: ClaimSnapshot = snapshot) {
  if (item.evidenceStatus !== "field-tested") return item.evidenceStatus;
  const valid = (item.kind === "attention" || item.kind === "process") && item.finding === "departure-phrase" && item.ledgerRows?.length && item.ledgerRows.every(saved => {
    const row = claims.rows.find(r => r.ledgerId === saved.ledgerId);
    return row?.fieldEligible && row.controlStatus === "passes" && !row.supersededBy && row.reader &&
      row.wording === saved.wording && row.controlStatus === saved.controlStatus && row.source === saved.source &&
      row.definition === preview?.departureDefinition && preview?.readers.some(r =>
        r.id === row.reader!.id && r.revision === row.reader!.revision && r.sha256 === row.reader!.sha256 && r.backend === row.reader!.backend);
  });
  return valid ? "field-tested" : "unvalidated";
}
export function currentFindings(findings: NonNullable<Packet["globalFindings"]>) {
  return findings.map(f => (snapshot.globalFindings.find(row => row.source === f.source) ?? f) as typeof f);
}
