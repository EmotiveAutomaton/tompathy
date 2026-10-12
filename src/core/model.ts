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
  authors: z
    .array(
      z.object({
        label: z.string().min(1).max(250),
        basis: z.enum(["page-metadata", "byline", "structured-data"]),
      }),
    )
    .max(20)
    .optional(),
  capture: z
    .object({
      method: z.enum(["article", "main", "content-container", "page"]),
      note: z.string().max(1000),
    })
    .optional(),
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
  kind: z.enum(["goal", "process", "value", "attention"]),
  label: z.string().min(1).max(250),
  description: z.string().max(4000),
  makers: z.array(id).min(1),
  regions: z.array(id),
  spans: z
    .array(
      z.object({
        region: id,
        start: z.number().int().nonnegative(),
        end: z.number().int().positive(),
      }),
    )
    .max(1500)
    .optional(),
  status: z.enum(["hypothesis", "creator-reported", "observed", "unknown"]),
  support: SupportSchema.nullish(),
  alternativeSet: id.optional(),
  evidence: z.array(id),
  decisionNodes: z.array(id).optional(),
  interpretation: z
    .enum([
      "current-attention",
      "governing-purpose",
      "local-goal",
      "historical-event",
      "reader-route",
      "repertoire",
      "preference",
      "value",
    ])
    .optional(),
});
export const PacketSchema = z
  .object({
    schemaVersion: z.enum(["1.0", "1.1", "1.2", "1.3", "1.4"]),
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
    currentAttention: z
      .array(
        z.object({
          maker: id,
          span: z.object({
            region: id,
            start: z.number().int().nonnegative(),
            end: z.number().int().positive(),
          }),
          items: z
            .array(
              z.object({ hypothesis: id, support: SupportSchema.nullish() }),
            )
            .max(40),
        }),
      )
      .max(3000)
      .optional(),
    alternatives: z.array(
      z.object({
        id,
        kind: z.enum(["competing", "independent", "coexisting"]),
        members: z.array(id).min(1),
        exhaustive: z.boolean(),
      }),
    ),
    process: z.object({
      interpretation: z
        .enum(["historical-production", "functional", "unspecified"])
        .optional(),
      nodes: z.array(id),
      edges: z.array(
        z.object({
          from: id,
          to: id,
          relationship: z.string().min(1).max(500),
          kind: z
            .enum([
              "precedes",
              "enables",
              "revises",
              "alternative",
              "related",
              "order-unknown",
            ])
            .optional(),
          status: z
            .enum(["hypothesis", "creator-reported", "observed", "unknown"])
            .optional(),
          evidence: z.array(id).optional(),
        }),
      ),
    }),
    goalHierarchy: z
      .object({
        nodes: z
          .array(
            z.object({
              id,
              parentId: id.optional(),
              parentIds: z.array(id).min(1).max(16).optional(),
              maker: id,
              label: z.string().min(1).max(250),
              description: z.string().max(4000),
              level: z.string().min(1).max(100).optional(),
              regions: z.array(id).min(1),
              span: z
                .object({
                  region: id,
                  start: z.number().int().nonnegative(),
                  end: z.number().int().positive(),
                })
                .optional(),
              evidence: z.array(id),
            }),
          )
          .min(1)
          .max(3000),
      })
      .optional(),
    accounts: z
      .array(
        z.object({
          id,
          label: z.string().min(1).max(250),
          members: z.array(id).min(1),
          explanation: z.string().min(1).max(4000),
        }),
      )
      .max(30)
      .optional(),
    documentContribution: z
      .object({
        value: z.number().min(0).max(1).nullable(),
        quantity: z.string().min(1).max(500),
        explanation: z.string().min(1).max(4000),
        evidence: z.array(id),
      })
      .optional(),
    estimates: z.array(
      z.object({
        region: id,
        contribution: z
          .object({
            value: z.number().min(0).max(1),
            quantity: z.string().min(1).max(500),
            scale: z.literal("0–1"),
            explanation: z.string().max(4000).optional(),
            evidence: z.array(id).optional(),
            basis: z
              .enum(["global-and-local", "local-only", "unspecified"])
              .optional(),
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
    unique(p.accounts ?? [], "account");
    const hs = new Map(p.hypotheses.map((x) => [x.id, x])),
      rs = new Set(p.artifact.regions.map((x) => x.id)),
      ms = new Set(p.makers.map((x) => x.id)),
      es = new Set(p.evidence.map((x) => x.id));
    const hierarchy = p.goalHierarchy?.nodes ?? [];
    unique(hierarchy, "goal hierarchy");
    const hierarchyById = new Map(hierarchy.map((n) => [n.id, n]));
    for (const n of hierarchy) {
      if (
        !["1.3", "1.4"].includes(p.schemaVersion) &&
        !["document", "section", "paragraph", "sentence"].includes(
          n.level ?? "",
        )
      )
        error(
          `Legacy hierarchy node ${n.id} requires a supported level; use 1.3 for optional level names.`,
        );
      if (
        !ms.has(n.maker) ||
        n.regions.some((r) => !rs.has(r)) ||
        n.evidence.some((e) => !es.has(e))
      )
        error(`Unresolved hierarchy references in ${n.id}.`);
      if (
        n.parentIds &&
        (p.schemaVersion !== "1.4" ||
          n.parentId ||
          new Set(n.parentIds).size !== n.parentIds.length)
      )
        error(
          `Multiple parents require 1.4 and unambiguous unique parentIds in ${n.id}.`,
        );
      for (const parentId of n.parentIds ?? (n.parentId ? [n.parentId] : [])) {
        const parent = hierarchyById.get(parentId);
        if (!parent || parent.maker !== n.maker)
          error(`Invalid hierarchy parent in ${n.id}.`);
        if (parent && n.regions.some((r) => !parent.regions.includes(r)))
          error(`Hierarchy regions must stay within their parent in ${n.id}.`);
      }
      if (n.level === "sentence" && !n.span)
        error(`Sentence goal ${n.id} requires an explicit span.`);
      if (
        n.span &&
        (!n.regions.includes(n.span.region) ||
          n.span.end <= n.span.start ||
          n.span.end >
            (p.artifact.regions.find((r) => r.id === n.span!.region)?.anchor
              .exact.length ?? 0))
      )
        error(`Invalid sentence span in ${n.id}.`);
    }
    const depths = new Map<string, number>(),
      visitingHierarchy = new Set<string>();
    const maxDepth = ["1.3", "1.4"].includes(p.schemaVersion) ? 64 : 12;
    const visitHierarchy = (id: string): number => {
      if (visitingHierarchy.has(id) || visitingHierarchy.size >= maxDepth) {
        error(
          `Goal hierarchy must be acyclic and at most ${maxDepth} levels deep.`,
        );
        return maxDepth;
      }
      if (depths.has(id)) return depths.get(id)!;
      visitingHierarchy.add(id);
      const n = hierarchyById.get(id);
      const depth =
        1 +
        Math.max(
          0,
          ...(n?.parentIds ?? (n?.parentId ? [n.parentId] : [])).map(
            visitHierarchy,
          ),
        );
      visitingHierarchy.delete(id);
      depths.set(id, depth);
      if (depth > maxDepth)
        error(
          `Goal hierarchy must be acyclic and at most ${maxDepth} levels deep.`,
        );
      return depth;
    };
    hierarchy.forEach((n) => visitHierarchy(n.id));
    if (p.schemaVersion !== "1.4")
      for (const m of p.makers) {
        const nodes = hierarchy.filter((n) => n.maker === m.id);
        if (nodes.length && nodes.filter((n) => !n.parentId).length !== 1)
          error("Each legacy maker hierarchy needs exactly one root.");
      }
    if (
      p.schemaVersion !== "1.4" &&
      (p.currentAttention || p.hypotheses.some((h) => h.kind === "attention"))
    )
      error("Independent current attention requires contract 1.4.");
    for (const frame of p.currentAttention ?? []) {
      const span = frame.span,
        region = p.artifact.regions.find((r) => r.id === span.region);
      if (
        !ms.has(frame.maker) ||
        !region ||
        span.end <= span.start ||
        span.end > region.anchor.exact.length
      )
        error("Invalid current-attention span or maker.");
      if (
        new Set(frame.items.map((i) => i.hypothesis)).size !==
        frame.items.length
      )
        error("Duplicate current-attention item.");
      for (const item of frame.items) {
        const h = hs.get(item.hypothesis),
          s = item.support === undefined ? h?.support : item.support;
        if (
          !h ||
          h.kind !== "attention" ||
          !h.makers.includes(frame.maker) ||
          (h.regions.length && !h.regions.includes(span.region))
        )
          error(
            "Current attention must reference separate, matching attention hypotheses.",
          );
        if (
          s &&
          (s.scale[0] >= s.scale[1] ||
            s.value < s.scale[0] ||
            s.value > s.scale[1])
        )
          error("Attention support outside declared scale.");
        if (
          s?.semantics === "probability" &&
          (s.scale[0] !== 0 || s.scale[1] !== 1 || !s.candidateSet)
        )
          error(
            "Attention probability requires scale [0,1] and a candidate set.",
          );
        if (
          s?.candidateSet &&
          !p.alternatives.some(
            (a) =>
              a.id === s.candidateSet && a.members.includes(item.hypothesis),
          )
        )
          error("Invalid attention candidate set.");
      }
      for (const set of p.alternatives.filter(
        (a) => a.exhaustive && a.kind === "competing",
      )) {
        const scores = set.members.map((id) => {
          const item = frame.items.find((i) => i.hypothesis === id);
          return item
            ? item.support === undefined
              ? hs.get(id)?.support
              : item.support
            : undefined;
        });
        if (
          scores.some((s) => s?.semantics === "probability") &&
          (scores.some(
            (s) => s?.semantics !== "probability" || s.candidateSet !== set.id,
          ) ||
            Math.abs(scores.reduce((a, s) => a + (s?.value ?? 0), 0) - 1) >
              0.000001)
        )
          error("Exhaustive attention probability set must sum to 1.");
      }
    }
    const frames = [...(p.currentAttention ?? [])].sort(
      (a, b) =>
        a.maker.localeCompare(b.maker) ||
        a.span.region.localeCompare(b.span.region) ||
        a.span.start - b.span.start,
    );
    for (let i = 1; i < frames.length; i++)
      if (
        frames[i].maker === frames[i - 1].maker &&
        frames[i].span.region === frames[i - 1].span.region &&
        frames[i].span.start < frames[i - 1].span.end
      )
        error("Current-attention spans must not overlap for the same maker.");
    for (const h of p.hypotheses) {
      if (
        h.spans?.some(
          (s) =>
            !h.regions.includes(s.region) ||
            s.start >= s.end ||
            s.end >
              (p.artifact.regions.find((r) => r.id === s.region)?.anchor.exact
                .length ?? 0),
        )
      )
        error(`Invalid goal span in ${h.id}.`);
      if (
        h.decisionNodes?.some(
          (n) =>
            !hierarchyById.has(n) ||
            !h.makers.includes(hierarchyById.get(n)!.maker),
        )
      )
        error(`Unresolved decision reference in ${h.id}.`);
      if (
        h.makers.some((x) => !ms.has(x)) ||
        h.regions.some((x) => !rs.has(x)) ||
        h.evidence.some((x) => !es.has(x))
      )
        error(`Unresolved references in ${h.id}.`);
      const allowedInterpretations = {
        attention: ["current-attention"],
        goal: ["governing-purpose", "local-goal"],
        process: ["historical-event", "reader-route", "repertoire"],
        value: ["preference", "value"],
      };
      if (
        h.interpretation &&
        !allowedInterpretations[h.kind].includes(h.interpretation)
      )
        error(`Interpretation does not match hypothesis kind in ${h.id}.`);
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
    for (const a of p.accounts ?? []) {
      if (
        new Set(a.members).size !== a.members.length ||
        a.members.some((x) => !hs.has(x))
      )
        error(`Invalid members in account ${a.id}.`);
    }
    const evidenceLists = [
      p.documentContribution?.evidence ?? [],
      ...p.process.edges.map((e) => e.evidence ?? []),
      ...p.estimates.map((e) => e.contribution?.evidence ?? []),
    ];
    if (evidenceLists.some((list) => list.some((x) => !es.has(x))))
      error("Unresolved contribution or process relationship evidence.");
    // Only explicit temporal claims imply order. A historical partial order cannot cycle.
    const temporal = p.process.edges.filter((e) => e.kind === "precedes");
    const visiting = new Set<string>(),
      visited = new Set<string>();
    const cycles = (node: string): boolean => {
      if (visiting.has(node)) return true;
      if (visited.has(node)) return false;
      visiting.add(node);
      if (temporal.filter((e) => e.from === node).some((e) => cycles(e.to)))
        return true;
      visiting.delete(node);
      visited.add(node);
      return false;
    };
    if (p.process.nodes.some(cycles))
      error("Historical precedence cannot contain a cycle.");
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
  authorLabel: z.string().max(250).optional(),
  savedPageId: z.uuid().optional(),
  contextSources: z
    .array(z.object({ author: z.string().max(250), url: z.string().max(4000) }))
    .max(3)
    .optional(),
  history: z
    .array(
      z.object({
        packet: PacketSchema,
        context: z.array(ContextSchema).max(30),
        acceptedAt: timestamp,
      }),
    )
    .max(5)
    .optional(),
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
