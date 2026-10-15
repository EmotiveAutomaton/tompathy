import type { Hypothesis } from "./model";
// Region sets: Panksepp's WSU lecture table (see docs/CORE_VALUES_DESIGN.md).
// Coordinates are a schematic projection, not registered anatomy or tractography.
export const driveSystems = {
  SEEKING: {
    description: "Exploring possibilities and pursuing things that matter.",
    regions: ["vta", "accumbens", "hypothalamus", "pag", "frontal"],
  },
  RAGE: {
    description:
      "Mobilizing resistance when needs are blocked or boundaries are crossed.",
    regions: ["amygdala", "bnst", "hypothalamus", "pag"],
  },
  FEAR: {
    description: "Detecting danger and preparing to avoid or escape it.",
    regions: ["amygdala", "hypothalamus", "pag"],
  },
  LUST: {
    description: "Sexual attraction and the motivation to seek intimacy.",
    regions: ["amygdala", "bnst", "preoptic", "hypothalamus", "pag"],
  },
  CARE: {
    description: "Nurturing, protecting and responding to another's needs.",
    regions: ["cingulate", "bnst", "preoptic", "vta", "pag"],
  },
  Belonging: {
    description:
      "Seeking closeness and responding to separation or lost connection.",
    regions: ["cingulate", "bnst", "preoptic", "thalamus", "pag"],
  },
  PLAY: {
    description: "Enjoying playful social exchange and learning through it.",
    regions: ["thalamus", "parafascicular", "pag"],
  },
} as const;
export function driveFor(h: Hypothesis) {
  if (h.valueCategory !== "drive") return undefined;
  return driveSystems[h.label as keyof typeof driveSystems];
}
