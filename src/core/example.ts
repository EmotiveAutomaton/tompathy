import {
  makeArtifact,
  PacketSchema,
  type Packet,
  type ContextItem,
} from "./model";
import { exampleAttention } from "./attention";
import { exampleHierarchy } from "./example-hierarchy";
import {
  exampleContext,
  exampleEmphasis,
  exampleGhostReadings,
  productionEvidence,
} from "./example-production";
export { exampleContext, exampleEmphasis } from "./example-production";
import { sentences } from "./sentences";
export const exampleText = [
  "The door we stopped explaining",
  "The first thing we noticed was not where players died. It was where they waited. In our little cooperative game, two strangers stood on opposite sides of a greenhouse door, each holding a lantern, while the instruction I had polished for an afternoon faded politely from the screen.",
  "We could have made the instruction louder. Instead, we put warm light beyond the glass and let each player open half the latch. Nothing flashed when they got it wrong. The door simply waited for both of them, leaving enough time for one player to notice the other.",
  "For two evenings, I watched recordings without touching the build. A tester pointed out that I kept calling silence confusion when it sometimes meant someone was waiting for their partner. Our first revision opened the door too quickly. We slowed it down again, until a shared action had time to feel shared.",
  "The next build kept the lanterns bright without making them blink. Every sound cue had a visible companion, and either player could pause the room. One tester played with a single hand and asked for a latch that stayed pressed. These are small decisions, but small decisions decide who gets to remain part of the adventure.",
  "I cannot tell you that a gentler door makes a kinder game. I can tell you that on Thursday, a veteran player stopped racing ahead and waited beside someone learning the controls. For now, that is a useful place to begin, even if a useful beginning is not yet a design principle.",
  "Solving a puzzle is not quite the same as finding a way to solve it together. The pause leaves room to notice: a partner moving toward the wrong latch, a lantern changing hands, a small attempt at helping that the old instruction had covered up. This approach guarantees that every player feels equally included from the very first interaction.",
  "The test was much smaller than the story I wanted to tell. The recordings show three pairs of players, one unreliable controller, and a tester who already knew the puzzle from an earlier session. There is a difference between an invitation and a guarantee, and the difference matters most when a polished sentence makes it easy to forget.",
  "Before sending the draft, I shortened the explanation, then restored the awkward detail about the controller. My collaborator asked whether removing an instruction merely hid the work somewhere else. She was right: the timing, the light, and the forgiving latch were still teaching, just without borrowing the player's entire attention.",
  "Next week we will try a room where the partners cannot see each other. I am tempted to carry the same solution across unchanged, which is probably a good reason to watch first. The door can wait; I want to find out what the people on either side are actually trying to do.",
];
export async function createExample(
  source = "tompathy:example",
  revised = false,
): Promise<Packet> {
  const artifact = await makeArtifact(exampleText, source, exampleText[0]);
  artifact.regions.forEach(
    (r) => (r.emphasis = exampleEmphasis(r.id, r.anchor.exact)),
  );
  const evidence = exampleText.slice(1).map((excerpt, i) => ({
    id: `e${i + 1}`,
    source,
    excerpt,
    capturedAt: artifact.capturedAt,
    relationship:
      "Text compatible with this account; it does not establish the maker’s intent.",
  }));
  evidence.push(...productionEvidence(artifact));
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
    schemaVersion: "1.6",
    ghostReadings: exampleGhostReadings(artifact),
    currentAttention: attention.currentAttention,
    goalHierarchy: {
      nodes: exampleHierarchy(artifact, revised),
      orderUncertainGroups: [
        {
          id: "noticing-order",
          nodes: ["sentence-1-1", "sentence-1-2", "sentence-1-3"],
          explanation:
            "The supplied account does not establish the order of these noticing steps. Vertical position is not a timeline.",
          evidence: ["e1"],
        },
        {
          id: "invitation-order",
          nodes: [
            "sentence-2-1",
            "sentence-2-2",
            "sentence-2-3",
            "sentence-2-4",
          ],
          explanation:
            "These design choices may have developed together; their production order is uncertain.",
          evidence: ["e2"],
        },
      ],
    },
    id: revised ? "lantern-analysis-2" : "lantern-analysis-1",
    revision: revised ? 2 : 1,
    artifact,
    provider: {
      id: "tompathy-example",
      method: "Hand-written interaction fixture",
    },
    origin: "synthetic example",
    scope: {
      kind: revised ? "context" : "artifact",
      contextIds: revised ? [exampleContext.id] : [],
    },
    makers: [
      {
        id: "maker-1",
        label: "Mara Vale",
        identity: "synthetic",
        relationship:
          "Fictional cooperative-game designer and creator of this reflection",
      },
    ],
    hypotheses: [
      ...attention.hypotheses,
      h(
        "assist",
        "process",
        "Select assisted phrasing",
        "Choose room to notice from an assistant session; an automated assembly step later adds an unreviewed guarantee.",
        ["p7"],
        0.86,
        ["production-6"],
      ),
      h(
        "qualify",
        "process",
        "Challenge the guarantee",
        "Set the polished claim against the limits of three playtests.",
        ["p8"],
        0.87,
        ["e7"],
      ),
      h(
        "copyedit",
        "process",
        "Edit without adding claims",
        "Keep a controller detail and a collaborator’s objection after a shortening pass.",
        ["p9"],
        0.82,
        ["production-8"],
      ),
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
        "Making access tangible through a persistent latch.",
        ["p5"],
        revised ? 0.48 : 0.85,
        ["e4", ...(revised ? ["notebook"] : [])],
      ),
      h(
        "observe",
        "process",
        "Observe everyday life",
        "Attention to pauses and joint actions offers a possible starting point.",
        ["p1", "p2", "p3", "p4", "p5", "p6"],
        0.8,
        ["e1", "e3"],
      ),
      h(
        "reframe",
        "process",
        "Reframe the problem",
        "A place to pause becomes a question of invitation, rather than instruction volume.",
        ["p1", "p2", "p3"],
        0.82,
        ["e2"],
      ),
      h(
        "iterate",
        "process",
        "Test & refine",
        "The recordings and the slower second latch support an iterative account.",
        ["p4"],
        0.92,
        ["e3"],
      ),
      h(
        "craft",
        "process",
        revised ? "Work within a brief" : "Design for inclusion",
        revised
          ? "The notebook attributes sound cues and pause control to the brief."
          : "The details are compatible with attention to different players’ needs.",
        ["p5"],
        0.83,
        [revised ? "notebook" : "e4"],
        revised ? "creator-reported" : "hypothesis",
      ),
      h(
        "reflect",
        "process",
        "Reflect without closure",
        "The creator may have selected and qualified a final observation while composing the reflection. The finished text alone cannot establish when this happened.",
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
        ["stewardship", "Thoughtful use of tools", 0.44, "e4"],
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
        "assist",
        "qualify",
        "copyedit",
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
          from: "assist",
          to: "qualify",
          kind: "precedes",
          status: "creator-reported",
          relationship: "The creator bounds the playtest claim while drafting",
          evidence: ["production-6", "production-7"],
        },
        {
          from: "qualify",
          to: "copyedit",
          kind: "related",
          status: "hypothesis",
          relationship:
            "Draft revision and copy editing overlap; precise order unresolved",
          evidence: ["production-7", "production-8"],
        },
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
          "These hypotheses can form one compatible account. They are not independent measurements of the creator.",
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
      quantity: "Synthetic support for consequential creator choices",
      explanation: revised
        ? "The notebook attributes sound cues and pause control to the brief. Choosing latch timing remains a possible consequential contribution."
        : "Choosing to invite joint discovery by changing a cooperative door may shape the whole artifact. This is an illustrative judgment, not a measured quantity of thought.",
      evidence: revised ? ["e2", "notebook"] : ["e2"],
    },
    estimates: artifact.regions.map((r, i) => ({
      region: r.id,
      contribution:
        i === 0
          ? null
          : {
              value: [0.6, 0.8, 0.7, 0.85, 0.65, 0.4, 0.7, 0.8, 0.65][i - 1],
              quantity: "Synthetic support for consequential creator choices",
              scale: "0–1",
              basis: "global-and-local",
              explanation:
                i === 4
                  ? "The sound cues and pause control may be local choices or requirements from the brief. These scores are illustrative, not calibrated."
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
          revisionOf: "lantern-analysis-1",
          changeExplanation:
            "The notebook shows that sound cues and pause control were requirements. “Design for inclusion” is replaced by “Work within a brief”; the values snapshot is explicitly revised.",
        }
      : {}),
  });
}
