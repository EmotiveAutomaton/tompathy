import assert from "node:assert/strict";
import { mkdtemp, mkdir, writeFile, rm } from "node:fs/promises";
import { join } from "node:path";
import { test } from "node:test";
import { BottomBoxSchema, PageReadingSchema, upgradeBottomBoxPacket } from "../src/core/bottom-box";
import { authorNeedSources, workNeedSources } from "../src/core/need-view";
import { createExample } from "../src/core/example";

test("reader contract upgrades only valid legacy empties and keeps maker readings closed", () => {
  const empty = { value: null, evidence: [], status: "unvalidated", ledgerRows: [] };
  const group = (keys: string[]) => Object.fromEntries(keys.map(k => [k, empty]));
  const raw = { schemaVersion: "1.10", bottom_box: { version: "bottom-box-0", hub: null,
    set_points: group(["knowledge", "tending", "belonging", "seen_as_competent", "seen_as_kind"]),
    body: group(["warmth", "food", "sleep"]), readings: group(["stress", "freedom"]),
    channels: group(["SEEKING", "FEAR", "RAGE", "PANIC_GRIEF", "CARE", "PLAY", "LUST", "DISGUST", "SHAME"]) } };
  const next = upgradeBottomBoxPacket(raw) as { schemaVersion: string; bottom_box: unknown };
  assert.equal(next.schemaVersion, "1.11");
  assert.deepEqual(BottomBoxSchema.parse(next.bottom_box), { version: "bottom-box-1", on_page: [], about_maker: [], marketplace: [] });
  const invalid = { ...raw, bottom_box: { ...raw.bottom_box, hub: "x", surprise: 1 } };
  assert.equal(upgradeBottomBoxPacket(invalid), invalid);
  assert.equal(BottomBoxSchema.safeParse({ version: "bottom-box-1", on_page: [], about_maker: [{}], marketplace: [] }).success, false);
  assert.equal(PageReadingSchema.safeParse({ status: "admitted" }).success, false);
});

test("real packets never receive demonstration need links or invented life actions", async () => {
  const packet = await createExample();
  packet.provider.id = "real-reader";
  const sources = workNeedSources(packet, [], packet.hypotheses);
  assert.ok(sources.every(s => s.needs.length === 0));
  const actions = authorNeedSources(packet, [], sources);
  assert.equal(actions.length, 1);
  assert.equal(actions[0].current, true);
  assert.equal(actions[0].date, undefined);
  assert.deepEqual(actions[0].needs, []);
});

test("release packaging refuses research and constructed packs", async () => {
  // Import the build guard as runtime JS without bundling its filesystem recursion.
  const { assertReleasePacks } = await import("../scripts/reader-pack-safety.mjs");
  const root = await mkdtemp(join(process.cwd(), ".local/reader-release-test-"));
  try {
    await mkdir(join(root, "reader"));
    const path = join(root, "reader", "pack.json");
    const pack = { version: "reader-pack-1", research_only: true,
      encoder: { kind: "sentence-transformers", license: { commercial_use: true } },
      training: [{ commercial_use: false }] };
    await writeFile(path, JSON.stringify(pack));
    await assert.rejects(assertReleasePacks(root), /Research-only/);
    await writeFile(path, JSON.stringify({ ...pack, research_only: false,
      encoder: { kind: "constructed", license: { commercial_use: true } }, training: [{ commercial_use: true }] }));
    await assert.rejects(assertReleasePacks(root), /constructed/);
  } finally { await rm(root, { recursive: true, force: true }); }
});
