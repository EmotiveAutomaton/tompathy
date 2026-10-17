import type { Hypothesis } from "./model";
// Region sets: Panksepp's WSU lecture table (see docs/CORE_VALUES_DESIGN.md).
// Coordinates are a schematic projection, not registered anatomy or tractography.
export const driveSystems = {
  SEEKING: {
    description:
      "Panksepp's SEEKING system: exploring possibilities and pursuing things that matter. The need it serves is finding resources and opportunities.",
    regions: ["vta", "accumbens", "hypothalamus", "pag", "frontal"],
  },
  RAGE: {
    description:
      "Panksepp's RAGE system: mobilizing resistance when needs are blocked or boundaries are crossed. The need it serves is restoring agency.",
    regions: ["amygdala", "bnst", "hypothalamus", "pag"],
  },
  FEAR: {
    description:
      "Panksepp's FEAR system: detecting danger and preparing to avoid or escape it. The need it serves is safety.",
    regions: ["amygdala", "hypothalamus", "pag"],
  },
  LUST: {
    description:
      "Panksepp's LUST system: sexual attraction and the motivation to seek intimacy. The need it serves is sexual connection.",
    regions: ["amygdala", "bnst", "preoptic", "hypothalamus", "pag"],
  },
  CARE: {
    description:
      "Panksepp's CARE system: nurturing, protecting and responding to another's needs. It serves the need to care for those who depend on us.",
    regions: ["cingulate", "bnst", "preoptic", "vta", "pag"],
  },
  Belonging: {
    description:
      "Panksepp's PANIC/GRIEF system: the pre-made response to separation. The need it serves is belonging.",
    regions: ["cingulate", "bnst", "preoptic", "thalamus", "pag"],
  },
  PLAY: {
    description:
      "Panksepp's PLAY system. In this account, play narrows our uncertainty about how our own solutions work in unfamiliar situations. Done together, it brings people closer.",
    regions: ["thalamus", "parafascicular", "pag"],
  },
} as const;
export function driveFor(h: Pick<Hypothesis, "label" | "valueCategory">) {
  if (h.valueCategory !== "drive") return undefined;
  return driveSystems[h.label as keyof typeof driveSystems];
}
