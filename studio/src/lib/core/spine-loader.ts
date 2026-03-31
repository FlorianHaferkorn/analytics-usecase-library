/**
 * Decision Spine Loader
 *
 * Loads Decision Spine YAML files from core/action_codes/decision_spines/.
 * Server-side only (fs access).
 */

import { readFile, readdir } from 'node:fs/promises';
import { join } from 'node:path';
import { parseYaml } from './yaml-loader';
import type { DecisionSpine } from '@/lib/schemas/decision-spine';

const SPINES_DIR = join(
  process.cwd(),
  '..',
  'core',
  'action_codes',
  'decision_spines',
);

/** Load all Decision Spines from core/action_codes/decision_spines/. */
export async function loadAllSpines(): Promise<DecisionSpine[]> {
  let entries: string[];
  try {
    entries = await readdir(SPINES_DIR);
  } catch {
    return [];
  }

  const yamlFiles = entries
    .filter((f) => f.startsWith('DEC-SPINE-') && f.endsWith('.yaml'))
    .sort();

  const results = await Promise.all(
    yamlFiles.map(async (file) => {
      try {
        const raw = await readFile(join(SPINES_DIR, file), 'utf-8');
        const parsed = parseYaml<DecisionSpine>(raw);
        if (parsed?.id && parsed?.schema_version === '1.0') {
          return parsed;
        }
      } catch {
        // Skip malformed files
      }
      return null;
    }),
  );

  return results.filter((s): s is DecisionSpine => s !== null);
}

/** Load a single Decision Spine by ID. */
export async function loadSpine(
  spineId: string,
): Promise<DecisionSpine | null> {
  const all = await loadAllSpines();
  return all.find((s) => s.id === spineId) ?? null;
}

/** Load spines as a Map keyed by ID. */
export async function loadSpineMap(): Promise<Map<string, DecisionSpine>> {
  const spines = await loadAllSpines();
  return new Map(spines.map((s) => [s.id, s]));
}
