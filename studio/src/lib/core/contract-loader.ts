/**
 * Data Contract Loader
 *
 * Loads Data Contract YAML files from core/data_contracts/domains/.
 * Server-side only (fs access).
 */

import { readFile, readdir } from 'node:fs/promises';
import { join } from 'node:path';
import { parseYaml } from './yaml-loader';
import type { DataContract, DimensionTable, FactTable } from '@/lib/schemas';

const CONTRACTS_DIR = join(
  process.cwd(),
  '..',
  'core',
  'data_contracts',
  'domains',
);

type ContractTable = { name: string; columns?: { name: string }[]; conformed_from?: string; uses_columns?: string[] };

/** A dimension of the domain view: the owner's definition; `conformed_from` marks a resolved reference. */
export type ResolvedDimension = DimensionTable & { conformed_from?: string };
/** A fact of the domain view; `grain` is missing only on an unresolvable reference. */
export type ResolvedFact = Omit<FactTable, 'grain'> & { grain?: string; conformed_from?: string };
/**
 * A contract after `resolveConformed` (domain view). The raw `DataContract` (generated from
 * `tooling/generator/schemas/data_contract.schema.json`) types a reference as
 * `ConformedReference` without columns; after resolution every table carries `columns`.
 */
export interface ResolvedContract extends Omit<DataContract, 'dimension' | 'fact'> {
  dimension: ResolvedDimension[];
  fact: ResolvedFact[];
}
type Section = 'dimension' | 'fact';

/**
 * Domain view of the contracts (Bus-Matrix, 29.09.2026 — same rule as the Python resolver
 * `tooling/utils/data_contracts.py`): a table is defined once, in its owning domain; another
 * domain refers with `{ name, conformed_from, uses_columns? }` and no columns. Every reference is
 * replaced by a copy of the owner's table, narrowed to `uses_columns`, with `conformed_from` kept;
 * a definition with `uses_columns` is narrowed the same way. Unresolvable references get
 * `columns: []` so no consumer reads `undefined`.
 */
export function resolveConformed(contracts: DataContract[]): ResolvedContract[] {
  const owners = new Map<string, { domain: string; section: Section; table: ContractTable }>();
  for (const c of contracts) {
    for (const section of ['dimension', 'fact'] as Section[]) {
      for (const t of ((c[section] ?? []) as ContractTable[])) {
        if (t?.name && !t.conformed_from && !owners.has(t.name)) {
          owners.set(t.name, { domain: c.domain, section, table: t });
        }
      }
    }
  }
  const narrow = (t: ContractTable, uses?: string[]): ContractTable => {
    if (!Array.isArray(uses)) return t;
    const byName = new Map((t.columns ?? []).map((col) => [col.name, col]));
    return { ...t, columns: uses.filter((n) => byName.has(n)).map((n) => byName.get(n)!) };
  };
  return contracts.map((c) => {
    const out = { ...c } as unknown as ResolvedContract;
    for (const section of ['dimension', 'fact'] as Section[]) {
      const tables = (c[section] ?? []) as ContractTable[];
      (out as unknown as Record<Section, ContractTable[]>)[section] = tables.map((t) => {
        if (!t?.conformed_from) return narrow(t, t?.uses_columns);
        const own = owners.get(t.name);
        if (!own || own.domain !== t.conformed_from) return { ...t, columns: [] };
        const ownerTable: ContractTable = { ...own.table };
        delete ownerTable.uses_columns;   // the owner's own use is not the referencing domain's
        return { ...narrow(ownerTable, t.uses_columns), conformed_from: t.conformed_from };
      });
    }
    return out;
  });
}

/** Load all Data Contracts from core/data_contracts/domains/ (domain view, see resolveConformed). */
export async function loadAllContracts(): Promise<ResolvedContract[]> {
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

  return resolveConformed(results.filter((c): c is DataContract => c !== null));
}

/** Load a single Data Contract by domain name. */
export async function loadContract(
  domain: string,
): Promise<ResolvedContract | null> {
  const all = await loadAllContracts();
  return all.find((c) => c.domain.toLowerCase() === domain.toLowerCase()) ?? null;
}

/** Load contracts as a Map keyed by domain. */
export async function loadContractMap(): Promise<Map<string, ResolvedContract>> {
  const contracts = await loadAllContracts();
  return new Map(contracts.map((c) => [c.domain, c]));
}
