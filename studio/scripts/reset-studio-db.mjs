import { existsSync, unlinkSync } from 'node:fs';
import { isAbsolute, relative, resolve } from 'node:path';

// Reset only the dedicated E2E database. Never scan the workspace for databases.
const studioRoot = resolve(process.cwd());
const e2eRoot = resolve(studioRoot, '.e2e');
const configured = process.env.STUDIO_DB_PATH ?? '.e2e/studio.db';
const dbPath = isAbsolute(configured) ? resolve(configured) : resolve(studioRoot, configured);
const relativeTarget = relative(e2eRoot, dbPath);

if (relativeTarget.startsWith('..') || isAbsolute(relativeTarget) || !relativeTarget) {
  throw new Error(`[reset-studio-db] Refusing to reset a database outside ${e2eRoot}: ${dbPath}`);
}

let removed = 0;
const deleted = [];
for (const candidate of [dbPath, `${dbPath}-wal`, `${dbPath}-shm`, `${dbPath}-journal`]) {
  if (!existsSync(candidate)) continue;
  unlinkSync(candidate);
  removed += 1;
  deleted.push(candidate);
}

console.log(`[reset-studio-db] Removed ${removed} dedicated E2E database artifacts`);
for (const p of deleted) {
  console.log(`[reset-studio-db] - ${p}`);
}

