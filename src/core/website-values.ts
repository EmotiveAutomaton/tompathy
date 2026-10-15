import type { Hypothesis, Packet } from "./model";

// Seven channels follow Panksepp; PANIC/GRIEF is displayed as Belonging. Combining them with constructed
// values is this prototype's design, not a claim that the two theories agree.
const drives = [
  [
    "SEEKING",
    "Exploration",
    "Follow an unresolved question",
    "Compare an awkward counterexample",
    "Keep the empirical questions open",
  ],
  [
    "RAGE",
    "Resistance",
    "Push back against erased agency",
    "Turn a complaint into a design constraint",
    "Direct opposition toward a workable alternative",
  ],
  [
    "FEAR",
    "Protection",
    "Notice a possible loss of human connection",
    "Make the uncertainty concrete",
    "Look for a preventative intervention",
  ],
  [
    "LUST",
    "Attraction",
    "Reserve space for an appetitive signal",
    "Keep the unsupported interpretation weak",
    "Leave the channel available without inventing a personal episode",
  ],
  [
    "CARE",
    "Nurturance",
    "Consider the reader's cognitive effort",
    "Preserve access to another person's choices",
    "End the proposal with kindness",
  ],
  [
    "Belonging",
    "Connection and loss",
    "Imagine losing a meaningful audience",
    "Notice the cost of failed connection",
    "Seek a way to reconnect creators and readers",
  ],
  [
    "PLAY",
    "Playfulness",
    "Try a deliberately silly analogy",
    "Use a meme to release tension",
    "Invite experimentation with the interface",
  ],
] as const;
const constructed = [
  [
    "Intellectual humility",
    "Knowing what is missing",
    "Admit that a model is simplified",
    "Give an opposing interpretation room",
    "Specify a result that could defeat a claim",
  ],
  [
    "Protective compassion",
    "Other people's capacity",
    "Notice the effort required to understand someone",
    "Design a gentler reading experience",
    "Treat kindness as part of the goal",
  ],
  [
    "Craft pride",
    "Deliberate making",
    "Find satisfaction in a precise explanation",
    "Revise a detail after feedback",
    "Make the method visible in the artifact",
  ],
  [
    "Social acceptance",
    "Shared participation",
    "Look for a shared reference",
    "Make room for an unfamiliar perspective",
    "Invite the reader into the work",
  ],
  [
    "Awe",
    "Expanded possibility",
    "Encounter an unexpectedly rich solution",
    "Allow surprise to reorganize the account",
    "Keep some of the original wonder",
  ],
  [
    "Anticipatory hope",
    "A workable future",
    "Imagine a beneficial outcome",
    "Translate possibility into a small action",
    "Invite others to try it",
  ],
  [
    "Moral indignation",
    "Preventable harm",
    "Notice an avoidable cost",
    "Separate a person from a damaging practice",
    "Propose accountability without losing nuance",
  ],
  [
    "Embarrassment",
    "Being seen imperfectly",
    "Acknowledge an awkward opening",
    "Keep a revealing human detail",
    "Trade polish for a clearer relationship",
  ],
  [
    "Gratitude",
    "Recognized help",
    "Notice another person's contribution",
    "Name what their help changed",
    "Make the credit visible",
  ],
  [
    "Nostalgia",
    "Continuity",
    "Recall a formative example",
    "Connect old practices to a new question",
    "Preserve a useful piece of the past",
  ],
  [
    "Epistemic disgust",
    "Boundaries of influence",
    "Notice a misleading signal",
    "Pause before adopting its implications",
    "Seek clearer grounds for trust",
  ],
  [
    "Shared purpose",
    "Coordinated effort",
    "Find a goal others can recognize",
    "Make the proposed contribution concrete",
    "Leave room for a different route",
  ],
  [
    "Tenderness",
    "Gentle attention",
    "Notice a small vulnerability",
    "Reduce an unnecessary burden",
    "Keep care present in the final wording",
  ],
  [
    "Creative delight",
    "Unexpected expression",
    "Try an unusual form",
    "Discover an expressive possibility",
    "Share the experiment without demanding agreement",
  ],
  [
    "Responsibility",
    "Consequences",
    "Consider who bears the cost",
    "Add a constraint that protects them",
    "Follow the implication beyond the immediate artifact",
  ],
  [
    "Earned confidence",
    "Trust in a method",
    "Start with an uncertain proposal",
    "Compare it against a hard case",
    "Retain confidence only where the test supports it",
  ],
  [
    "Regret",
    "Repair",
    "Recognize an earlier shortcoming",
    "Describe what could have been done differently",
    "Turn that comparison into a revision",
  ],
  [
    "Solidarity",
    "Mutual support",
    "Recognize a shared difficulty",
    "Connect separate experiences",
    "Offer a way to act together",
  ],
] as const;

