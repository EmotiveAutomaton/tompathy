import { build } from "esbuild";
import { spawnSync } from "node:child_process";
await build({
  entryPoints: ["tests/core.test.ts"],
  bundle: true,
  platform: "node",
  format: "esm",
  outfile: ".local/core.test.mjs",
});
const result = spawnSync(process.execPath, ["--test", ".local/core.test.mjs"], {
  stdio: "inherit",
});
process.exitCode = result.status ?? 1;
