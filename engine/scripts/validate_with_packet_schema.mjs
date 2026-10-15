// Use the extension's own validator; no independent JavaScript contract copy.
import { build } from "esbuild";
import { mkdir, readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const root = path.resolve(import.meta.dirname, "../..");
await mkdir(path.join(root, ".local"), { recursive: true });
const output = path.join(root, ".local/engine-packet-validator.mjs");
await build({
  entryPoints: [path.join(root, "src/core/model.ts")],
  bundle: true, platform: "node", format: "esm", outfile: output,
});
const { PacketSchema } = await import(pathToFileURL(output).href);
async function packets(input) {
  if (input.endsWith(".json")) return [input];
  let entries;
  try { entries = await readdir(input, { withFileTypes: true }); }
  catch (error) { if (error.code === "ENOENT") return []; throw error; }
  return (await Promise.all(entries.map(entry => {
    const name = path.join(input, entry.name);
    return entry.isDirectory() ? packets(name) : name.endsWith(".json") ? [name] : [];
  }))).flat();
}
const inputs = process.argv.slice(2);
const files = (await Promise.all((inputs.length ? inputs : [
  path.join(root, "examples"), path.join(root, "engine/tests/fixtures/packets"),
]).map(packets))).flat();
let validated = 0;
for (const file of files) {
  const value = JSON.parse(await readFile(file, "utf8"));
  // examples may contain source captures; only analysis packets are candidates.
  if (!value.schemaVersion) continue;
  const result = PacketSchema.safeParse(value);
  if (!result.success) throw new Error(`${file}: ${result.error.message}`);
  validated++;
}
if (!validated) throw new Error("No contract packets were found");
console.log(`Validated ${validated} packets with the authoritative PacketSchema`);
