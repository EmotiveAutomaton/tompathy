import { z } from "zod";

const id = z.string().min(1).max(200);
const timestamp = z.iso.datetime();
export const AnchorSchema = z.object({
  exact: z.string().min(1).max(20000),
  prefix: z.string().max(160),
  suffix: z.string().max(160),
  start: z.number().int().nonnegative(),
  index: z.number().int().nonnegative(),
});
export const ArtifactSchema = z.object({
  id,
  revision: id,
  title: z.string().max(1000),
  source: z.string().max(4000),
  capturedAt: timestamp,
  regions: z
    .array(z.object({ id, anchor: AnchorSchema }))
    .min(1)
    .max(1500),
  truncated: z.boolean().default(false),
});
export const ContextSchema = z.object({
  id,
  source: z.string().max(4000),
  excerpt: z.string().min(1).max(20000),
  retrievedAt: timestamp,
  selected: z.boolean(),
  lineage: z.enum(["pasted", "file", "public-url", "synthetic"]),
});
const SupportSchema = z.object({
  value: z.number().finite(),
  scale: z.tuple([z.number().finite(), z.number().finite()]),
  semantics: z.enum(["relative", "probability"]),
  meaning: z.string().min(1).max(1000),
  calibration: z.string().max(1000).optional(),
  candidateSet: id.optional(),
});
export const HypothesisSchema = z.object({
  id,
  kind: z.enum(["goal", "process", "value"]),
  label: z.string().min(1).max(250),
  description: z.string().max(4000),
  makers: z.array(id).min(1),
  regions: z.array(id),
  status: z.enum(["hypothesis", "creator-reported", "observed", "unknown"]),
  support: SupportSchema.nullish(),
  alternativeSet: id.optional(),
  evidence: z.array(id),
});
export const PacketSchema = z
  .object({
    schemaVersion: z.literal("1.0"),
    id,
    revision: z.number().int().positive(),
    artifact: ArtifactSchema,
    provider: z.object({ id, method: z.string().min(1).max(1000) }),
    origin: z.enum(["synthetic example", "imported", "live provider"]),
    scope: z.object({
      kind: z.enum(["artifact", "context"]),
      contextIds: z.array(id),
    }),
    makers: z
      .array(
        z.object({
          id,
          label: z.string().max(250),
          identity: z.enum(["unknown", "supplied", "synthetic"]),
          relationship: z.string().max(1000),
        }),
      )
      .min(1),
    hypotheses: z.array(HypothesisSchema).max(1000),
    alternatives: z.array(
      z.object({
        id,
        kind: z.enum(["competing", "independent"]),
        members: z.array(id).min(1),
        exhaustive: z.boolean(),
      }),
    ),
    process: z.object({
      nodes: z.array(id),
      edges: z.array(
        z.object({
          from: id,
          to: id,
          relationship: z.string().min(1).max(500),
        }),
      ),
    }),
    estimates: z.array(
      z.object({
        region: id,
        contribution: z
          .object({
            value: z.number().min(0).max(1),
            quantity: z.string().min(1).max(500),
            scale: z.literal("0–1"),
          })
          .nullish(),
        uncertainty: z.object({
          level: z.enum(["low", "medium", "high", "unknown"]),
          meaning: z.string().min(1).max(500),
        }),
      }),
    ),
    evidence: z.array(
      z.object({
        id,
        source: z.string().max(4000),
        excerpt: z.string().max(20000),
        capturedAt: timestamp,
        relationship: z.string().min(1).max(2000),
      }),
    ),
    revisionOf: id.optional(),
    changeExplanation: z.string().max(4000).optional(),
  })
  .superRefine((p, ctx) => {
    const error = (message: string) =>
      ctx.addIssue({ code: "custom", message });
    const unique = (items: { id: string }[], name: string) => {
      if (new Set(items.map((x) => x.id)).size !== items.length)
        error(`Duplicate ${name} IDs.`);
    };
    unique(p.hypotheses, "hypothesis");
    unique(p.artifact.regions, "region");
    unique(p.makers, "maker");
    unique(p.evidence, "evidence");
    unique(p.alternatives, "alternative set");
    const hs = new Map(p.hypotheses.map((x) => [x.id, x])),
      rs = new Set(p.artifact.regions.map((x) => x.id)),
      ms = new Set(p.makers.map((x) => x.id)),
      es = new Set(p.evidence.map((x) => x.id));
    for (const h of p.hypotheses) {
      if (
        h.makers.some((x) => !ms.has(x)) ||
        h.regions.some((x) => !rs.has(x)) ||
        h.evidence.some((x) => !es.has(x))
      )
        error(`Unresolved references in ${h.id}.`);
      if (h.support) {
        const s = h.support;
        if (
          s.scale[0] >= s.scale[1] ||
          s.value < s.scale[0] ||
          s.value > s.scale[1]
        )
          error(`Support outside declared scale in ${h.id}.`);
        if (
          s.semantics === "probability" &&
          (s.scale[0] !== 0 || s.scale[1] !== 1 || !s.candidateSet)
        )
          error(
            `Probability in ${h.id} requires scale [0,1] and a candidate set.`,
          );
        if (
          s.candidateSet &&
          !p.alternatives.some(
            (a) => a.id === s.candidateSet && a.members.includes(h.id),
          )
        )
          error(`Invalid candidate set for ${h.id}.`);
      }
      if (
        h.alternativeSet &&
        !p.alternatives.some(
          (a) => a.id === h.alternativeSet && a.members.includes(h.id),
        )
      )
        error(`Invalid alternative set for ${h.id}.`);
    }
    for (const a of p.alternatives) {
      if (a.members.some((x) => !hs.has(x)))
        error(`Missing member of ${a.id}.`);
      const scores = a.members.map((x) => hs.get(x)?.support);
      if (
        a.kind === "competing" &&
        a.exhaustive &&
        scores.some((s) => s?.semantics === "probability")
      ) {
        if (
          scores.some(
            (s) => s?.semantics !== "probability" || s.candidateSet !== a.id,
          ) ||
          Math.abs(scores.reduce((v, s) => v + (s?.value ?? 0), 0) - 1) >
            0.000001
        )
          error(`Exhaustive probability set ${a.id} must sum to 1.`);
      }
    }
    if (p.process.nodes.some((x) => hs.get(x)?.kind !== "process"))
      error("Process nodes must reference process hypotheses.");
    if (
      p.process.edges.some(
        (e) =>
          !p.process.nodes.includes(e.from) || !p.process.nodes.includes(e.to),
      )
    )
      error("Process edge has an unresolved endpoint.");
    if (
      p.estimates.some((e) => !rs.has(e.region)) ||
      new Set(p.estimates.map((e) => e.region)).size !== p.estimates.length
    )
      error("Invalid or duplicate estimate region.");
    if (p.scope.kind === "artifact" && p.scope.contextIds.length)
      error("Artifact scope cannot include context.");
  });
