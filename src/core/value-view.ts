import { z } from "zod";

export const WorkValueViewSchema = z
  .strictObject({
    work: z.string(),
    evidenceTier: z.enum(["T0", "production"]),
    provenance: z.enum(["structure-only", "admitted"]),
    asOf: z.iso.datetime({ offset: true }),
    firstMissingLink: z.string().max(1000).nullable(),
    rows: z
      .array(
        z.strictObject({
          id: z.string().min(1).max(200),
          label: z.string().min(1).max(300),
          order: z.number().int().nonnegative(),
          date: z.iso.datetime({ offset: true }).nullable(),
          evidence: z.array(z.string()).max(30),
          region: z.string().nullable().optional(),
        }),
      )
      .max(1500),
    tips: z
      .array(
        z.strictObject({
          id: z.string().min(1).max(200),
          label: z.string().min(1).max(200),
          status: z.enum([
            "drawn",
            "named-not-drawn",
            "no-evidence",
            "no-admitted-reader",
          ]),
          support: z.number().finite().nullable(),
          interval: z
            .tuple([z.number().finite(), z.number().finite()])
            .nullable()
            .optional(),
          hypothesis: z.string().nullable().optional(),
        }),
      )
      .max(1000),
    feeds: z
      .array(
        z.strictObject({
          row: z.string(),
          tip: z.string(),
          weight: z.number().min(0).max(1),
        }),
      )
      .max(30000),
    coSupport: z
      .array(
        z.strictObject({
          tips: z.tuple([z.string(), z.string()]),
          share: z.number().min(0).max(1),
        }),
      )
      .max(500),
  })
  .superRefine((view, ctx) => {
    const fail = (message: string) => ctx.addIssue({ code: "custom", message });
    const rows = new Set(view.rows.map((r) => r.id)),
      tips = new Set(view.tips.map((t) => t.id)),
      drawn = new Set(
        view.tips.filter((t) => t.status === "drawn").map((t) => t.id),
      );
    if (rows.size !== view.rows.length || tips.size !== view.tips.length)
      fail("Duplicate value-view identity");
    for (const tip of view.tips) {
      if (
        tip.support !== null &&
        (!tip.interval ||
          tip.interval[0] > tip.support ||
          tip.interval[1] < tip.support)
      )
        fail("Tip interval must contain its contrast");
      if (
        ["drawn", "named-not-drawn"].includes(tip.status) &&
        (tip.support === null || !tip.hypothesis)
      )
        fail("Estimated tips require their admitted hypothesis");
      if (tip.status === "drawn" && (!tip.interval || tip.interval[0] <= 0))
        fail("Drawn tip requires lower 95% bound above zero");
    }
    if (
      (view.evidenceTier === "T0" || view.provenance === "structure-only") &&
      view.tips.some(
        (t) =>
          t.support !== null || ["drawn", "named-not-drawn"].includes(t.status),
      )
    )
      fail("Structure-only views cannot carry inferred tips");
    if (view.feeds.some((f) => !rows.has(f.row) || !tips.has(f.tip)))
      fail("Unresolved value-view feed");
    if (
      view.coSupport.some(
        (c) => c.tips[0] === c.tips[1] || c.tips.some((t) => !drawn.has(t)),
      )
    )
      fail("Co-support only connects distinct drawn tips");
  });
