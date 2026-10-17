import manuscript from "./essays-source.txt?raw";
import { essayFigures, figuresFor } from "./essay-figures";

import type { EssayKind } from "./essay-kind";
export {
  essayLabels,
  isEssayKind,
  isEssayPage,
  type EssayKind,
  type EssayPage,
} from "./essay-kind";

export type EssayReference = { text: string; href: string; number: number };
export type EssayParagraph = { text: string; notes: string[] };
export type Essay = {
  title: string;
  paragraphs: EssayParagraph[];
  references: Record<string, EssayReference>;
};

// Local manuscript keys stay editable; display numbers are shared across essays.
export function parseEssays(source: string): Record<EssayKind, Essay> {
  const essays: Record<EssayKind, Essay> = {
    goals: { title: "Current Attention", paragraphs: [], references: {} },
    process: {
      title: "Expertise (Previous Attention)",
      paragraphs: [],
      references: {},
    },
    values: { title: "Core Values", paragraphs: [], references: {} },
  };
  let kind: EssayKind = "goals",
    inReferences = false;
  for (const line of source.replace(/^\uFEFF/, "").split(/\r?\n/)) {
    if (!line.trim() || /^_+$/.test(line)) continue;
    if (line === "References") {
      inReferences = true;
      continue;
    }
    const heading = line.replace(/^-/, "").replace(/:$/, "");
    const match = (Object.keys(essays) as EssayKind[]).find(
      (k) => essays[k].title === heading,
    );
    if (match) {
      kind = match;
      continue;
    }
    if (inReferences) {
      const ref = line.match(/^(\d+)\.\s+(.+)$/);
      if (!ref) throw Error(`Unrecognized essay reference: ${line}`);
      const target = ref[2].trim().split(/\s+/).at(-1)!;
      const href = target.startsWith("doi:")
        ? `https://doi.org/${target.slice(4)}`
        : target.startsWith("arXiv:")
          ? `https://arxiv.org/abs/${target.slice(6)}`
          : target.startsWith("https://")
            ? target
            : `https://${target}`;
      if (new URL(href).protocol !== "https:")
        throw Error("Invalid reference URL");
      essays[kind].references[ref[1]] = { text: ref[2], href, number: 0 };
    } else {
      const notes: string[] = [];
      const text = line
        .replace(/\[([^\]]+)\]/g, (whole, inner: string) => {
          if (/^\d+$/.test(inner) || inner === "abrahamhaskins.org/art")
            return whole;
          notes.push(inner);
          return "";
        })
        .replace(/ {2,}/g, " ")
        .replace(/ +([.,;:!?])/g, "$1")
        .trim();
      if (text) essays[kind].paragraphs.push({ text, notes });
    }
  }
  for (const essay of Object.values(essays)) {
    for (const paragraph of essay.paragraphs) {
      for (const [, number] of paragraph.text.matchAll(/\[(\d+)\]/g))
        if (!essay.references[number])
          throw Error(`Missing citation ${essay.title}: ${number}`);
    }
  }
  return essays;
}

export const essays = parseEssays(manuscript);

export const bibliography: EssayReference[] = [];
const bySource = new Map<string, EssayReference>();
for (const kind of Object.keys(essays) as EssayKind[]) {
  const essay = essays[kind];
  for (const figure of essayFigures[kind]) {
    if (
      essay.paragraphs.filter((p) => p.text.includes(figure.anchor)).length !==
      1
    )
      throw Error(
        `Ambiguous or missing figure anchor: ${kind}: ${figure.anchor}`,
      );
  }
  const cite = (text: string) => {
    for (const [, key] of text.matchAll(/\[(\d+)\]/g)) {
      const ref = essay.references[key];
      if (!ref) throw Error(`Missing citation ${kind}: ${key}`);
      const canonical = ref.href.replace(/\/$/, "");
      const previous = bySource.get(canonical);
      if (previous) ref.number = previous.number;
      else {
        ref.number = bibliography.length + 1;
        bibliography.push(ref);
        bySource.set(canonical, ref);
      }
    }
  };
  for (const paragraph of essay.paragraphs) {
    figuresFor(kind, paragraph.text, "before").forEach((f) =>
      cite(f.caption ?? ""),
    );
    cite(paragraph.text);
    figuresFor(kind, paragraph.text, "after").forEach((f) =>
      cite(f.caption ?? ""),
    );
  }
}