export type Artifact = z.infer<typeof ArtifactSchema>;
export type Packet = z.infer<typeof PacketSchema>;
export type Hypothesis = z.infer<typeof HypothesisSchema>;
export type ContextItem = z.infer<typeof ContextSchema>;
export type Scope = "artifact" | "context";
export const SessionSchema = z.object({
  sessionVersion: z.literal("1.0"),
  artifact: ArtifactSchema.nullable(),
  packet: PacketSchema.nullable(),
  context: z.array(ContextSchema).max(30),
  scope: z.enum(["artifact", "context"]),
});
export type Session = z.infer<typeof SessionSchema>;
export { normalize, makeArtifact } from "./artifact";
export function matchPacket(
  packet: Packet,
  artifact: Artifact,
  scope: Scope,
  context: ContextItem[],
): string | null {
  if (
    packet.artifact.id !== artifact.id ||
    packet.artifact.revision !== artifact.revision
  )
    return "This result belongs to a different artifact or text revision. Capture its source and import again.";
  if (
    packet.artifact.regions.length !== artifact.regions.length ||
    packet.artifact.regions.some((r, i) => {
      const a = artifact.regions[i];
      return (
        r.id !== a.id ||
        (["exact", "prefix", "suffix", "start", "index"] as const).some(
          (k) => r.anchor[k] !== a.anchor[k],
        )
      );
    })
  )
    return "Passage anchors do not match this capture. No claims have been attached.";
  const selected = context
    .filter((c) => c.selected)
    .map((c) => c.id)
    .sort();
  if (
    packet.scope.kind !== scope ||
    (scope === "context" &&
      JSON.stringify([...packet.scope.contextIds].sort()) !==
        JSON.stringify(selected))
  )
    return "Analysis scope differs from the selected context. Import a matching revision.";
  return null;
}
export function parsePacket(text: string): Packet {
  if (text.length > 2_000_000)
    throw Error("Result exceeds the 2 MB import limit.");
  const result = PacketSchema.safeParse(JSON.parse(text));
  if (!result.success)
    throw Error(
      result.error.issues
        .slice(0, 4)
        .map((e) => `${e.path.join(".") || "Packet"}: ${e.message}`)
        .join("\n"),
    );
  return result.data;
}
