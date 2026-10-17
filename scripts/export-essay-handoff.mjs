// Produce a self-contained website handoff from the current authored sources.
import { build } from "esbuild";
import { readFile, writeFile, mkdir, copyFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import path from "node:path";
import { zipSync } from "fflate";
const root = "docs/website-essay-handoff";
await mkdir(`${root}/assets`, { recursive: true });
await mkdir(`${root}/source`, { recursive: true });
const assetPlugin = { name: "local-image-path", setup(b) {
  b.onLoad({ filter: /\.(png|jpe?g|webp|avif)$/ }, ({ path: file }) => ({ contents: `export default ${JSON.stringify(`./assets/${path.basename(file)}`)}`, loader: "js" }));
}};
await build({ stdin: { contents: 'export { essays, bibliography } from "./src/content/essays"; export { essayFigures } from "./src/content/essay-figures";', resolveDir: process.cwd() }, bundle: true, platform: "node", format: "cjs", outfile: ".local/essay-export.cjs", loader: { ".txt": "text" }, plugins: [assetPlugin] });
const { essays, bibliography, essayFigures } = createRequire(import.meta.url)(path.resolve(".local/essay-export.cjs"));
const hash = bytes => createHash("sha256").update(bytes).digest("hex");
const html = s => s.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll('"', "&quot;");
const cite = (kind, text) => text.replace(/\[(\d+)\]/g, (_, key) => {
  const ref = essays[kind].references[key];
  return `<sup><a href="${html(ref.href)}" title="${html(ref.text)}">${ref.number}</a></sup>`;
}).replace("[abrahamhaskins.org/art]", "[abrahamhaskins.org/art](https://abrahamhaskins.org/art/)");
const ordered = {}, manifest = [];
for (const [kind, essay] of Object.entries(essays)) {
  ordered[kind] = [];
  for (const [index, paragraph] of essay.paragraphs.entries()) {
    const figures = placement => essayFigures[kind].filter(f => paragraph.text.includes(f.anchor) && (f.placement ?? "after") === placement);
    ordered[kind].push(...figures("before").map(f => ({ type: "figure", ...f })), { type: "paragraph", id: `${kind}-${index+1}`, ...paragraph }, ...figures("after").map(f => ({ type: "figure", ...f })));
  }
  for (const figure of essayFigures[kind]) for (const image of figure.images ?? []) {
    const file = path.basename(image.src);
    await copyFile(`src/assets/essays/${file}`, `${root}/assets/${file}`);
    manifest.push({ file: `assets/${file}`, sha256: hash(await readFile(`${root}/assets/${file}`)), ...image });
  }
}
const sourceFiles = ["src/content/essays-source.txt", "src/content/essay-figures.ts", "src/content/essays.ts", "src/content/essay-kind.ts", "src/components/Essay.tsx", "src/components/SectionTitle.tsx", "src/components/DriveBrain.tsx", "src/components/PreferenceChart.tsx", "src/core/drive-systems.ts", "src/core/example-values.ts", "src/core/website-values.ts", "src/essay.css", "src/assets/essays/provenance.json", "src/assets/essays/NOTICES.txt"];
for (const file of sourceFiles) {
  const target = `${root}/source/${file}`;
  await mkdir(path.dirname(target), { recursive: true });
  await copyFile(file, target);
}
await writeFile(`${root}/content.json`, JSON.stringify({ essays, bibliography, figures: essayFigures, ordered, images: manifest }, null, 2) + "\n");
await copyFile("docs/CITATION_AUDIT_2026-10-17.md", `${root}/CITATION_AUDIT.md`);
await copyFile("docs/citation-url-audit-2026-10-17.json", `${root}/citation-url-audit.json`);
const guide = await readFile("docs/WEBSITE_ESSAY_HANDOFF_GUIDE.md", "utf8");
let markdown = `${guide}\n\n## Exact reading sequence\n\nThe following is the authored content. Paragraph and figure comments are placement metadata, not reader-facing copy. Citations use the same shared display numbers as ToMpathy.\n`;
for (const [kind, blocks] of Object.entries(ordered)) {
  markdown += `\n### ${essays[kind].title}\n\n`;
  for (const block of blocks) {
    if (block.type === "paragraph") markdown += `<!-- ${block.id} -->\n\n${cite(kind, block.text)}\n\n`;
    else {
      markdown += `<!-- Figure: ${JSON.stringify({ anchor: block.anchor, placement: block.placement ?? "after", large: !!block.large, portrait: !!block.portrait })} -->\n\n`;
      for (const image of block.images ?? []) markdown += `![${image.name}](${encodeURI(image.src).replaceAll("'", "%27")})\n\n<!-- ${image.generated ? "Grey #999 generated-image" : "Black #111 human-image"} border; ${image.uncropped ? "full natural aspect ratio" : block.portrait ? "4:5 crop" : "4:3 crop"}. -->\n\n`;
      if (block.diagram) markdown += `<!-- Insert the ${block.diagram} diagram from the included reference preview/source, without changing its geometry or introducing measurements. -->\n\n`;
      if (block.caption) markdown += `${cite(kind, block.caption)}\n\n`;
    }
  }
}
markdown += "\n## Shared bibliography metadata\n\nRender this only in the separate Bibliography view, not beneath each essay.\n\n";
markdown += bibliography.map(ref => `${ref.number}. [${ref.text.replaceAll("[", "\\[").replaceAll("]", "\\]")}](${ref.href})`).join("\n") + "\n";
await writeFile(`${root}/README.md`, markdown);
const entry = `import React, {useState} from 'react'; import {createRoot} from 'react-dom/client'; import {EssayDialog} from './src/components/Essay'; import {SectionTitle} from './src/components/SectionTitle'; function Preview(){const [kind,setKind]=useState(null);return <main className="handoff-home"><h1>ToMpathy essay reference</h1><p>Use the question marks to open the three essays.</p>{['goals','process','values'].map((k,i)=><div className="section-heading" key={k}><SectionTitle kind={k} onOpen={()=>setKind(k)}>{['Current attention','Expertise (Previous attention)','Core values'][i]}</SectionTitle></div>)}<button onClick={()=>setKind('bibliography')}>Bibliography</button>{kind&&<EssayDialog kind={kind} onClose={()=>setKind(null)} onNavigate={setKind}/>}</main>}createRoot(document.getElementById('root')).render(<Preview/>);`;
await build({ stdin: { contents: entry, resolveDir: process.cwd(), loader: "tsx" }, bundle: true, format: "iife", platform: "browser", outfile: `${root}/preview.js`, minify: true, loader: { ".txt": "text" }, plugins: [assetPlugin], define: { "process.env.NODE_ENV": '"production"' } });
await writeFile(`${root}/preview.html`, `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ToMpathy essay reference</title><link rel="stylesheet" href="preview.css"><style>:root{--surface:#fffefa;--ink:#273e39;--muted:#5f7068;--green:#42685b;--soft:#eff3ed;--bg:#fffefa;--line:#dce3dd;color:var(--ink);background:var(--bg)}*{box-sizing:border-box}body{margin:0;font:16px/1.6 "Segoe UI",sans-serif}.handoff-home{padding:48px;max-width:900px}button{font:inherit;cursor:pointer;color:var(--green)}.section-heading{margin:24px 0}.section-heading h2{font-size:18px}.section-question{border:0;background:transparent}.preference-chart{width:100%;height:auto}</style><div id="root"></div><script src="preview.js"></script></html>`);
const files = ["README.md", "content.json", "preview.html", "preview.js", "preview.css", "CITATION_AUDIT.md", "citation-url-audit.json", ...sourceFiles.map(f => `source/${f}`), ...manifest.map(i => i.file)];
await writeFile(`${root}/manifest.json`, JSON.stringify({ date: "2026-10-17", sourceSha256: hash(await readFile("src/content/essays-source.txt")), files: Object.fromEntries(await Promise.all(files.map(async f => [f, hash(await readFile(`${root}/${f}`))]))) }, null, 2) + "\n");
await writeFile(`${root}.zip`, zipSync(Object.fromEntries(await Promise.all([...files, "manifest.json"].map(async f => [`website-essay-handoff/${f}`, await readFile(`${root}/${f}`)]))), {level: 6}));
console.log(JSON.stringify({ root, paragraphs: Object.values(essays).reduce((n,e)=>n+e.paragraphs.length,0), images: manifest.length, references: bibliography.length }));
