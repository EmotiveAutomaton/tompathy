import { readFile, access } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
export async function verifyBuild() {
  const manifest = JSON.parse(await readFile("dist/manifest.json", "utf8"));
  if (
    manifest.manifest_version !== 3 ||
    !manifest.permissions.includes("sidePanel")
  )
    throw Error("Missing Chrome side-panel manifest.");
  const assets = [
    manifest.background.service_worker,
    manifest.side_panel.default_path,
    ...Object.values(manifest.icons),
    "panel.js",
    "panel.css",
    "content.js",
    "example.html",
    "snapshot.html",
    "review.html",
    "review.css",
    "review.js",
    "build-info.json",
  ];
  for (const asset of assets) {
    if (path.dirname(asset) !== ".")
      throw Error(`Unexpected package asset path: ${asset}`);
    await access(path.join("dist", asset));
  }
  return {
    name: manifest.name,
    version: manifest.version,
    folder: path.resolve("dist"),
    files: assets.length,
  };
}
if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
)
  console.log(await verifyBuild());
