import { build } from "esbuild";
import { mkdir, copyFile, writeFile } from "node:fs/promises";
import { icons } from "./icons.mjs";
await mkdir("dist", { recursive: true });
await icons("dist");
await build({
  entryPoints: ["src/main.tsx"],
  bundle: true,
  outfile: "dist/panel.js",
  format: "esm",
  minify: true,
  sourcemap: true,
  target: "chrome116",
  define: { "process.env.NODE_ENV": '"production"' },
});
await build({
  entryPoints: ["src/background.ts", "src/content.ts"],
  bundle: true,
  outdir: "dist",
  format: "iife",
  target: "chrome116",
  sourcemap: true,
});
await copyFile("public/manifest.json", "dist/manifest.json");
const html =
  '<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ToMpathy — Maker Reader</title><link rel="stylesheet" href="panel.css"></head><body><div id="root"></div><script type="module" src="panel.js"></script></body></html>';
await writeFile("dist/panel.html", html);
await writeFile(
  "dist/example.html",
  html.replace(
    "<title>ToMpathy — Maker Reader</title>",
    "<title>A bench is an invitation</title>",
  ),
);
