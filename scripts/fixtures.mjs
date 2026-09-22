import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
await mkdir("examples", { recursive: true });
await build({
  entryPoints: ["src/core/example.ts"],
  bundle: true,
  platform: "node",
  format: "esm",
  outfile: ".local/example-generator.mjs",
});
const { createExample, exampleText, exampleContext } =
  await import("../.local/example-generator.mjs");
await writeFile(
  "examples/bench-result.json",
  JSON.stringify(await createExample(), null, 2),
);
await writeFile(
  "examples/bench-revision.json",
  JSON.stringify(await createExample("tompathy:example", true), null, 2),
);
await writeFile("examples/bench-source.txt", exampleText.join("\n\n") + "\n");
await writeFile(
  "examples/bench-context.json",
  JSON.stringify(exampleContext, null, 2),
);
