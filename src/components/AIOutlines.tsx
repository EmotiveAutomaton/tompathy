import { useId } from "react";
import { aiOutlineOpacity, aiOutlineWidth, type AIMark } from "../core/ai-attribution";

/** Paint above every cell. The union mask removes thick internal borders,
 * including partial shared edges, without changing the graph's hit targets. */
export function AIOutlines({ tiles, marks, width, height }: {
  tiles: {key: string; path: string; node: {id: string}}[];
  marks?: Map<string, AIMark>;
  width: number;
  height: number;
}) {
  const id = useId().replace(/:/g, "");
  const marked = tiles.flatMap(tile => {
    const mark = marks?.get(tile.node.id);
    return mark ? [{...tile, mark}] : [];
  });
  if (!marked.length) return null;
  return <g className="ai-outline-layer" pointerEvents="none" aria-hidden="true">
    <defs>
      <clipPath id={`${id}-union`} clipPathUnits="userSpaceOnUse">
        {marked.map(tile => <path key={tile.key} d={tile.path} />)}
      </clipPath>
      <mask id={`${id}-outside`} maskUnits="userSpaceOnUse" maskContentUnits="userSpaceOnUse"
        x={-10} y={-10} width={width + 20} height={height + 20} style={{maskType: "luminance"}}>
        <rect x={-10} y={-10} width={width + 20} height={height + 20} fill="white" />
        <g clipPath={`url(#${id}-union)`}>
          <rect x={-10} y={-10} width={width + 20} height={height + 20} fill="black" />
        </g>
      </mask>
    </defs>
    <g opacity={0.4}>
      {marked.map(tile => <path key={tile.key} className="ai-outline ai-outline-inner" d={tile.path}
        fill="none" stroke="#c43d42" strokeWidth={0.45} vectorEffect="non-scaling-stroke" strokeLinejoin="round" />)}
    </g>
    <g mask={`url(#${id}-outside)`}>
      {marked.map(tile => <path key={tile.key} className="ai-outline ai-outline-outer" d={tile.path}
        data-ai-node={tile.node.id} data-outline-width={aiOutlineWidth(tile.mark.involvement)}
        fill="none" stroke="#c43d42" strokeOpacity={aiOutlineOpacity(tile.mark.confidence)}
        // Only the outside half survives the mask, so double the requested width.
        strokeWidth={2 * aiOutlineWidth(tile.mark.involvement)}
        vectorEffect="non-scaling-stroke" strokeLinejoin="round" />)}
    </g>
  </g>;
}
