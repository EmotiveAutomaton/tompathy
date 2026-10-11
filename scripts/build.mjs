import { build } from "esbuild";
import { mkdir, copyFile, writeFile } from "node:fs/promises";
import { icons } from "./icons.mjs";
import path from "node:path";
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
const { verifyBuild } = await import("./check-build.mjs");
await verifyBuild();
console.log(
  `\nBuild succeeded. ToMpathy is ready to load in Chrome.\n\n  Load unpacked: ${path.resolve("dist")}\n\nOpen chrome://extensions, choose Load unpacked, and select that folder.\nAlready loaded? Click Reload on the ToMpathy card, then refresh the source page.\nRun npm run testbed to open the local test page.\n`,
);
