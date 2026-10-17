import { useId } from "react";
import type { Hypothesis } from "../core/model";
import { driveFor } from "../core/drive-systems";
const regions: Record<string, [number, number, string]> = {
  frontal: [41, 37, "Medial frontal cortex"],
  cingulate: [60, 35, "Anterior cingulate"],
  accumbens: [55, 62, "Nucleus accumbens"],
  amygdala: [57, 72, "Amygdala"],
  bnst: [65, 57, "Bed nucleus of the stria terminalis"],
  preoptic: [67, 67, "Preoptic area"],
  hypothalamus: [75, 66, "Hypothalamus"],
  thalamus: [79, 52, "Dorsomedial thalamus"],
  parafascicular: [88, 55, "Parafascicular thalamus"],
  vta: [89, 76, "Ventral tegmental area"],
  pag: [95, 68, "Periaqueductal gray"],
};
export function DriveBrain({
  h,
  title,
}: {
  h: Pick<Hypothesis, "label" | "valueCategory">;
  title?: string;
}) {
  const system = driveFor(h),
    id = useId().replace(/:/g, "");
  if (!system) return null;
  const nodes = system.regions.map((key) => regions[key]);
  const description = `${h.label}: schematic network, viewed through a left-facing head. Highlighted regions: ${nodes.map((n) => n[2]).join(", ")}. Approximate locations, not a map of this creator's brain.`;
  return (
    <figure className="drive-brain" title={title ?? description}>
      <svg viewBox="0 0 150 130" role="img" aria-labelledby={id}>
        <title id={id}>{title ?? description}</title>
        <g className="brain-anatomy">
          <path
            className="brain-head"
            d="M53 124 L53 106 Q37 107 32 100 L33 92 26 87 32 81 23 79 Q20 77 24 72 L33 59 Q29 53 31 44 C34 15 61 6 89 10 C120 12 139 35 133 66 Q132 83 114 98 L112 124"
          />
          <path
            className="brain-cortex"
            d="M37 48 C32 31 47 22 59 19 C71 12 98 16 110 24 C127 32 133 54 122 66 C114 76 98 75 88 72 C78 79 62 80 54 70 C43 71 35 60 37 48Z"
          />
          <g className="brain-folds">
            <path d="M39 43 Q48 37 43 30 M45 58 Q52 52 45 47 Q57 40 54 29 L60 22 M53 67 Q58 59 57 51 Q68 45 65 35 Q59 31 67 23 M72 19 Q79 25 74 32 M85 20 Q79 32 87 38 M99 23 Q91 30 96 41 M111 30 Q105 36 116 43 M123 47 Q112 47 115 57 M108 65 Q103 56 97 59 M76 73 Q74 62 64 62" />
            <path d="M48 48 C49 32 82 26 99 41 C106 46 107 56 101 61 M53 50 C55 40 77 36 89 43 Q96 48 94 57 M60 54 Q72 48 85 52" />
          </g>
          <path
            className="brain-stem"
            d="M87 72 Q88 83 100 93 L102 118 109 120 109 95 Q113 82 101 69"
          />
          <path
            className="brain-cerebellum"
            d="M106 76 C118 70 132 77 128 90 C124 99 112 99 104 91 Q99 82 106 76Z M106 81 Q119 77 127 83 M105 86 Q119 82 126 88 M108 91 Q118 88 123 93"
          />
        </g>
        <g className="brain-network">
          <path d={`M${nodes.map((n) => `${n[0]},${n[1]}`).join(" L")}`} />
          {nodes.map(([x, y, name]) => (
            <g key={name}>
              <circle className="brain-halo" cx={x} cy={y} r="5.5" />
              <circle cx={x} cy={y} r="2.7" />
            </g>
          ))}
        </g>
      </svg>
    </figure>
  );
}
