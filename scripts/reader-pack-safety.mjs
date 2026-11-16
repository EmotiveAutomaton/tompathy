import { readdir, readFile } from 'node:fs/promises';
import { join } from 'node:path';

/** Only inspects files entering a package, never the user's local research store. */
export async function assertReleasePacks(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isSymbolicLink()) throw new Error(`Release cannot follow a symbolic link: ${path}`);
    if (entry.isDirectory()) await assertReleasePacks(path);
    else if (entry.name === 'pack.json') {
      const pack = JSON.parse(await readFile(path, 'utf8'));
      if (pack.version !== 'reader-pack-1' || pack.research_only !== false ||
          pack.encoder?.kind === 'constructed' || !pack.training?.length ||
          [...pack.training, pack.encoder?.license].some(x => x?.commercial_use !== true)) {
        throw new Error(`Research-only, constructed or unlicensed reader refused by release: ${path}`);
      }
    }
  }
}
