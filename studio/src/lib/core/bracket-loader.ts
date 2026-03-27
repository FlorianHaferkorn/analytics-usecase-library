/**
 * UseCase Bracket Loader
 *
 * Loads UseCase_Bracket.yaml files from core/usecases/ and returns
 * typed UseCaseBracket objects. Server-side only (fs access).
 */

import { readFile, readdir, stat } from 'node:fs/promises';
import { join } from 'node:path';
import { parseYaml } from './yaml-loader';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';

const CORE_USECASES_DIR = join(
  process.cwd(),
  '..',
  'core',
  'usecases',
  'core'
);

/** Load a single UseCase Bracket by use case ID (e.g. "COM-001"). */
export async function loadBracket(
  useCaseId: string
): Promise<UseCaseBracketV20Lean | null> {
  const dirs = await readdir(CORE_USECASES_DIR);
  const match = dirs.find((d) => d.startsWith(useCaseId));
  if (!match) return null;

  const bracketPath = join(CORE_USECASES_DIR, match, 'UseCase_Bracket.yaml');
  try {
    const raw = await readFile(bracketPath, 'utf-8');
    return parseYaml<UseCaseBracketV20Lean>(raw);
  } catch {
    return null;
  }
}

/** Load all UseCase Brackets from core/usecases/core/. */
export async function loadAllBrackets(): Promise<UseCaseBracketV20Lean[]> {
  const dirs = await readdir(CORE_USECASES_DIR);
  const brackets: UseCaseBracketV20Lean[] = [];

  for (const dir of dirs.sort()) {
    const bracketPath = join(CORE_USECASES_DIR, dir, 'UseCase_Bracket.yaml');
    try {
      const s = await stat(bracketPath);
      if (!s.isFile()) continue;
      const raw = await readFile(bracketPath, 'utf-8');
      brackets.push(parseYaml<UseCaseBracketV20Lean>(raw));
    } catch {
      // Skip directories without a bracket file
    }
  }

  return brackets;
}
