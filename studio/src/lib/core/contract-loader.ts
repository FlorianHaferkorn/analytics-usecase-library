/**
 * Data Contract Loader
 *
 * Loads Data Contract YAML files from core/data_contracts/domains/.
 * Server-side only (fs access).
 */

import { readFile, readdir } from 'node:fs/promises';
import { join } from 'node:path';
import { parseYaml } from './yaml-loader';
import type { DataContract } from '@/lib/schemas';

const CONTRACTS_DIR = join(
  process.cwd(),
  '..',
  'core',
  'data_contracts',
  'domains',
);

/** Load all Data Contracts from core/data_contracts/domains/. */
export async function loadAllContracts(): Promise<DataContract[]> {
  let entries: string[];
  try {
    entries = await readdir(CONTRACTS_DIR);
  } catch {
    return [];
  }

  const yamlFiles = entries
    .filter((f) => f.endsWith('.yaml') || f.endsWith('.yml'))
    .sort();

  const results = await Promise.all(
    yamlFiles.map(async (file) => {
      try {
        const raw = await readFile(join(CONTRACTS_DIR, file), 'utf-8');
        const parsed = parseYaml<DataContract>(raw);
        if (parsed?.domain && parsed?.version) {
          return parsed;
        }
      } catch {
        // Skip malformed files
      }
      return null;
    }),
  );

  return results.filter((c): c is DataContract => c !== null);
}

/** Load a single Data Contract by domain name. */
export async function loadContract(
  domain: string,
): Promise<DataContract | null> {
  const all = await loadAllContracts();
  return all.find((c) => c.domain.toLowerCase() === domain.toLowerCase()) ?? null;
}

/** Load contracts as a Map keyed by domain. */
export async function loadContractMap(): Promise<Map<string, DataContract>> {
  const contracts = await loadAllContracts();
  return new Map(contracts.map((c) => [c.domain, c]));
}
