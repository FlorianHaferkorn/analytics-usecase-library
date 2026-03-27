/**
 * Action Code Loader
 *
 * Loads Action Code YAML files from core/action_codes/ and returns
 * typed ActionCode objects. Server-side only (fs access).
 */

import { readFile, readdir, stat } from 'node:fs/promises';
import { join } from 'node:path';
import { parseYaml } from './yaml-loader';
import type { ActionCodeDefinitionV20AIMirror } from '@/lib/schemas';

const ACTION_CODES_DIR = join(process.cwd(), '..', 'core', 'action_codes');

/** Recursively find all .yaml files in a directory. */
async function findYamlFiles(dir: string): Promise<string[]> {
  const entries = await readdir(dir, { withFileTypes: true });
  const files: string[] = [];

  for (const entry of entries) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await findYamlFiles(fullPath)));
    } else if (entry.name.endsWith('.yaml') || entry.name.endsWith('.yml')) {
      files.push(fullPath);
    }
  }

  return files;
}

/** Load all Action Codes from core/action_codes/. */
export async function loadAllActionCodes(): Promise<
  ActionCodeDefinitionV20AIMirror[]
> {
  const yamlFiles = await findYamlFiles(ACTION_CODES_DIR);

  const results = await Promise.all(
    yamlFiles.sort().map(async (filePath) => {
      try {
        const raw = await readFile(filePath, 'utf-8');
        const parsed = parseYaml<ActionCodeDefinitionV20AIMirror>(raw);
        if (parsed?.id && parsed?.schema_version === '2.0') {
          return parsed;
        }
      } catch {
        // Skip malformed files
      }
      return null;
    })
  );

  return results.filter(
    (a): a is ActionCodeDefinitionV20AIMirror => a !== null
  );
}

/** Load a single Action Code by ID (e.g. "C-M2.1"). */
export async function loadActionCode(
  actionId: string
): Promise<ActionCodeDefinitionV20AIMirror | null> {
  const all = await loadAllActionCodes();
  return all.find((a) => a.id === actionId) ?? null;
}
