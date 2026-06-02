/**
 * GET /api/core/brackets/[id]  — returns raw YAML for a single bracket
 * PUT /api/core/brackets/[id]  — writes YAML back to core/
 *
 * Security: the directory is resolved via readdir prefix-match only — no
 * caller-controlled path fragments reach fs.readFile / fs.writeFile.
 */

import { readdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { NextRequest } from 'next/server';
import { apiSuccess, apiError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';
import { requireAuth } from '@/lib/auth/session';
import { logAuditEvent } from '@/lib/db/audit-repo';

const CORE_USECASES_DIR = join(process.cwd(), '..', 'core', 'usecases', 'core');

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const [, authError] = await requireAuth();
  if (authError) return authError;

  const { id } = await params;

  if (!/^[A-Za-z0-9-]+$/.test(id)) {
    return apiError(ErrorCode.VALIDATION_ERROR, 'Invalid use case ID', 400);
  }

  const dirs = await readdir(CORE_USECASES_DIR);
  const match = dirs.find((d) => d.startsWith(id));
  if (!match) {
    return apiError(ErrorCode.NOT_FOUND, `No use case directory found for id: ${id}`, 404);
  }

  const targetPath = join(CORE_USECASES_DIR, match, 'UseCase_Bracket.yaml');
  const yaml = await readFile(targetPath, 'utf-8');

  return apiSuccess({ id, yaml });
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const [user, authError] = await requireAuth();
  if (authError) return authError;

  const { id } = await params;

  // Validate id: must look like a use-case ID (letters, digits, hyphens only)
  if (!/^[A-Za-z0-9-]+$/.test(id)) {
    return apiError(ErrorCode.VALIDATION_ERROR, 'Invalid use case ID', 400);
  }

  let yaml: string;
  try {
    const body = await request.json() as { yaml?: unknown };
    if (typeof body.yaml !== 'string' || body.yaml.trim().length === 0) {
      return apiError(ErrorCode.VALIDATION_ERROR, 'Body must contain a non-empty "yaml" string', 400);
    }
    yaml = body.yaml;
  } catch {
    return apiError(ErrorCode.VALIDATION_ERROR, 'Invalid JSON body', 400);
  }

  // Resolve the directory via readdir — never trust the caller to provide a path
  const dirs = await readdir(CORE_USECASES_DIR);
  const match = dirs.find((d) => d.startsWith(id));
  if (!match) {
    return apiError(ErrorCode.NOT_FOUND, `No use case directory found for id: ${id}`, 404);
  }

  const targetPath = join(CORE_USECASES_DIR, match, 'UseCase_Bracket.yaml');

  let beforeYaml = '';
  try {
    beforeYaml = await readFile(targetPath, 'utf-8');
  } catch {
    beforeYaml = '';
  }

  await writeFile(targetPath, yaml, 'utf-8');

  logAuditEvent(
    'bracket',
    id,
    'update',
    {
      before: { length: beforeYaml.length },
      after: { length: yaml.length },
    },
    'default',
    user!.email,
  );

  return apiSuccess({ saved: true, path: `core/usecases/core/${match}/UseCase_Bracket.yaml` });
}
