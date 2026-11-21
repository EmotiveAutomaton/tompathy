import assert from "node:assert/strict";
import { test } from "node:test";
import { BottomBoxSchema, PageReadingSchema, upgradeBottomBoxPacket } from "../src/core/bottom-box";
import { pageNeedSources, pageNeedActivity, pageStress, workNeedSources } from "../src/core/need-view";
import { createExample } from "../src/core/example";
import { sentences } from "../src/core/sentences";
import { worryLift } from "../src/core/worry-lift";

test("worry lift is pack-bound and includes a difference of exactly one original point", () => {
  const r = reading("S1", [], [.25, .5, .625, .5, .5].map((value, i) => ({ from: i*5, to: i*5+8, value })));
  const pass = { pack: r.pack, sourceReceiptPin: "c".repeat(64) };
  assert.deepEqual(worryLift(r, pass), [{ from: 10, to: 18, lift: 1 }]);
  assert.deepEqual(worryLift({ ...r, series: r.series.slice(-1) }, pass), []);
  assert.equal(worryLift(r, { ...pass, pack: "another" }), null);
  assert.equal(worryLift(r, { ...pass, sourceReceiptPin: null }), null);
});

const mapping = { status: "proposed", source: "constructed answer" } as const;
const event = (span: [number, number], confidence: number, direction: string) => ({
  span, confidence, label: "fear", who: "unclear", words: [],
  stake: { need: "N2", direction, by: "other", when: "ahead", mapping },
});
const reading = (id: string | null, events: unknown[], series: unknown[] = []) => PageReadingSchema.parse({
  id, tier: "on_page", share: null, events, series, pack: `constructed@${"a".repeat(64)}`,
  key: { corpus: "constructed", labelled_by: "test author", n: 3 },
  score: { metric: "constructed", value: 1, interval: null },
  people: {}, floor: {}, nothing_here: {}, mapping, status: "research",
});

test("TS3 UTF-16 fixture agrees with engine spans, including non-BMP characters", () => {
  assert.deepEqual(sentences("Fear 😟. Joy. Plain."), [
    { text: "Fear 😟.", start: 0, end: 8 }, { text: "Joy.", start: 9, end: 13 }, { text: "Plain.", start: 14, end: 20 },
  ]);
});

test("TS3 channel stakes map by overlap, hide N5, retain activity without inventing levels", async () => {
  const packet = await createExample();
  packet.provider.id = "constructed-test-reader";
  packet.artifact.regions = packet.artifact.regions.slice(0, 2).map((r, i) => ({ ...r,
    id: `region-${i}`, anchor: { ...r.anchor, start: i === 0 ? 0 : 9, exact: i === 0 ? "Fear 😟." : "Joy. Plain." } }));
  const channel = reading("C3", [event([0, 8], .9, "threatened"), event([9, 13], .5, "restored"), event([14, 20], .7, "either")]);
  packet.bottom_box = BottomBoxSchema.parse({ version: "bottom-box-2", on_page: [channel,
    reading("N1", [{ span: [0, 8], confidence: .8, label: "curiosity" }]),
    reading("N5", [{ span: [0, 8], confidence: .8, label: "idealism" }]),
    reading(null, [{ span: [9, 13], confidence: .8, label: "romance" }]),
    reading("S1", [], [{ from: 0, to: 20, value: .5 }]),
  ], about_maker: [], toolbox: [] });
  const sources = pageNeedSources(packet);
  assert.ok(Math.abs(sources[0].confidence! - .7) < 1e-12);
  assert.deepEqual(sources.map(s => ({ ...s, confidence: Number(s.confidence!.toFixed(12)) })), [{ id: `page:constructed@${"a".repeat(64)}:C3`, label: "FEAR", type: "channel",
    confidence: .7, regions: ["region-0", "region-1"], nodes: [],
    needs: [{ id: "N2", direction: -1, illustration: false }, { id: "N2", direction: 1, illustration: false }] }]);
  assert.equal(pageNeedActivity(packet).N1[0].tag, "curiosity");
  assert.deepEqual(pageNeedActivity(packet).N5, []);
  assert.equal(pageStress(packet).length, 0);
  assert.equal(pageStress(packet, true).length, 1);
  assert.equal(workNeedSources(packet, [], packet.hypotheses).some(s => s.id.startsWith("page:")), false);
  assert.equal(workNeedSources(packet, [], packet.hypotheses, true).some(s => s.id.startsWith("page:")), true);
});

test("TS3 preserves old box inputs, rejects unmapped levels and nonempty maker claims", () => {
  const old = { bottom_box: { version: "bottom-box-1", on_page: [], about_maker: [], marketplace: [] } };
  assert.deepEqual(upgradeBottomBoxPacket(old), { bottom_box: { version: "bottom-box-2", on_page: [], about_maker: [], toolbox: [] } });
  assert.throws(() => reading(null, [], [{ from: 0, to: 2, value: .5 }]));
  assert.equal(BottomBoxSchema.safeParse({ version: "bottom-box-2", on_page: [], about_maker: [{}], toolbox: [] }).success, false);
});
