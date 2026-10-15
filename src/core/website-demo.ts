import snapshot from "./art-snapshot.json" with { type: "json" };
import { artIntentRows } from "./art-intents";
import {
  PacketSchema,
  type Artifact,
  type Packet,
  type Hypothesis,
} from "./model";
import { sentences, regionSentences } from "./sentences";
import { websiteValues } from "./website-values";
import portfolio from "./portfolio-intents.json" with { type: "json" };
import type { GoalNode } from "./hierarchy";

const maker = "abraham-haskins";
const key = (s: string) =>
  s
    .toLowerCase()
    .replace(/\[\d+\]|[▶†]/g, "")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .trim();
const sourceRows = snapshot.blocks.map((b, i) => ({
  ...b,
  i,
  key: key(b.text),
  row: artIntentRows[i],
  sentences: sentences(b.text),
}));
const exactRows = new Map(sourceRows.map((b) => [b.key, b]));
const sentenceRows = new Map(
  sourceRows.flatMap((b) =>
    b.sentences.map(
      (s, j) => [key(s.text), { block: b, intent: b.row.intents[j] }] as const,
    ),
  ),
);
const homeRows: Record<string, [string, string, string]> = {
  "Human-AI Systems Lead": [
    "Position myself at the human-AI boundary",
    "Professional identity",
    "Human-AI coordination",
  ],
  "Lead Human Factors Engineer": [
    "Establish practical engineering responsibility",
    "Professional identity",
    "Usable systems",
  ],
  "Human Factors Psychologist": [
    "Ground the engineering in human behavior",
    "Professional identity",
    "Human understanding",
  ],
  "Building resilient systems through human understanding.": [
    "Make human understanding the basis of resilient systems",
    "Professional identity",
    "Resilience",
  ],
  "Abraham Haskins, PhD": [
    "Attach my identity and qualification to the work",
    "Professional identity",
    "Credibility",
  ],
  "Abraham is open to research partnerships, speaking engagements, and select consulting in human-AI systems and cognitive design.":
    [
      "Invite relevant collaboration without promising every kind of work",
      "Invite collaboration",
      "Selective partnerships",
    ],
  "Selected Works": [
    "Let concrete work substantiate the introduction",
    "Demonstrate range",
    "Evidence of competence",
  ],
  "Alaska Door Plug Investigations": [
    "Lead with consequential systems investigation",
    "Demonstrate range",
    "Safety investigation",
  ],
  "When complex systems fail, Cognitive and Systems Analysis can find the human root cause.":
    [
      "Connect systems analysis with understanding human causes of failure",
      "Demonstrate range",
      "Human causes",
    ],
  "Enterprise AI Tools": [
    "Show experience building tools for organizations",
    "Demonstrate range",
    "Practical AI",
  ],
  "Scaling validation through agentic workflows.": [
    "Present automation as a way to expand validation",
    "Demonstrate range",
    "Reliable scale",
  ],
  "Academic Rigor": [
    "Offer research depth alongside applied work",
    "Demonstrate range",
    "Research quality",
  ],
  "Deep research into Human-Autonomy Teaming.": [
    "Name the specific research problem behind the credentials",
    "Demonstrate range",
    "Human-autonomy teaming",
  ],
  "Teaming & Culture": [
    "Show attention to collaboration beyond tools",
    "Demonstrate range",
    "Team relationships",
  ],
  "Navigating complex dynamics - on and off the clock.": [
    "Connect workplace teamwork with broader social experience",
    "Demonstrate range",
    "Social complexity",
  ],
  "Advanced Interface Design": [
    "Make interface expertise a visible part of the portfolio",
    "Demonstrate range",
    "Interface craft",
  ],
  "Designing for high-stakes human-machine interaction.": [
    "Emphasize consequences rather than decorative interface polish",
    "Demonstrate range",
    "High-stakes decisions",
  ],
  "Home Projects": [
    "Leave room for self-directed making",
    "Demonstrate range",
    "Personal curiosity",
  ],
  "Side projects that blend passion with engineering.": [
    "Connect personal motivation with hands-on capability",
    "Demonstrate range",
    "Enjoying the work",
  ],
  "Compassion & Connection": [
    "Include care as part of the professional identity",
    "Invite collaboration",
    "Human connection",
  ],
  "Resilience through community and connection.": [
    "Ground resilience in relationships as well as systems",
    "Invite collaboration",
    "Community support",
  ],
};
const homeByKey = new Map(
  Object.entries(homeRows).map(([k, v]) => [key(k), v]),
);
const liveExtras = new Map(
  [
    [
      "Prompt: Demonstrate this effect by writing out a cold paragraph that drives readers to skim or skip ahead",
      "Disclose the instruction behind the deliberately cold example",
    ],
    [
      "Prompt: Explain the generation process of diffusion models using a Feynman-like explanation to signal processing, focusing on how vector averaging destroys the high-frequency signal of individual human intent.",
      "Show the requested analogy behind the generated diffusion explanation",
    ],
    [
      "Prompt: Summarize the rules for presenting ghost text intentionally to the reader.",
      "Reveal the instruction used to condense the ghost-text rules",
    ],
    ["Bibliography", "Make the supporting sources available for inspection"],
    ["Links", "Offer routes into the work beyond this essay"],
  ].map(([text, intent]) => [key(text), intent]),
);
const portfolioByKey = new Map(portfolio.entries.map((e) => [key(e.text), e]));
const projectHeadings: Record<string, string> = {
  "Root Cause Analysis & Systemic Redesign":
    "Introduce a case of preventing repeated system failure",
  "App Development & AI Consulting":
    "Connect building tools with advising on safe use",
  "Ph.D. Research & Experimental Design":
    "Make the research foundations visible",
  "AI Governance & Human Engineering Councils":
    "Explain how human concerns enter governance",
  "Adaptive UIs & Biometric Integration":
    "Introduce interfaces that respond to operator needs",
  "Personal Engineering & Side Projects":
    "Show what I choose to build without an assignment",
  "About Abraham": "Offer a personal context for the professional work",
};
const support = (value: number) => ({
  value,
  scale: [0, 1] as [number, number],
  semantics: "relative" as const,
  meaning:
    "Authored demo confidence and prominence, not a calibrated model output.",
});
function sourceBlock(text: string) {
  const normalized = key(text),
    exact = exactRows.get(normalized);
  if (exact) return exact;
  // Live KaTeX, linked citations and typography can alter plain-text extraction.
  // Require substantial overlap; unmatched text gets an explicitly provisional cue.
  if (normalized.length < 40) return undefined;
  const words = new Set(normalized.split(" "));
  let best: (typeof sourceRows)[number] | undefined,
    score = 0.72;
  for (const b of sourceRows) {
    if (
      b.key.length < normalized.length * 0.55 ||
      b.key.length > normalized.length * 1.8
    )
      continue;
    const other = new Set(b.key.split(" "));
    const overlap = [...words].filter((w) => other.has(w)).length;
    const similarity = (2 * overlap) / (words.size + other.size);
    if (similarity > score) {
      best = b;
      score = similarity;
    }
  }
  return best;
}
function branchFor(index: number) {
  if (index < 8 || index === 17)
    return ["trust", "Earn a fair hearing", true] as const;
  if (index >= 289 && index < 299)
    return ["invitation", "Invite a cultural experiment", true] as const;
  if (index >= 299)
    return ["formal", "Make the proposal testable", false] as const;
  if (index >= 236 && index < 285)
    return ["interface", "Make involvement readable", false] as const;
  if (index >= 198)
    return ["alignment", "Protect learning and align AI", false] as const;
  return ["explanation", "Explain art through intention", false] as const;
}
/** Attach the commissioned demonstration to this capture's exact regions/spans.
 * Never substitutes a saved webpage or calls a backend. */
