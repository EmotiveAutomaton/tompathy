import { build } from "esbuild";
import {
  mkdir,
  copyFile,
  writeFile,
  readdir,
  readFile,
} from "node:fs/promises";
import { createHash } from "node:crypto";
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
for (const file of ["review.html", "review.css", "review.js"])
  await copyFile(`public/${file}`, `dist/${file}`);
const html =
  '<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ToMpathy - What&#39;s on the author&#39;s mind?</title><link rel="stylesheet" href="panel.css"></head><body><div id="root"></div><script type="module" src="panel.js"></script></body></html>';
await writeFile("dist/panel.html", html);
await writeFile("dist/snapshot.html", html);
await writeFile(
  "dist/example.html",
  html.replace(
    "<title>ToMpathy - What&#39;s on the author&#39;s mind?</title>",
    "<title>A bench is an invitation</title>",
  ),
);
const { verifyBuild } = await import("./check-build.mjs");
const hash = createHash("sha256");
for (const file of (await readdir("dist")).sort()) {
  if (file.endsWith(".map") || file === "build-info.json") continue;
  hash
    .update(file)
    .update("\0")
    .update(await readFile(path.join("dist", file)));
}
const { version } = JSON.parse(await readFile("dist/manifest.json", "utf8"));
await writeFile(
  "dist/build-info.json",
  JSON.stringify(
    { version, fingerprint: hash.digest("hex").slice(0, 12) },
    null,
    2,
  ),
);
await verifyBuild();
console.log(
  `\nBuild succeeded. ToMpathy ${version} is ready.\n\n  Review in Chrome: npm run chrome\n  Or double-click Review ToMpathy.cmd next time.\n  Manual Load unpacked: ${path.resolve("dist")}\n`,
);
