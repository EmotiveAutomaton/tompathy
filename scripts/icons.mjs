import { copyFile } from "node:fs/promises";

// Derived from the supplied src/assets/icon-master.png. Builds on every platform use these
// small, checked-in sizes; resize-icons.ps1 regenerates them on Windows.
export async function icons(dir) {
  for (const size of [16, 32, 48, 128])
    await copyFile(`public/icon${size}.png`, `${dir}/icon${size}.png`);
}
