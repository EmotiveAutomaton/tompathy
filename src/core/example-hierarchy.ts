import type { Artifact } from "./model";
import type { GoalNode } from "./hierarchy";
import { sentences } from "./sentences";

/** Written fixture interpretations, never generated from arbitrary page text. */
export function exampleHierarchy(
  artifact: Artifact,
  revised: boolean,
): GoalNode[] {
  const base = { maker: "maker-1", evidence: ["e1", "e2", "e3", "e4", "e5"] };
  const nodes: GoalNode[] = [
    {
      ...base,
      id: "purpose",
      label: "Make room for discovery",
      description:
        "A possible governing purpose: show how cooperative design can invite players to notice each other. Hand-written example, not established intent.",
      level: "document",
      regions: artifact.regions.map((r) => r.id),
    },
    {
      ...base,
      id: "story",
      parentId: "purpose",
      label: "Tell a design story",
      description:
        "Build an argument through noticing, trying and revising a shared game mechanic.",
      level: "section",
      regions: ["p2", "p3", "p4", "p5"],
    },
    {
      ...base,
      id: "limits",
      parentId: "purpose",
      label: "Leave room for doubt",
      description: "Qualify the claim and close with a concrete encounter.",
      level: "section",
      regions: ["p6", "p8", "p10"],
    },
  ];
  nodes.push(
    {
      ...base,
      id: "draft",
      level: "section",
      parentId: "purpose",
      label: "Turn experience into an essay",
      description:
        "Select language, invite a challenge, then edit without losing the troublesome details.",
      regions: ["p7", "p9"],
      evidence: ["production-6", "production-8"],
    },
    {
      ...base,
      id: "editing",
      level: "section",
      parentId: "draft",
      label: "Revise without erasing friction",
      description:
        "The copy-edit pass shortened the account; Mara restored the controller detail and kept the collaborator’s objection.",
      regions: ["p9"],
      evidence: ["production-8"],
    },
    {
      ...base,
      id: "assembly",
      level: "document",
      label: "Complete automated assembly",
      description:
        "A later tool step inserted a guarantee after review. This is a recorded tool operation, not an inferred creator intention.",
      regions: ["p7"],
      evidence: ["production-ghost"],
    },
    {
      ...base,
      id: "next-test",
      level: "section",
      label: "Keep learning from play",
      description:
        "A separate practical aim survives the essay: test partners who cannot see one another before reusing the door mechanism.",
      regions: ["p10"],
      evidence: ["production-9"],
    },
  );
  const paragraphLabels = [
    "Notice hesitation",
    "Offer an invitation",
    "Show the iteration",
    revised ? "Explain the constraints" : "Make inclusion tangible",
    "Close without certainty",
    "Shape an assisted draft",
    "Question the polished claim",
    "Keep the awkward detail",
    "Watch before repeating",
  ];
  const labels = [
    ["Shift our attention", "Notice the pauses", "Make hesitation visible"],
    [
      "Consider a simple fix",
      "Reframe the invitation",
      "Avoid demanding contact",
      "Make space for encounter",
    ],
    [
      "Show sustained attention",
      "Make observation concrete",
      "Admit a failed attempt",
      "Show willingness to revise",
    ],
    [
      revised ? "Acknowledge the access brief" : "Avoid a flashing cue",
      revised ? "Describe the shared checklist" : "Pair sound and vision",
      "Anticipate a player’s needs",
      "Connect details to belonging",
    ],
    [
      "Bound the claim",
      "Offer one observed encounter",
      "Invite a modest beginning",
    ],
    [
      "Separate solo and shared discovery",
      "Select room to notice",
      "No reviewed creator choice",
    ],
    [
      "Bound the scale of the test",
      "Expose the sample limits",
      "Separate invitation from guarantee",
    ],
    [
      "Keep a troublesome detail",
      "Include a collaborator’s objection",
      "Reframe what teaching means",
    ],
    [
      "Introduce a different problem",
      "Resist copying the solution",
      "Watch the players first",
    ],
  ];
  artifact.regions.slice(1).forEach((r, i) => {
    const paragraphId = `paragraph-${i + 1}`,
      evidence = [`e${i + 1}`, ...(revised && i === 3 ? ["notebook"] : [])];
    nodes.push({
      ...base,
      evidence,
      id: paragraphId,
      parentId:
        i === 7
          ? "editing"
          : i === 5
            ? "draft"
            : [4, 6, 8].includes(i)
              ? "limits"
              : "story",
      label: paragraphLabels[i],
      description: `A possible role for this paragraph: ${paragraphLabels[i].toLowerCase()}. Grounded in the quoted passage, with alternatives still possible.`,
      level: "paragraph",
      regions: [r.id],
    });
    sentences(r.anchor.exact).forEach((s, j) =>
      nodes.push({
        ...base,
        evidence,
        id: `sentence-${i + 1}-${j + 1}`,
        parentId: i === 5 && j === 2 ? "assembly" : paragraphId,
        label: labels[i][j],
        description:
          i === 5 && j === 2
            ? "No reviewed creator choice is supplied for this generated insertion. Its surrounding paragraph provides context, not evidence of an intended claim."
            : `“${s.text}” — a possible proximal goal, supplied by the fictional example account.`,
        level: "sentence",
        regions: [r.id],
        span: { region: r.id, start: s.start, end: s.end },
      }),
    );
  });
  // A second possible end stops one tier earlier. Shared subgoals can lead
  // toward either end, so this is a DAG rather than two unrelated pictures.
  nodes.push({
    ...base,
    id: "practical-care",
    label: "Keep play accessible",
    description:
      "A second possible end: accessible play may matter independently of the broader social story. A written stress-test branch.",
    regions: ["p4", "p5"],
  });
  for (const id of ["paragraph-3", "paragraph-4"]) {
    const n = nodes.find((n) => n.id === id)!;
    n.parentIds = [n.parentId!, "practical-care"];
    delete n.parentId;
  }
  const next = nodes.find((n) => n.id === "paragraph-9")!;
  next.parentIds = [next.parentId!, "next-test"];
  delete next.parentId;
  return nodes;
}
