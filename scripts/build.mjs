import { build } from "esbuild";
import {
  mkdir,
  copyFile,
  writeFile,
  readdir,
  readFile,
  unlink,
} from "node:fs/promises";
import { createHash } from "node:crypto";
import { icons } from "./icons.mjs";
import path from "node:path";
await mkdir("dist", { recursive: true });
// Remove only the superseded, known gallery outputs from this build directory.
for (const file of ["showcase.html", "showcase.css", "showcase.js"])
  await unlink(path.resolve("dist", file)).catch((error) => {
    if (error.code !== "ENOENT") throw error;
  });
await icons("dist");
await import("./notices.mjs");
for (const file of ["LICENSE", "THIRD_PARTY_NOTICES.txt"])
  await copyFile(file, `dist/${file}`);
await build({
  entryPoints: ["src/main.tsx"],
  bundle: true,
  outfile: "dist/panel.js",
  format: "esm",
  minify: true,
  loader: { ".woff": "file" },
  assetNames: "[name]",
  sourcemap: true,
  target: "chrome116",
  define: { "process.env.NODE_ENV": '"production"' },
});
await build({
  entryPoints: ["src/background.ts", "src/content.ts"],
  bundle: true,
  outdir: "dist",
  minify: true,
  format: "iife",
  target: "chrome116",
  sourcemap: true,
});
await copyFile("public/manifest.json", "dist/manifest.json");
for (const file of ["review.html", "review.css", "review.js", "icons.css"])
  await copyFile(`public/${file}`, `dist/${file}`);
await build({
  entryPoints: ["src/icon-studies.ts"],
  bundle: true,
  outfile: "dist/icons.js",
  format: "esm",
  minify: true,
  target: "chrome116",
});
await writeFile(
  "dist/icons.html",
  (await readFile("public/icons.html", "utf8")).replace(
    "/src/icon-studies.ts",
    "icons.js",
  ),
);
const html =
  '<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ToMpathy - What&#39;s on the creator&#39;s mind?</title><link rel="stylesheet" href="panel.css"></head><body><div id="root"></div><script type="module" src="panel.js"></script></body></html>';
await writeFile("dist/panel.html", html);
await writeFile("dist/snapshot.html", html);
await writeFile(
  "dist/example.html",
  html.replace(
    "<title>ToMpathy - What&#39;s on the creator&#39;s mind?</title>",
    "<title>The door we stopped explaining</title>",
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
