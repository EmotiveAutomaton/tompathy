// Shared with the small content adapter; keep manuscript and React out of it.
export type EssayKind = "goals" | "process" | "values";
export type EssayPage = EssayKind | "bibliography";
export const essayLabels: Record<EssayPage, string> = {
  goals: "Current attention",
  process: "Expertise (Previous attention)",
  values: "Core values",
  bibliography: "Bibliography",
};
export const isEssayKind = (value: unknown): value is EssayKind =>
  value === "goals" || value === "process" || value === "values";
export const isEssayPage = (value: unknown): value is EssayPage =>
  isEssayKind(value) || value === "bibliography";
