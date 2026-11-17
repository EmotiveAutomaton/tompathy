import { z } from "zod";
import names from "./reader-names.json";

export const readerNames = names;
const unit = z.number().finite().min(0).max(1);
const span = z.tuple([z.number().int().nonnegative(), z.number().int().positive()])
  .refine(([a, b]) => a < b, "Invalid span");
const mapping = z.strictObject({ status: z.enum(["proposed", "ruled"]), source: z.string().min(1).max(2000) });
const readingId = z.enum(["N1", "N2", "N3", "N4", "N5", "N6", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "S1", "K1"]);
const share = z.strictObject({ value: unit, interval: z.tuple([unit, unit]),
  of: z.literal("sentences read as carrying a feeling"), method: z.literal("corrected") })
  .refine(s => s.interval[0] <= s.value && s.value <= s.interval[1], "Invalid share interval");
export const PageReadingSchema = z.strictObject({
  id: readingId.nullable(), tier: z.literal("on_page"), share: share.nullable(),
  events: z.array(z.strictObject({
    span, label: z.string().min(1).max(200), confidence: unit,
    who: z.enum(["writer", "other", "unclear"]).default("unclear"),
    words: z.array(span).max(200).default([]),
    channel_by_table: z.strictObject({ channel: z.enum(["C2", "C3", "C6", "C8", "C9"]),
      version: z.string().min(1).max(200) }).nullish(),
    stake: z.strictObject({ need: z.enum(["N1", "N2", "N3", "N4", "N5", "N6"]),
      direction: z.enum(["up", "down", "threatened", "restored", "unfed", "either"]),
      by: z.enum(["self", "other", "circumstance", "any"]), when: z.enum(["ahead", "already", "now", "any"]),
      mapping }).nullish(),
  }).refine(e => e.words.every(([a, b]) => e.span[0] <= a && b <= e.span[1]), "Attribution outside event")).max(10000),
  series: z.array(z.strictObject({ from: z.number().int().nonnegative(), to: z.number().int().positive(), value: unit })
    .refine(s => s.from < s.to, "Invalid series span")).max(2000),
  pack: z.string().regex(/^[a-z0-9][a-z0-9-]*@[0-9a-f]{64}$/),
  key: z.strictObject({ corpus: z.string().min(1).max(300), labelled_by: z.string().min(1).max(300), n: z.number().int().positive() }),
  score: z.strictObject({ metric: z.string().min(1).max(100), value: z.number().finite(), interval: z.tuple([z.number().finite(), z.number().finite()]).nullable() })
    .refine(s => !s.interval || s.interval[0] <= s.value && s.value <= s.interval[1], "Invalid score interval"),
  people: z.record(z.string(), z.number().finite()), floor: z.record(z.string(), z.number().finite()),
  nothing_here: z.record(z.string(), unit.nullable()), mapping, status: z.enum(["benchmarked", "research"]),
}).refine(r => r.id !== null || (r.status === "research" && r.share === null && !r.series.length
  && r.events.every(e => !e.stake)), "Unmapped labels cannot imply a level or stake");
const BottomBoxV1Schema = z.strictObject({
  version: z.literal("bottom-box-1"), on_page: z.array(PageReadingSchema).max(100),
  about_maker: z.array(z.never()).max(0),
  marketplace: z.array(z.strictObject({ id: z.string().min(1).max(200), label: z.string().min(1).max(250), source: z.string().min(1).max(2000) })).max(100),
}).refine(b => b.on_page.every(r => r.id !== null) && new Set(b.on_page.map(r => `${r.id}:${r.pack}`)).size === b.on_page.length
  && new Set(b.marketplace.map(t => t.id)).size === b.marketplace.length, "Duplicate reader or tile");
const BottomBoxV2Schema = z.strictObject({
  version: z.literal("bottom-box-2"), on_page: z.array(PageReadingSchema).max(100),
  about_maker: z.array(z.never()).max(0),
  toolbox: z.array(z.strictObject({ id: z.string().min(1).max(200), label: z.string().min(1).max(250), source: z.string().min(1).max(2000) })).max(100),
}).refine(b => new Set(b.on_page.map(r => `${r.id}:${r.pack}`)).size === b.on_page.length
  && new Set(b.toolbox.map(t => t.id)).size === b.toolbox.length, "Duplicate reader or tile");
export const BottomBoxSchema = z.union([BottomBoxV1Schema, BottomBoxV2Schema]);
const empty = z.strictObject({ value: z.null(), evidence: z.array(z.never()).max(0),
  status: z.literal("unvalidated"), ledgerRows: z.array(z.never()).max(0) });
const group = (keys: string[]) => z.record(z.string(), empty).refine(g => keys.length === Object.keys(g).length && keys.every(k => k in g));
const legacy = z.strictObject({ version: z.literal("bottom-box-0"), hub: z.string().max(250).nullable(),
  set_points: group(["knowledge", "tending", "belonging", "seen_as_competent", "seen_as_kind"]),
  body: group(["warmth", "food", "sleep"]), readings: group(["stress", "freedom"]),
  channels: group(["SEEKING", "FEAR", "RAGE", "PANIC_GRIEF", "CARE", "PLAY", "LUST", "DISGUST", "SHAME"]) });
export function upgradeBottomBoxPacket(raw: unknown): unknown {
  if (!raw || typeof raw !== "object") return raw;
  const p = raw as Record<string, unknown>;
  if (legacy.safeParse(p.bottom_box).success) return { ...p, schemaVersion: "1.11",
    bottom_box: { version: "bottom-box-1", on_page: [], about_maker: [], marketplace: [] } };
  const old = BottomBoxV1Schema.safeParse(p.bottom_box);
  if (old.success) {
    const { marketplace, ...rest } = old.data;
    return { ...p, bottom_box: { ...rest, version: "bottom-box-2", toolbox: marketplace } };
  }
  return raw;
}
export type PageReading = z.infer<typeof PageReadingSchema>;
