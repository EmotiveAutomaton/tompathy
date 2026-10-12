import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { unzipSync } from "fflate";
import assert from "node:assert/strict";

const { version } = JSON.parse(await readFile("dist/manifest.json", "utf8"));
const bytes = await readFile(`tompathy-${version}.zip`);
const files = unzipSync(bytes);
const built = (await readdir("dist"))
  .filter((name) => !name.endsWith(".map"))
  .sort();
assert.deepEqual(Object.keys(files).sort(), built);
for (const name of built)
  assert.deepEqual(Buffer.from(files[name]), await readFile(`dist/${name}`));
const manifest = JSON.parse(Buffer.from(files["manifest.json"]).toString());
assert.equal(manifest.manifest_version, 3);
assert.equal(manifest.host_permissions, undefined);
const receipt = {
  verifiedAt: new Date().toISOString(),
  zipBytes: bytes.length,
  sha256: createHash("sha256").update(bytes).digest("hex"),
  entries: built,
  matchesBuild: true,
  permanentHostPermissions: false,
};
await mkdir("evidence", { recursive: true });
await writeFile(
  "evidence/package-verification.json",
  JSON.stringify(receipt, null, 2),
);
console.log(receipt);
