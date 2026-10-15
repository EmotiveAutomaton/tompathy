// Opt-in, local-only companion. Never copied into dist or published by a build.
// Usage: node scripts/art-local-history.mjs PATH_TO_WEBSITE_CHECKOUT
import { execFileSync } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { build } from "esbuild";
if (!process.argv[2]) throw Error("Supply the local Website checkout path.");
const repo = path.resolve(process.argv[2]);
const log = execFileSync(
  "git",
  [
    "-c",
    `safe.directory=${repo.replaceAll("\\", "/")}`,
    "-C",
    repo,
    "log",
    "--follow",
    "--format=%H%x09%aI%x09%s",
    "--",
    "docs/art-content.md",
  ],
  { encoding: "utf8" },
);
await mkdir(".local", { recursive: true });
await build({
  stdin: {
    contents:
      "export {createArtExample,artContext} from './src/core/art-example'; export {readingFile,parseReadingFile} from './src/core/reading-file';",
    resolveDir: process.cwd(),
  },
  bundle: true,
  platform: "node",
  format: "esm",
  outfile: ".local/art-history-tools.mjs",
});
const { createArtExample, artContext, readingFile, parseReadingFile } =
  await import("../.local/art-history-tools.mjs");
const packet = await createArtExample();
const rows = log
  .trim()
  .split("\n")
  .map((line) => {
    const [sha, date, ...subject] = line.split("\t");
    return { sha, date, subject: subject.join("\t") };
  });
const context = [artContext];
for (let i = 0; i < rows.length; i += 20) {
  const batch = rows.slice(i, i + 20);
  context.push({
    id: `art-local-history-${i / 20}`,
    source: "Local Website Git history · docs/art-content.md",
    lineage: "file",
    selected: false,
    retrievedAt: new Date().toISOString(),
    excerpt:
      "Saved revisions from the local essay repository. Dates are commit timestamps, not proven dates of ideation or AI involvement. Commit subjects are recorded descriptions, not independently verified causal accounts.",
    facts: batch.map((r) => ({
      date: r.date.slice(0, 10),
      dateKind: "source-updated",
      label: r.subject,
      quote: `Saved revision ${r.sha.slice(0, 12)}: ${r.subject}`,
      source: `Local Git revision ${r.sha}`,
    })),
  });
}
const html = readingFile({
  sessionVersion: "1.0",
  artifact: packet.artifact,
  packet,
  scope: "artifact",
  context,
});
const roundTrip = await parseReadingFile(html);
if (roundTrip.context.length !== context.length)
  throw Error("History export round trip failed");
const destination = ".local/art-with-local-history.html";
await writeFile(destination, html);
console.log(
  JSON.stringify({
    destination,
    revisions: rows.length,
    earliest: rows.at(-1).date,
    latest: rows[0].date,
    bytes: Buffer.byteLength(html),
    roundTrip: "passed",
  }),
);
