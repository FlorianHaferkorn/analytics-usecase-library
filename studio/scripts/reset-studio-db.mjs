import { unlinkSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

// Reset Studio's local SQLite file so E2E tests are deterministic.
// We delete all matching studio.db artifacts found under the workspace.
const root = process.cwd();
const dbBasenames = new Set(['studio.db', 'studio.db-wal', 'studio.db-shm', 'studio.db-journal']);

const ignoredDirs = new Set(['node_modules', '.next', 'dist', 'build', 'coverage', '.git', '.turbo']);

function walk(dir, depth) {
  if (depth <= 0) return;
  let entries;
  try {
    entries = readdirSync(dir, { withFileTypes: true });
  } catch {
    return;
  }

  for (const ent of entries) {
    if (ent.isDirectory()) {
      if (ignoredDirs.has(ent.name)) continue;
      walk(join(dir, ent.name), depth - 1);
      continue;
    }

    if (!ent.isFile()) continue;
    if (!dbBasenames.has(ent.name)) continue;

    const p = join(dir, ent.name);
    try {
      unlinkSync(p);
      removed += 1;
      deleted.push(p);
    } catch {
      // Best-effort cleanup
    }
  }
}

let removed = 0;
const deleted = [];
walk(root, 8);

console.log(`[reset-studio-db] Removed ${removed} studio.db artifacts`);
for (const p of deleted.slice(0, 20)) {
  console.log(`[reset-studio-db] - ${p}`);
}
if (deleted.length > 20) {
  console.log(`[reset-studio-db] ... and ${deleted.length - 20} more`);
}