export function createWebsiteDemo(artifact: Artifact, offline = false): Packet {
  const essay =
    offline || new URL(artifact.source).pathname.replace(/\/$/, "") === "/art";
  const nodes: GoalNode[] = [],
    hypotheses: Hypothesis[] = websiteValues(maker);
  const currentAttention: NonNullable<Packet["currentAttention"]> = [],
    ghostReadings: NonNullable<Packet["ghostReadings"]> = [];
  const evidence: Packet["evidence"] = [];
  const nodeMap = new Map<string, GoalNode>(),
    focusMap = new Map<string, string>();
  const ensure = (
    id: string,
    label: string,
    parentId?: string,
    level = "section",
  ) => {
    let node = nodeMap.get(id);
    if (!node) {
      node = {
        id,
        label: label.slice(0, 240),
        maker,
        description:
          "A one-off editorial interpretation for this website demo; not recovered production history.",
        level,
        regions: [],
        evidence: [],
        ...(parentId ? { parentId } : {}),
      };
      nodeMap.set(id, node);
      nodes.push(node);
    }
    return node;
  };
  const focus = (label: string) => {
    if (!focusMap.has(label)) {
      const id = `website-attention-${focusMap.size}`;
      focusMap.set(label, id);
      hypotheses.push({
        id,
        kind: "attention",
        interpretation: "current-attention",
        label,
        description: "An authored attentional cue for this demonstration.",
        makers: [maker],
        regions: [],
        status: "hypothesis",
        support: null,
        evidence: [],
      });
    }
    return focusMap.get(label)!;
  };
  let section = "Opening",
    lastIndex = 0;
  let exactCount = 0,
    provisionalCount = 0;
  artifact.regions.forEach((r, i) => {
    const b = essay ? sourceBlock(r.anchor.exact) : undefined;
    if (b) {
      lastIndex = b.i;
      if (b.type === "section" || b.type === "heading") section = b.text;
    }
    if (r.pageHint?.section) section = r.pageHint.section;
    const home = homeByKey.get(key(r.anchor.exact));
    const project = portfolioByKey.get(
      key(sentences(r.anchor.exact)[0]?.text ?? ""),
    );
    const branch = essay
      ? branchFor(b?.i ?? lastIndex)
      : ([
          home?.[1] ?? "Demonstrate range",
          home?.[1] ?? "Demonstrate range",
          home?.[1] === "Invite collaboration",
        ] as const);
    const root = ensure(
      `website-root-${branch[0]}`,
      branch[1],
      undefined,
      "purpose",
    );
    const parent = branch[2]
      ? root
      : ensure(
          `website-section-${branch[0]}-${key(section).slice(0, 100)}`,
          essay ? section : (home?.[1] ?? section),
          root.id,
          "section",
        );
    const short = r.anchor.exact
      .replace(/\[\d+\]/g, "")
      .trim()
      .split(/\s+/)
      .slice(0, 9)
      .join(" ");
    const purpose =
      b?.row.purpose ??
      home?.[0] ??
      projectHeadings[r.anchor.exact] ??
      (project
        ? `Explain ${project.section.toLowerCase()}`
        : `Present ${short}`);
    const paragraph = ensure(`art-passage-${i}`, purpose, parent.id, "passage");
    for (const n of new Set([root, parent, paragraph])) n.regions.push(r.id);
    const cues =
      b?.row.cues ??
      (project
        ? [project.cue, "Concrete experience", "Reader understanding"]
        : undefined) ??
      (home
        ? [home[2], "Reader orientation", "Professional credibility"]
        : [
            "Reader orientation",
            "Supporting context",
            "Communicating clearly",
          ]);
    const parts = regionSentences(r);
    parts.forEach((s, j) => {
      const known = essay ? sentenceRows.get(key(s.text)) : undefined;
      const intent =
        (r.pageHint?.unit === "group"
          ? "Offer sources, credentials and ways to make contact"
          : undefined) ??
        known?.intent ??
        (b && parts.length === b.sentences.length
          ? b.row.intents[j]
          : undefined) ??
        liveExtras.get(key(s.text)) ??
        portfolioByKey.get(key(s.text))?.intent ??
        projectHeadings[s.text] ??
        homeByKey.get(key(s.text))?.[0];
      if (intent) exactCount++;
      else provisionalCount++;
      const span = { region: r.id, start: s.start, end: s.end };
      const label =
        intent ??
        `${purpose}: ${s.text.split(/\s+/).slice(0, 7).join(" ")}`.slice(
          0,
          200,
        );
      const eid = `website-reading-${i}-${j}`;
      evidence.push({
        id: eid,
        source: artifact.source,
        capturedAt: artifact.capturedAt,
        excerpt: `Possible function: ${label}.`,
        relationship: "Authored demo interpretation of this exact sentence.",
      });
      const contextual = `website-context-${i}-${j}`;
      evidence.push({
        id: contextual,
        source: artifact.source,
        capturedAt: artifact.capturedAt,
        excerpt: `In this passage: ${purpose.charAt(0).toLowerCase() + purpose.slice(1)}.`,
        relationship:
          "Editorial context for the sentence, not independent corroboration.",
      });
      nodes.push({
        id: `art-sentence-${i}-${j}`,
        parentId: paragraph.id,
        maker,
        label,
        description: `${s.text}\n\nDemo reading: ${label}.`,
        level: "sentence",
        regions: [r.id],
        span,
        evidence: [eid],
      });
      const cueSet = [
        ...new Set([
          ...(known?.block.row.cues ?? cues),
          ...(b?.row.cues ?? []),
          essay
            ? lastIndex >= 299
              ? "Formal precision"
              : "Reader understanding"
            : "Human connection",
        ]),
      ];
      currentAttention.push({
        maker,
        span,
        items: cueSet.map((label, k) => ({
          hypothesis: focus(label),
          support: support(
            Math.max(
              0.17,
              0.86 - k * 0.18 + (((i * 7 + j * 11 + k * 3) % 13) - 6) * 0.018,
            ),
          ),
        })),
      });
      const declared =
        r.pageHint?.involvement ??
        (b
          ? b.mixed
            ? "unknown"
            : b.ghost === 100
              ? "original"
              : b.ghost === 95
                ? "edited"
                : b.ghost === 60
                  ? "curated"
                  : b.ghost === 0
                    ? "ghost"
                    : "unknown"
          : undefined);
      const kind = declared ?? (essay ? "edited" : "original");
      const declaration = `website-mark-${i}-${j}`;
      evidence.push({
        id: declaration,
        source: artifact.source,
        capturedAt: artifact.capturedAt,
        excerpt: declared
          ? `The page's own involvement marking is ${kind === "edited" ? "human-written with minor AI edits" : kind === "curated" ? "curated or synthesized" : kind === "ghost" ? "generated ghost text" : kind === "unknown" ? "mixed or unspecified" : "creator-written"}.`
          : "Involvement is a provisional demo choice for this unmarked passage.",
        relationship: declared
          ? "Observed creator disclosure; demo confidence is invented."
          : "Invented display data, not a production-history claim.",
      });
      ghostReadings.push({
        maker,
        span,
        kind,
        confidence:
          kind === "unknown"
            ? 0.36
            : Math.min(
                0.96,
                (declared ? 0.82 : 0.56) + ((i * 3 + j * 7) % 12) / 100,
              ),
        explanation: label,
        confidenceExplanation:
          "Invented confidence for the visual demo; this is not backend analysis.",
        evidence: [declaration, eid, contextual],
        ...(b?.prompt ? { prompt: b.prompt } : {}),
      });
    });
  });
  return PacketSchema.parse({
    schemaVersion: "1.6",
    id: `website-demo-${artifact.revision.slice(0, 16)}`,
    revision: 1,
    artifact,
    provider: {
      id: essay ? "tompathy-art-demo" : "tompathy-website-demo",
      method: `Website demo: ${exactCount} authored sentence interpretations; ${provisionalCount} provisional cues for unmatched text. Invented attention, confidence and value trajectories. No backend analysis.`,
    },
    origin: "imported",
    scope: { kind: "artifact", contextIds: [] },
    makers: [
      {
        id: maker,
        label: "Abraham Haskins",
        identity: "supplied",
        relationship:
          "Website creator; this demonstration was requested by the creator.",
      },
    ],
    hypotheses,
    currentAttention,
    ghostReadings,
    goalHierarchy: { nodes },
    alternatives: [],
    process: { interpretation: "functional", nodes: [], edges: [] },
    estimates: [],
    evidence,
  });
}
