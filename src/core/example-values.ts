import type { Hypothesis, Packet } from "./model";

// Authored illustration records; no scores or trajectories are inferred here.
const stories: Record<string, [string, string, string, string]> = {
  care: [
    "Everyday comfort",
    "Mara shortened a play session after a partner tired; she gave up another test run.",
    "She kept a pause control despite a collaborator's request for a faster release.",
    "She spent an evening adding the persistent latch for a one-handed tester.",
  ],
  curiosity: [
    "Room to discover",
    "Mara set aside a successful puzzle to try an unfamiliar cooperative mechanic.",
    "She stopped adding novelty when players could no longer tell what they had learned.",
    "She delayed a revision for two evenings to watch the recordings first.",
  ],
  accessibility: [
    "Ability to participate",
    "Mara replaced a timed input after a friend repeatedly missed it.",
    "She removed a redundant cue when it obscured the main signal.",
    "She reserved the final test session for a player using one hand.",
  ],
  adaptability: [
    "Freedom to revise",
    "Mara abandoned a favorite mechanic after a failed playtest.",
    "She froze a working build long enough to compare the alternatives.",
    "She restored the slower door after trying a faster one.",
  ],
  stewardship: [
    "Useful assistance",
    "Mara used a small tool to remove repetitive layout work.",
    "She rejected automatic hints that interrupted players' own discoveries.",
    "She kept one assistant phrase, then restored a detail the edit had dropped.",
  ],
  belonging: [
    "Shared participation",
    "Mara redesigned a puzzle so the second player had a consequential action.",
    "She removed forced cooperation from a quiet exploration room.",
    "She kept space for the veteran to wait beside the newcomer.",
  ],
  patience: [
    "Time to notice",
    "Mara postponed a fix to see whether players solved the difficulty themselves.",
    "She cut a long wait when it offered no useful information.",
    "She watched two evenings of recordings before changing the door.",
  ],
  restraint: [
    "Proportionate claims",
    "Mara narrowed a project claim after a colleague asked for evidence.",
    "She added a concrete observation to a draft that had become too guarded.",
    "She restored the controller caveat despite its awkwardness in the story.",
  ],
  autonomy: [
    "Freedom of choice",
    "A fictional play group traded a faster start for the ability to choose roles.",
    "The group asked for defaults when setup choices became burdensome.",
    "Participants kept an opt-out even though it complicated matchmaking.",
  ],
  fairness: [
    "Fair contribution",
    "A fictional group redistributed turns after one player dominated decisions.",
    "The group relaxed equal-turn rules when a novice wanted more guidance.",
    "Participants accepted slower progress to let every player contribute.",
  ],
  stability: [
    "Predictable footing",
    "A fictional studio deferred a release to resolve unpredictable controls.",
    "The studio accepted a small experiment once its rollback was easy.",
    "The team paid maintenance time to preserve reliable saved games.",
  ],
  playfulness: [
    "Room for play",
    "A fictional group abandoned a score target to explore a surprising interaction.",
    "The group removed an amusing distraction that blocked newcomers.",
    "Participants spent an extra session trying optional collaborative puzzles.",
  ],
};
export function demoPreference(
  id: string,
  global = false,
): Hypothesis["preferenceTrace"] {
  const story = stories[id];
  if (!story) return undefined;
  const variant = Object.keys(stories).indexOf(id) % 4;
  const trajectory = (x: number) =>
    0.5 + Math.sin(x * 5 * 1.15 + variant * 0.6) * 0.085 + x * 5 * 0.018;
  return {
    domain: story[0],
    start: "2021",
    end: "2026",
    points: [0, 0.2, 0.4, 0.6, 0.8, 1].map((x, i) => ({
      x,
      y: trajectory(x),
      uncertainty: (global ? 0.16 : 0.28) + (i % 2) * 0.025,
    })),
    observations: [
      {
        date: "2021",
        label: "Make room",
        explanation: story[1],
        from: [0.2, trajectory(0.23) - 0.13] as [number, number],
        to: [0.23, trajectory(0.23) - 0.025] as [number, number],
        cost: 0.45,
        horizon: "Days",
      },
      {
        date: "2024",
        label: "Ease back",
        explanation: story[2],
        from: [0.43, trajectory(0.5) + 0.12] as [number, number],
        to: [0.5, trajectory(0.5) + 0.025] as [number, number],
        cost: 0.25,
        horizon: "Weeks",
      },
      {
        date: "2026",
        label: "Return toward balance",
        explanation: story[3],
        from: [0.76, trajectory(0.86) - 0.14] as [number, number],
        to: [0.86, trajectory(0.86) - 0.025] as [number, number],
        cost: 0.8,
        horizon: "Months",
      },
    ],
  };
}

export function demoGlobalValues(
  packet: Packet | null,
  values: Hypothesis[],
): Hypothesis[] {
  if (
    packet?.origin !== "synthetic example" ||
    packet.provider.id !== "tompathy-example"
  )
    return [];
  const shared = values.slice(0, 4).map((h, i) => ({
    ...h,
    id: `global-${h.id}`,
    evidence: [],
    decisionNodes: [],
    description: `A synthetic Global illustration of ${h.label.toLowerCase()}; not a finding about people in general.`,
    support: { ...h.support!, value: [0.86, 0.92, 0.83, 0.89][i] },
    preferenceTrace: demoPreference(h.id, true),
  }));
  return [
    ...shared,
    ...["autonomy", "fairness", "stability", "playfulness"].map(
      (id, i): Hypothesis => ({
        id: `global-${id}`,
        kind: "value",
        label: [
          "Personal agency",
          "Fair contribution",
          "Reliable foundations",
          "Room for play",
        ][i],
        description: "Authored Global demo data; not a population estimate.",
        makers: [packet.makers[0].id],
        regions: [],
        status: "hypothesis",
        evidence: [],
        support: {
          value: [0.88, 0.94, 0.81, 0.9][i],
          scale: [0, 1],
          semantics: "relative",
          meaning: "Synthetic demo confidence; not calibrated.",
        },
        preferenceTrace: demoPreference(id, true),
      }),
    ),
  ];
}
