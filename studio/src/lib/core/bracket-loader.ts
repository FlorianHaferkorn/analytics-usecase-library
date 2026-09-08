/**
 * UseCase Bracket Loader
 *
 * Loads UseCase_Bracket.yaml files from core/usecases/ and returns
 * typed UseCaseBracket objects. Server-side only (fs access).
 */

import { readFile, readdir } from 'node:fs/promises';
import { join } from 'node:path';
import { parseYaml } from './yaml-loader';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';

const CORE_USECASES_DIR = join(
  /*turbopackIgnore: true*/ process.cwd(),
  '..',
  'core',
  'usecases',
  'core'
);

export async function resolveBracketPath(useCaseId: string): Promise<string | null> {
  const dirs = await readdir(CORE_USECASES_DIR);
  const match = dirs.find((d) => d.startsWith(useCaseId));
  if (!match) return null;
  return join(CORE_USECASES_DIR, match, 'UseCase_Bracket.yaml');
}

/** Load raw bracket YAML for editing. */
export async function loadBracketYaml(useCaseId: string): Promise<string | null> {
  const path = await resolveBracketPath(useCaseId);
  if (!path) return null;
  try {
    return await readFile(path, 'utf-8');
  } catch {
    return null;
  }
}

/** Load a single UseCase Bracket by use case ID (e.g. "COM-001"). */
export async function loadBracket(
  useCaseId: string
): Promise<UseCaseBracketV20Lean | null> {
  const path = await resolveBracketPath(useCaseId);
  if (!path) return null;
  try {
    const raw = await readFile(path, 'utf-8');
    return parseYaml<UseCaseBracketV20Lean>(raw);
  } catch {
    return null;
  }
}

/** Load all UseCase Brackets from core/usecases/core/. */
export async function loadAllBrackets(): Promise<UseCaseBracketV20Lean[]> {
  const dirs = await readdir(CORE_USECASES_DIR);

  const results = await Promise.all(
    dirs.sort().map(async (dir) => {
      const bracketPath = join(CORE_USECASES_DIR, dir, 'UseCase_Bracket.yaml');
      try {
        const raw = await readFile(bracketPath, 'utf-8');
        return parseYaml<UseCaseBracketV20Lean>(raw);
      } catch {
        return null;
      }
    })
  );

  return results.filter((b): b is UseCaseBracketV20Lean => b !== null);
}
