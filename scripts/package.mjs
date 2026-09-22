import { zipSync } from "fflate";
import { readdir, readFile, writeFile } from "node:fs/promises";
const files = {};
for (const name of await readdir("dist"))
  if (!name.endsWith(".map"))
    files[name] = new Uint8Array(await readFile(`dist/${name}`));
await writeFile("tompathy-0.1.0.zip", zipSync(files));
console.log("Created tompathy-0.1.0.zip");