const workObservations = [
  [
    "Try a difficult art example rather than a tidy definition.",
    "Connect the example to the intention behind it.",
    "End with questions that could test the idea.",
  ],
  [
    "Object to treating every output as equivalent.",
    "Turn that objection into a design requirement.",
    "Offer a concrete alternative to the practice.",
  ],
  [
    "Raise the possibility of losing meaningful human signals.",
    "Make that risk visible through an example.",
    "Propose a way to preserve those signals.",
  ],
  [
    "No sexual motivation is evident in this work.",
    "Leave this channel weakly supported.",
    "Keep the placeholder available for visual review.",
  ],
  [
    "Explain a difficult idea through familiar examples.",
    "Consider the reader's ability to follow the argument.",
    "Close by making kindness an explicit aim.",
  ],
  [
    "Address the reader as another person.",
    "Use shared cultural references to build connection.",
    "Invite a continuing conversation about the proposal.",
  ],
  [
    "Introduce a deliberately playful analogy.",
    "Use an unexpected image to release tension.",
    "Invite experimentation with the proposed interface.",
  ],
  [
    "Describe the model as a simplification.",
    "Give a counterexample serious attention.",
    "Suggest an outcome that would challenge the model.",
  ],
  [
    "Notice what is lost when a person's choices are obscured.",
    "Protect the possibility of understanding someone.",
    "Make care part of the proposed design.",
  ],
  [
    "Start from an uncertain but promising idea.",
    "Test it against the essay's difficult cases.",
    "Separate the promising proposal from established evidence.",
  ],
];
const definitions: Record<string, string> = {
  "Intellectual humility":
    "Leaving room to be wrong, learn and revise an explanation.",
  "Protective compassion":
    "Taking another person's vulnerability seriously and trying to reduce harm.",
  "Craft pride": "Finding satisfaction in thoughtful, deliberate work.",
  "Earned confidence":
    "Trust that grows through evidence and survives a difficult test.",
};

export function websiteValues(
  maker: string,
  global = false,
  currentWork = false,
): Hypothesis[] {
  return [
    ...drives,
    ...(currentWork
      ? [constructed[0], constructed[1], constructed[15]]
      : constructed.slice(0, global ? constructed.length : 3)),
  ].map((row, i) => {
    const value = currentWork
      ? [0.91, 0.37, 0.58, 0.08, 0.79, 0.62, 0.68, 0.84, 0.76, 0.7][i]
      : global
        ? 0.48 + ((i * 13) % 43) / 100
        : [0.86, 0.42, 0.65, 0.14, 0.83, 0.49, 0.71, 0.77, 0.81, 0.74][i];
    const trajectory = (x: number) =>
      0.44 +
      0.12 * Math.sin(x * 4 + i * 0.43 + (currentWork ? 0.9 : 0)) +
      x * 0.09;
    return {
      id: `${currentWork ? "work" : global ? "global" : "creator"}-website-value-${i}`,
      kind: "value",
      interpretation: "preference",
      valueCategory: i < 7 ? "drive" : "constructed",
      label: row[0],
      description: definitions[row[0]] ?? `${row[2]}. ${row[4]}.`,
      makers: [maker],
      regions: [],
      status: "hypothesis",
      evidence: [],
      support: {
        value,
        scale: [0, 1],
        semantics: "relative",
        meaning:
          "Invented demo confidence, used to exercise the display; not calibrated.",
      },
      preferenceTrace: {
        domain: row[1],
        start: "Earlier life",
        end: "Present",
        points: [0, 0.2, 0.4, 0.6, 0.8, 1].map((x, j) => ({
          x,
          y: trajectory(x),
          uncertainty:
            (currentWork ? 0.29 : global ? 0.18 : 0.25) + (j % 2) * 0.02,
        })),
        observations: [0, 1, 2].map((j) => {
          const x = [0.22, 0.48, 0.76][j],
            direction = j === 1 ? 1 : -1;
          return {
            date: ["Draft", "Review", "Revision"][j],
            label: row[j + 2],
            explanation: currentWork ? workObservations[i][j] : row[j + 2],
            from: [
              x - 0.018 * (j + 1),
              trajectory(x) + direction * (0.105 + j * 0.015),
            ] as [number, number],
            to: [x, trajectory(x) + direction * 0.025] as [number, number],
            cost: [0.35, 0.56, 0.7][j],
            horizon: ["Exploration", "Reconsideration", "Integration"][j],
          };
        }),
      },
    };
  });
}
export const isWebsitePacket = (packet: Packet | null) =>
  packet?.provider.id === "tompathy-art-demo" ||
  packet?.provider.id === "tompathy-website-demo";
