import {
  makeArtifact,
  PacketSchema,
  type Packet,
  type ContextItem,
} from "./model";
import { exampleAttention } from "./attention";
import { exampleHierarchy } from "./example-hierarchy";
import { sentences } from "./sentences";
export const exampleText = [
  "A bench is an invitation",
  "The first thing we noticed was not where people sat. It was where they stopped. At the edge of the garden, visitors paused with their bags still on their shoulders, as if waiting for permission to stay.",
  "We could have added a sign. Instead, we moved one bench into the shade and turned it slightly toward the path. Nothing about it demanded a conversation. It simply made room for one.",
  "For two weeks, we returned at different hours. We counted pauses, sketched the paths people took, and listened when someone offered a comment. Our first arrangement was too close to the gate. We moved it again.",
  "The final bench is made from reclaimed cedar. Its corners are rounded, its seat a little higher than the old one. A walking stick can rest against either arm. These are small decisions, but small decisions decide who feels welcome.",
  "We do not know whether a bench can make a neighborhood kinder. We do know that on Thursday, two people who had never met sat down in the shade. For now, that is a useful place to begin.",
];
export const exampleContext: ContextItem = {
  id: "context-notebook",
  source: "Synthetic designer’s notebook",
  excerpt:
    "The site brief required reclaimed cedar and a raised seat. The first layout came from a standard park plan. Observations led us to change the position twice; the material and seat height were constraints, not our original choices.",
  retrievedAt: "2026-09-19T10:00:00.000Z",
  selected: true,
  lineage: "synthetic",
};
export async function createExample(
  source = "tompathy:example",
  revised = false,
): Promise<Packet> {
  const artifact = await makeArtifact(
    exampleText,
    source,
    "A bench is an invitation",
  );
  const evidence = exampleText.slice(1).map((excerpt, i) => ({
    id: `e${i + 1}`,
    source,
    excerpt,
    capturedAt: artifact.capturedAt,
    relationship:
      "Text compatible with this account; it does not establish the maker’s intent.",
  }));
  if (revised)
    evidence.push({
      id: "notebook",
      source: exampleContext.source,
      excerpt: exampleContext.excerpt,
      capturedAt: exampleContext.retrievedAt,
      relationship:
        "Creator-reported constraints offer an alternative to original design choices.",
    });
  const h = (
    id: string,
    kind: "goal" | "process" | "value",
    label: string,
    description: string,
    regions: string[],
    value: number | null,
    ev: string[],
    status: "hypothesis" | "unknown" | "creator-reported" = "hypothesis",
  ) => ({
    id,
    kind,
    label,
    description,
    makers: ["maker-1"],
    regions,
    status,
    support:
      value === null
        ? null
        : {
            value,
            scale: [0, 1],
            semantics: "relative",
            ...(kind === "goal" ? { candidateSet: "aims" } : {}),
            meaning:
              "Illustrative relative support, not a probability or calibrated estimate.",
          },
    evidence: ev,
    ...(id === "attention"
      ? {
          spans: ["p2", "p4"].map((region) => ({
            region,
            ...sentences(
              artifact.regions.find((r) => r.id === region)!.anchor.exact,
            )[0],
          })),
        }
      : {}),
    ...(id === "care" ? { decisionNodes: ["sentence-4-3"] } : {}),
    interpretation:
      kind === "goal"
        ? id === "invite"
          ? "governing-purpose"
          : "local-goal"
        : kind === "process"
          ? "historical-event"
          : id === "care"
            ? "value"
            : "preference",
  });
  const attention = exampleAttention(artifact);
  return PacketSchema.parse({
    schemaVersion: "1.4",
    currentAttention: attention.currentAttention,
    goalHierarchy: { nodes: exampleHierarchy(artifact, revised) },
    id: revised ? "bench-analysis-2" : "bench-analysis-1",
    revision: revised ? 2 : 1,
    artifact,
    provider: {
      id: "tompathy-example",
      method: "Hand-authored interaction fixture",
    },
    origin: "synthetic example",
    scope: {
      kind: revised ? "context" : "artifact",
      contextIds: revised ? [exampleContext.id] : [],
    },
    makers: [
      {
        id: "maker-1",
        label: "The garden designer",
        identity: "synthetic",
        relationship: "Fictional designer and author of this reflection",
      },
    ],
    hypotheses: [
      ...attention.hypotheses,
      h(
        "concrete",
        "goal",
        "Make it tangible",
        "Ground an abstract invitation in observable design choices.",
        [],
        0.53,
        ["e2", "e4"],
      ),
      h(
        "ordinary",
        "goal",
        "Reframe",
        "Suggest that an everyday object can carry a social purpose.",
        [],
        0.31,
        ["e1", "e5"],
      ),
      h(
        "reflection",
        "goal",
        "Reflection",
        "Leave the reader room to form their own judgment.",
        [],
        0.38,
        ["e5"],
      ),
      h(
        "attention",
        "goal",
        "Look closer",
        "Use a close observation to let the situation become visible.",
        ["p2", "p4"],
        0.24,
        ["e1", "e3"],
      ),
      h(
        "modesty",
        "goal",
        "Keep the claim modest",
        "Qualify what this small intervention can establish.",
        ["p3", "p6"],
        0.34,
        ["e2", "e5"],
      ),
      h(
        "invite",
        "goal",
        "Invite connection",
        "The writer may be making an everyday encounter feel possible.",
        ["p1", "p2", "p3", "p4", "p5", "p6"],
        0.88,
        ["e1", "e2", "e5"],
      ),
      h(
        "notice",
        "goal",
        "Help us notice",
        "Directing attention to quiet behavior before proposing a change.",
        ["p1", "p2", "p4"],
        0.62,
        ["e1", "e3"],
      ),
      h(
        "persuade",
        "goal",
        "Make a case",
        "The story may also make the design project feel worthwhile.",
        ["p1", "p2", "p3", "p5", "p6"],
        0.46,
        ["e2", "e5"],
      ),
      h(
        "test",
        "goal",
        "Test an assumption",
        "The writer may be showing how observation changed a decision.",
        ["p4"],
        0.91,
        ["e3"],
      ),
      h(
        "include",
        "goal",
        "Reduce barriers",
        "Making access tangible through the details of a seat.",
        ["p5"],
        revised ? 0.48 : 0.85,
        ["e4", ...(revised ? ["notebook"] : [])],
      ),
      h(
        "observe",
        "process",
        "Observe everyday life",
        "Attention to pauses and routes offers a possible starting point.",
        ["p1", "p2", "p3", "p4", "p5", "p6"],
        0.8,
        ["e1", "e3"],
      ),
      h(
        "reframe",
        "process",
        "Reframe the problem",
        "A place to pause becomes a question of invitation, rather than signage.",
        ["p1", "p2", "p3"],
        0.82,
        ["e2"],
      ),
      h(
        "iterate",
        "process",
        "Test & refine",
        "The described visits and second move support an iterative account.",
        ["p4"],
        0.92,
        ["e3"],
      ),
      h(
        "craft",
        "process",
        revised ? "Work within a brief" : "Design for inclusion",
        revised
          ? "The notebook attributes material and seat height to the brief."
          : "The details are compatible with attention to different visitors’ needs.",
        ["p5"],
        0.83,
        [revised ? "notebook" : "e4"],
        revised ? "creator-reported" : "hypothesis",
      ),
      h(
        "reflect",
        "process",
        "Reflect without closure",
        "The author may have selected and qualified a final observation while composing the reflection. The finished text alone cannot establish when this happened.",
        ["p6"],
        0.8,
        ["e5"],
      ),
      h(
        "convention",
        "process",
        "Adapt a familiar pattern",
        "A familiar design or editorial convention could produce the same text.",
        ["p1", "p2", "p3", "p4", "p5", "p6"],
        0.38,
        ["e2"],
      ),
      h(
        "history",
        "process",
        "Earlier experience",
        "No records identify the earlier events that shaped this work. Their timing and influence are unresolved.",
        ["p1", "p2", "p3", "p4", "p5", "p6"],
        null,
        [],
        "unknown",
      ),
      h(
        "care",
        "value",
        revised ? "Practical care" : "Care for others",
        "A possible concern for everyday comfort, limited to this fictional artifact.",
        [],
        revised ? 0.64 : 0.78,
        ["e2", "e4", ...(revised ? ["notebook"] : [])],
      ),
      h(
        "curiosity",
        "value",
        "Curiosity",
        "A possible preference for learning through observation.",
        [],
        0.64,
        ["e1", "e3"],
      ),
      ...[
        ["accessibility", "Access for everyone", 0.51, "e4"],
        ["adaptability", "Willingness to revise", 0.48, "e3"],
        ["stewardship", "Thoughtful use of materials", 0.44, "e4"],
        ["belonging", "Shared belonging", 0.4, "e2"],
        ["patience", "Patient observation", 0.36, "e1"],
      ].map(([id, label, value, evidence]) =>
        h(
          String(id),
          "value",
          String(label),
          `An illustrative recurring preference: ${String(label).toLowerCase()}.`,
          [],
          Number(value),
          [String(evidence)],
        ),
      ),
      h(
        "restraint",
        "value",
        "Restraint",
        "A possible preference for modest interventions and qualified claims.",
        [],
        0.55,
        ["e2", "e5"],
      ),
    ],
    alternatives: [
      {
        id: "aims",
        kind: "coexisting",
        members: [
          "invite",
          "notice",
          "persuade",
          "test",
          "include",
          "concrete",
          "ordinary",
          "reflection",
          "attention",
          "modesty",
        ],
        exhaustive: false,
      },
      {
        id: "routes",
        kind: "competing",
        members: ["observe", "convention"],
        exhaustive: false,
      },
    ],
    process: {
      interpretation: "historical-production",
      nodes: [
        "observe",
        "reframe",
        "iterate",
        "craft",
        "reflect",
        "convention",
        "history",
      ],
      edges: [
        {
          from: "observe",
          to: "reframe",
          kind: "enables",
          status: "hypothesis",
          relationship: "May inform the decision",
          evidence: ["e1", "e2"],
        },
        {
          from: "observe",
          to: "iterate",
          kind: "precedes",
          status: "creator-reported",
          relationship: "Reported before the later move",
          evidence: ["e3"],
        },
        {
          from: "iterate",
          to: "craft",
          kind: "order-unknown",
          status: "unknown",
          relationship: "Order unresolved",
          evidence: ["e3", "e4"],
        },
        {
          from: "craft",
          to: "reflect",
          kind: "related",
          status: "hypothesis",
          relationship: "Related; timing unknown",
          evidence: ["e4", "e5"],
        },
      ],
    },
    accounts: [
      {
        id: "account-observation",
        label: "Learning through observation",
        members: ["invite", "observe", "iterate", "curiosity"],
        explanation:
          "These hypotheses can form one compatible account. They are not independent measurements of the author.",
      },
      {
        id: "account-convention",
        label: "Adapting an existing brief",
        members: ["convention", "craft", "care"],
        explanation:
          "A brief or familiar pattern may explain the same choices; the notebook can change which decisions belong to this maker.",
      },
    ],
    documentContribution: {
      value: revised ? 0.55 : 0.7,
      quantity: "Synthetic support for consequential maker choices",
      explanation: revised
        ? "The notebook attributes material and height to the brief. Choosing placement remains a possible consequential contribution."
        : "Choosing to invite encounters by changing a bench may shape the whole artifact. This is an illustrative judgment, not a measured quantity of thought.",
      evidence: revised ? ["e2", "notebook"] : ["e2"],
    },
    estimates: artifact.regions.map((r, i) => ({
      region: r.id,
      contribution:
        i === 0
          ? null
          : {
              value: [0.6, 0.8, 0.7, 0.85, 0.65][i - 1],
              quantity: "Synthetic support for consequential maker choices",
              scale: "0–1",
              basis: "global-and-local",
              explanation:
                i === 4
                  ? "The material and height may be local choices or requirements from the brief. These scores are illustrative, not calibrated."
                  : "The document-wide choice supplies context; the described observation or intervention supplies local evidence. No arithmetic decomposition is asserted.",
              evidence: [`e${i}`],
            },
      uncertainty: {
        level: i === 4 ? "high" : "medium",
        meaning:
          "Illustrative uncertainty about the production account, independent of contribution.",
      },
    })),
    evidence,
    ...(revised
      ? {
          revisionOf: "bench-analysis-1",
          changeExplanation:
            "The notebook shows that material and seat height were requirements. “Design for inclusion” is replaced by “Work within a brief”; the values snapshot is explicitly revised.",
        }
      : {}),
  });
}
