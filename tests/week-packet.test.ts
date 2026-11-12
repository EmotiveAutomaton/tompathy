import assert from "node:assert/strict";
import { test } from "node:test";
import { readFileSync } from "node:fs";
import { PacketSchema } from "../src/core/model";
import { evidenceStatus, type ClaimSnapshot } from "../src/core/claims";
import { valueTable, connectedValues } from "../src/core/value-table";
import { createExample } from "../src/core/example";

test("week engine fields round trip and reject malformed timeline/density", () => {
  const raw = JSON.parse(readFileSync("engine/tests/fixtures/packets/week-preview.json", "utf8"));
  const packet = PacketSchema.parse(raw);
  assert.deepEqual(packet.attentionTimeline, raw.attentionTimeline);
  assert.deepEqual(packet.goalHierarchy, raw.goalHierarchy);
  assert.ok(packet.hypotheses.some(h => h.finding));
  for (const change of [(p: typeof raw) => p.attentionTimeline[0].node = "missing", (p: typeof raw) => p.attentionTimeline[0].invented = true,
    (p: typeof raw) => p.attentionTimeline[0].located = !p.attentionTimeline[0].located,
    (p: typeof raw) => p.goalHierarchy.nodes.at(-1).attentionDensity = 0]) {
    const broken = structuredClone(raw); change(broken);
    assert.equal(PacketSchema.safeParse(broken).success, false);
  }
});

test("field status resolves against current rows, definition and reader, never sentence or habit", () => {
  const packet = PacketSchema.parse(JSON.parse(readFileSync("engine/tests/fixtures/packets/week-preview.json", "utf8")));
  const row = { ledgerId: "fixture", wording: "Scoped software fixture", controlStatus: "passes", source: "fixture:only" };
  const claims: ClaimSnapshot = { rows: [{ ...row, fieldEligible: true, supersededBy: null, definition: packet.preview!.departureDefinition!, reader: packet.preview!.readers[0] }] };
  const item = { kind: "attention" as const, finding: "departure-phrase" as const, evidenceStatus: "field-tested" as const, ledgerRows: [row] };
  assert.equal(evidenceStatus(item, packet.preview, claims), "field-tested");
  assert.equal(evidenceStatus({...item, finding: "departure-sentence"}, packet.preview, claims), "unvalidated");
  assert.equal(evidenceStatus({...item, kind: "value"}, packet.preview, claims), "unvalidated");
  assert.equal(evidenceStatus({...item, kind: undefined}, packet.preview, claims), "unvalidated");
  assert.equal(evidenceStatus({...item, finding: undefined}, packet.preview, claims), "unvalidated");
  assert.equal(evidenceStatus(item, {...packet.preview!, departureDefinition: "new"}, claims), "unvalidated");
  claims.rows[0].supersededBy = "withdrawn";
  assert.equal(evidenceStatus(item, packet.preview, claims), "unvalidated");
  assert.equal(evidenceStatus(item, packet.preview), "unvalidated");
});

test("table preserves multiple parents and ranks every parent above its child", async () => {
  const packet = await createExample();
  const nodes = packet.goalHierarchy!.nodes;
  const table = valueTable(packet, nodes, packet.hypotheses.filter(h => h.kind === "value"));
  const rank = new Map(table.rows.flatMap((row, i) => row.map(c => [c.id, i] as const)));
  for (const edge of table.edges) assert.ok(rank.get(edge.to)! < rank.get(edge.from)!);
  for (const node of nodes) for (const parent of node.parentIds ?? (node.parentId ? [node.parentId] : [])) {
    assert.ok(table.edges.some(e => e.from === `goal:${node.id}` && e.to === `goal:${parent}`));
    assert.ok(connectedValues(table, `goal:${node.id}`).has(`goal:${parent}`));
  }
  assert.equal(new Set(table.rows.flat().map(c => c.id)).size, table.rows.flat().length);
  const live = structuredClone(packet); live.provider.id = "fixture-live"; live.origin = "imported";
  assert.ok(valueTable(live, nodes, []).edges.every(e => e.weight === undefined && !e.illustrative));
});
