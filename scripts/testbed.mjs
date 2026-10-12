import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
await mkdir(".local", { recursive: true });
await build({
  entryPoints: ["src/core/example.ts"],
  bundle: true,
  platform: "node",
  format: "esm",
  outfile: ".local/testbed-generator.mjs",
});
const { createExample, exampleText, exampleContext } =
  await import("../.local/testbed-generator.mjs");
const source = "http://127.0.0.1:5173/testbed.html";
const packet = await createExample(source);
const escape = (s) =>
  s.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll('"', "&quot;");
await writeFile("public/testbed-result.json", JSON.stringify(packet, null, 2));
await writeFile(
  "public/testbed-revision.json",
  JSON.stringify(await createExample(source, true), null, 2),
);
await writeFile("public/testbed-notebook.txt", exampleContext.excerpt);
await writeFile(
  "public/testbed.html",
  `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="author" content="The garden designer"><title>A bench is an invitation · ToMpathy testbed</title><style>
body{margin:0;background:#f7f8f5;color:#273e39;font:16px/1.75 system-ui}header,article,footer{max-width:760px;margin:auto;padding:28px}header{border-bottom:1px solid #dce3dd;font-size:13px}h1{font:42px/1.2 Georgia,serif}article p{font:20px/1.8 Georgia,serif;margin:32px 0}a{color:#42685b}nav{display:flex;flex-wrap:wrap;gap:20px}small{color:#5f7068}footer{border-top:1px solid #dce3dd;font-size:13px}details{margin-top:14px}code{font-size:12px}
</style></head><body><header><strong>ToMpathy · local testbed</strong><p>A fictional author and hand-authored results. No live inference and no real person is analyzed.</p><nav><a download href="testbed-result.json">Download first account</a><a download href="testbed-revision.json">Download revised account</a><a href="testbed-notebook.txt">Read the notebook</a><a href="/">Design preview</a></nav><details><summary>How to try it</summary><ol><li>Load the <code>dist</code> folder in Chrome’s Extensions page.</li><li>Click ToMpathy in the toolbar while this page is active.</li><li>Choose Options → Import and load the first account downloaded above.</li><li>Hover the article, pin a passage, and inspect evidence. Values remain fixed.</li><li>Use the separate Development tools example from the Review desk to explore context revisions and earlier accounts.</li></ol><p>These files match this page at <code>${source}</code>. The built-in example has a different source identity.</p></details></header>
<article><h1>${escape(exampleText[0])}</h1><div data-tompathy-ui><small>By The garden designer · Fictional author</small></div>${exampleText
    .slice(1)
    .map((t) => `<p>${escape(t)}</p>`)
    .join("")}</article>
<footer><strong>Next: a public author</strong><p><a href="https://simonwillison.net/2022/May/4/datasette-lite/">Simon Willison’s Datasette Lite article</a> · <a href="https://github.com/simonw/datasette-lite">Linked GitHub project</a></p><p>Public pages can be captured and exported. These synthetic result files only match the fictional article above.</p></footer></body></html>`,
);
console.log("Testbed prepared: http://127.0.0.1:5173/testbed.html");
