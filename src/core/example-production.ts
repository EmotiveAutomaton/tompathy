import type { Artifact, ContextItem, GhostReading } from "./model";
import { sentences } from "./sentences";
const notebook = [
  [
    "2026-09-04",
    "First playtest",
    "Mara's handwritten notes describe players waiting at the door. The original instruction draft predates any AI session.",
  ],
  [
    "2026-09-06",
    "Review recordings",
    "Three pairs of players were observed. The second pair had an unreliable controller; the third had prior puzzle exposure.",
  ],
  [
    "2026-09-09",
    "Access review",
    "A collaborator's checklist already required paired sound and visual cues and a pause control. Mara added the persistent latch after the one-handed playtest.",
  ],
  [
    "2026-09-12",
    "Draft with an assistant",
    "An assistant proposed 'room to notice'; Mara selected and revised that phrasing. A later automated assembly step generated a universal-inclusion claim after her final review.",
  ],
  [
    "2026-09-14",
    "Copy edit and response",
    "Mara accepted shortening edits and restored the controller detail. Her draft already cautioned against guarantees. An automated assembly step then inserted a guarantee she never reviewed; the publication copy contradicts her draft's caution.",
  ],
];
export const exampleContext: ContextItem = {
  id: "context-notebook",
  source: "Fictional studio notebook · Lantern House",
  selected: true,
  retrievedAt: "2026-09-14T10:00:00.000Z",
  lineage: "synthetic",
  excerpt:
    "Mara Vale makes cooperative puzzle games. A collaborator supplied the visual cues and pause control requirements; Mara added the persistent latch after a playtest. Drafts include selected AI suggestions, light copy edits, and an unreviewed generated claim. All people, records and dates here are fictional.",
  facts: notebook.map(([date, label, quote]) => ({
    date,
    label,
    quote,
    source: "Fictional studio notebook · Lantern House",
    dateKind: "event",
  })),
};
export function exampleEmphasis(region: string, text: string) {
  const phrases: Record<string, string> = {
    p3: "leaving enough time",
    p5: "who gets to remain",
    p8: "an invitation and a guarantee",
  };
  const phrase = phrases[region],
    start = phrase ? text.indexOf(phrase) : -1;
  return start >= 0 ? [{ start, end: start + phrase.length }] : [];
}
const production: [GhostReading["kind"], number, string][] = [
  [
    "original",
    0.93,
    "A dated handwritten draft contains this wording before the assistant session.",
  ],
  [
    "edited",
    0.84,
    "A saved copy-edit diff shortens the phrasing without changing the described design choice.",
  ],
  [
    "original",
    0.91,
    "The observation log and personal draft agree; the interpretation remains Mara's account.",
  ],
  [
    "curated",
    0.78,
    "A collaborator's checklist supplies some of the decisions, which Mara selects and explains.",
  ],
  [
    "original",
    0.65,
    "This reflection appears in the personal draft, but its earlier drafting history is incomplete.",
  ],
  [
    "curated",
    0.96,
    "The assistant transcript and revision log show a deliberately selected phrase woven into Mara's own account.",
  ],
  [
    "original",
    0.89,
    "Mara's draft already cautioned against generalizing from three pairs. This predates the unreviewed guarantee inserted during assembly.",
  ],
  [
    "edited",
    0.94,
    "The visible diff records sentence shortening; the controller detail was restored by Mara.",
  ],
  [
    "original",
    0.48,
    "A draft fragment contains this plan; no record shows whether earlier phrasing was assisted.",
  ],
];
export function exampleGhostReadings(artifact: Artifact): GhostReading[] {
  return artifact.regions.slice(1).flatMap((r, i) =>
    sentences(r.anchor.exact).map((s, j) => {
      let [kind, confidence, explanation] = production[i];
      const ghost = i === 5 && j === 2;
      if ((i === 3 && j >= 2) || (i === 5 && j === 0)) {
        kind = "original";
        confidence = 0.87;
        explanation =
          i === 3
            ? "The playtest note records Mara proposing the persistent latch; the collaborator's checklist did not contain it."
            : "This distinction appears in Mara's draft before the assisted phrase is introduced.";
      }
      const evidence = ghost
        ? ["production-ghost", "production-caution"]
        : i === 3 && j >= 2
          ? ["production-latch", "production-context-4"]
          : i === 5 && j === 0
            ? ["production-distinction", "production-context-7"]
            : [`production-${i + 1}`, `production-context-${i + 1}`];
      return {
        maker: "maker-1",
        span: { region: r.id, start: s.start, end: s.end },
        kind: ghost ? "ghost" : kind,
        confidence: ghost ? 0.99 : Math.max(0.2, confidence - j * 0.045),
        explanation: ghost
          ? "An automated assembly step inserted this assistant-generated guarantee after Mara's final review. It contradicts the caution already in her draft. The fictional version log records no review of the added sentence."
          : explanation,
        confidenceExplanation:
          "Illustrative support from the fictional draft record, not a calibrated probability. Missing intermediate versions lower confidence.",
        evidence,
        evidenceDirections: evidence.map((id, k) => ({
          id,
          direction: ghost
            ? ("less" as const)
            : kind === "original"
              ? (i === 4 || i === 8 || i === 3) && k === 1
                ? ("neutral" as const)
                : ("more" as const)
              : kind === "edited"
                ? k === 0
                  ? ("less" as const)
                  : ("more" as const)
                : ("less" as const),
        })),
        ...(ghost
          ? {
              prompt:
                "Write one upbeat concluding sentence claiming the tutorial makes all players feel included.",
            }
          : {}),
      };
    }),
  );
}
export function productionEvidence(artifact: Artifact) {
  const context = [
    "The first playtest predates the assistant session by eight days; its notes already describe waiting at the greenhouse door.",
    "The copy-edit changes phrasing, while the joint latch and waiting-for-a-partner decisions already appear in the earlier draft.",
    "A tester challenged Mara’s interpretation of silence. The draft keeps both that objection and the failed faster-door experiment.",
    "The access checklist required paired cues and a pause control. The persistent latch was a later response to a one-handed player.",
    "The record preserves one veteran waiting for a newcomer, not a broad test of lasting social effects.",
    "The assistant supplied ‘room to notice’; the revision log records Mara selecting it. Selection establishes review, not sole invention.",
    "Only three pairs played; a faulty controller and prior puzzle exposure are alternative explanations the draft explicitly retains.",
    "Mara restored the controller detail after shortening. Keeping the collaborator’s objection makes the polished account less one-sided.",
    "The next test changes whether partners can see each other. The proposed plan is recorded, but earlier wording is missing.",
  ];
  return [
    ...[
      [
        "production-latch",
        "The playtest note records Mara adding a persistent latch after a one-handed player asked for it; the earlier collaborator checklist did not include this change.",
      ],
      [
        "production-distinction",
        "Mara's own draft distinguishes completing a puzzle from solving it together before the assisted phrase was introduced.",
      ],
    ].map(([id, excerpt]) => ({
      id,
      excerpt,
      source: "Fictional draft record · Lantern House",
      capturedAt: artifact.capturedAt,
      relationship: "Authored demonstration record",
    })),
    ...production.map(([, , excerpt], i) => ({
      id: `production-${i + 1}`,
      source: "Fictional draft record · Lantern House",
      excerpt: i === 5 ? notebook[3][2] : excerpt,
      capturedAt: artifact.capturedAt,
      relationship:
        "An authored production history for this fictional reading; no real creator is being assessed.",
    })),
    ...context.map((excerpt, i) => ({
      id: `production-context-${i + 1}`,
      source: "Fictional notebook · context and limitations",
      excerpt,
      capturedAt: artifact.capturedAt,
      relationship: "Authored demonstration record",
    })),
    {
      id: "production-ghost",
      source: "Fictional assembly log",
      excerpt:
        "The guarantee was generated and inserted after Mara’s final review; the version log records no later review of that sentence.",
      capturedAt: artifact.capturedAt,
      relationship: "Authored demonstration record",
    },
    {
      id: "production-caution",
      source: "Fictional earlier draft",
      excerpt:
        "The earlier draft already distinguishes an invitation from a guarantee. The inserted universal claim conflicts with that explicit caution.",
      capturedAt: artifact.capturedAt,
      relationship: "Authored demonstration record",
    },
  ];
}
