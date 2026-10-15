import { readFile, readdir, writeFile } from "node:fs/promises";
const lock = JSON.parse(await readFile("package-lock.json", "utf8"));
const parts = [
  "ToMpathy third-party notices\nGenerated from the locked production dependencies. Build/test tools are not shipped.\n",
];
for (const [folder, entry] of Object.entries(lock.packages)) {
  if (!folder.startsWith("node_modules/") || entry.dev) continue;
  const pkg = JSON.parse(await readFile(`${folder}/package.json`, "utf8"));
  const names = (await readdir(folder)).filter((n) =>
    /^licen[cs]e(?:\.|$)/i.test(n),
  );
  if (!names.length) throw Error(`Missing license for ${pkg.name}`);
  parts.push(
    `\n${"=".repeat(72)}\n${pkg.name} ${pkg.version} (${pkg.license ?? entry.license})\n`,
  );
  for (const name of names)
    parts.push(await readFile(`${folder}/${name}`, "utf8"));
}
parts.push(
  "\nRoboto Serif · Latin subsets: variable GRAD for reading; variable wght (100–900) for confidence labels.\nhttps://github.com/google/fonts/tree/main/ofl/robotoserif\n",
  (await readFile("src/assets/RobotoSerif-OFL.txt", "utf8")).replace(/[ \t]+$/gm, ""),
);
await writeFile("THIRD_PARTY_NOTICES.txt", parts.join("\n"));
