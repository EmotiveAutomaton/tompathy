import type { Artifact } from "./model";
import type { GoalNode } from "./hierarchy";
import { sentences } from "./sentences";

/** Authored fixture interpretations, never generated from arbitrary page text. */
export function exampleHierarchy(
  artifact: Artifact,
  revised: boolean,
): GoalNode[] {
  const base = { maker: "maker-1", evidence: ["e1", "e2", "e3", "e4", "e5"] };
  const nodes: GoalNode[] = [
    {
      ...base,
      id: "purpose",
      label: "Make room for connection",
      description:
        "A possible governing purpose: show how modest design choices can invite people to stay. Hand-authored example, not established intent.",
      level: "document",
      regions: artifact.regions.map((r) => r.id),
    },
    {
      ...base,
      id: "story",
      parentId: "purpose",
      label: "Tell a design story",
      description:
        "Build an argument through noticing, trying and revising a small intervention.",
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
      regions: ["p6"],
    },
  ];
  const paragraphLabels = [
    "Notice hesitation",
    "Offer an invitation",
    "Show the iteration",
    revised ? "Explain the constraints" : "Make inclusion tangible",
    "Close without certainty",
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
      revised ? "Acknowledge the material brief" : "Name a considered material",
      revised ? "Describe the required seat" : "Show care in the details",
      "Anticipate a visitor’s needs",
      "Connect details to belonging",
    ],
    [
      "Bound the claim",
      "Offer one observed encounter",
      "Invite a modest beginning",
    ],
  ];
  artifact.regions.slice(1).forEach((r, i) => {
    const paragraphId = `paragraph-${i + 1}`,
      evidence = [`e${i + 1}`, ...(revised && i === 3 ? ["notebook"] : [])];
    nodes.push({
      ...base,
      evidence,
      id: paragraphId,
      parentId: i === 4 ? "limits" : "story",
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
        parentId: paragraphId,
        label: labels[i][j],
        description: `“${s.text}” — a possible proximal goal, supplied by the fictional example account.`,
        level: "sentence",
        regions: [r.id],
        span: { region: r.id, start: s.start, end: s.end },
      }),
    );
  });
  return nodes;
}
