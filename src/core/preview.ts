import { z } from "zod";
import type { Packet } from "./model";

/** Exact-cache replay must catch up before replacing a saved partial reading. */
export function keepsPreviewProgress(next: Packet, previous: Packet) {
  if (!previous.preview) return true;
  if (!next.preview) return false;
  const modules = new Map(next.preview.modules.map(m => [m.id, m]));
  return previous.preview.modules.every(old => {
    const current = modules.get(old.id);
    return current && (old.status !== "complete" || current.status === "complete") &&
      (current.completed ?? 0) >= (old.completed ?? 0);
  }) && (previous.preview.coverage ?? []).every(r => next.preview!.coverage?.includes(r)) &&
    (previous.goalHierarchy?.nodes ?? []).every(n => next.goalHierarchy?.nodes.some(candidate => candidate.id === n.id)) &&
    (next.preview.payoff?.sentencesScored ?? 0) >= (previous.preview.payoff?.sentencesScored ?? 0);
}

export const previewLabels = {
  entry: z.enum(["page", "person", "process"]).optional(),
  evidenceStatus: z.enum(["admitted", "constructed-tested", "unvalidated"]).optional(),
  basis: z.enum(["choices", "corrections", "history", "text-surface", "population", "model-judgment"]).optional(),
};
export const PreviewSchema = z.object({
  rootCueReliability: z.number().min(0).max(1).optional(),
  rootCueStatus: z.literal("assumed").optional(),
  goalLenses: z.array(z.array(z.string())).max(2).nullish(),
  budgetDrops: z.array(z.enum(["payoff-layer-2", "second-reader", "techniques-after-30", "governing-call"])).max(4).optional(),
  github: z.object({ quotaRemaining: z.number().int().nonnegative().nullable(), commits: z.number().int().positive(), declaredAiCommitShare: z.number().min(0).max(1) }).nullish(),
  payoff: z.object({ sentencesScored: z.number().int().nonnegative().nullish(), totalSentences: z.number().int().nonnegative().nullish(), layer1NovelRetention: z.number().min(0).max(1), layer2NovelRetention: z.number().min(0).max(1).nullish(), layer1Seconds: z.number().nonnegative(), contextFreeMean: z.number().nonnegative().nullable(), easyWithoutContext: z.boolean(), layer2Status: z.string().max(500) }).nullish(),
  agreement: z.object({
    short: z.object({ spearman: z.number().min(-1).max(1).nullable(), overlap: z.number().min(0).max(1), words: z.number().int().positive() }),
    full: z.object({ spearman: z.number().min(-1).max(1).nullable(), overlap: z.number().min(0).max(1), words: z.number().int().positive() }),
    regions: z.array(z.object({ region: z.string(), readers: z.array(z.union([z.literal(0), z.literal(1)])).min(1).max(2) })).max(1500),
    method: z.string().max(1000),
  }).nullish(),
  modules: z.array(z.object({
    id: z.string().min(1).max(100), title: z.string().min(1).max(200),
    status: z.enum(["pending", "running", "complete", "unavailable", "failed", "skipped"]),
    detail: z.string().max(2000), elapsedMs: z.number().nonnegative().nullish(),
    completed: z.number().int().nonnegative().nullish(), total: z.number().int().nonnegative().nullish(), unit: z.string().max(100).nullish(),
  }).refine(m => (m.completed == null) === (m.total == null) && (m.completed == null || m.completed <= m.total!), "Progress must have bounded completed and total counts")).max(20),
  readers: z.array(z.object({
    id: z.string().max(200), revision: z.string().max(200),
    sha256: z.string().regex(/^[a-f0-9]{64}$/), backend: z.string().max(200),
  })).max(4),
  statistics: z.object({
    mean: z.number().nonnegative(), median: z.number().nonnegative(),
    iqr: z.number().nonnegative(), words: z.number().int().nonnegative(),
    heldOut: z.number().int().nonnegative(), heldOutExamples: z.array(z.string()).max(20),
  }).nullish(),
  cachedAt: z.iso.datetime().nullish(), completedAt: z.iso.datetime().nullish(),
  latestSummary: z.string().max(2000).optional(),
  resumable: z.boolean().optional(), priorityRegion: z.string().nullish(),
  coverage: z.array(z.string()).max(1500).nullish(),
  layoutGroups: z.array(z.array(z.string())).max(20).nullish(),
  historySource: z.enum(["wikipedia", "github"]).nullish(),
  timings: z.record(z.string(), z.number().nonnegative()).nullish(),
});

export const PREVIEW_NOTICE = "Research preview: these are the engine's guesses. Each one says what it's based on and whether it has been tested.";
