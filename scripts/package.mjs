import { zipSync } from "fflate";
import { readdir, readFile, writeFile } from "node:fs/promises";
const files = {};
for (const name of await readdir("dist"))
  if (!name.endsWith(".map"))
    files[name] = new Uint8Array(await readFile(`dist/${name}`));
const { version } = JSON.parse(await readFile("dist/manifest.json", "utf8"));
const file = `tompathy-${version}.zip`;
await writeFile(file, zipSync(files));
console.log(`Created ${file}`);
