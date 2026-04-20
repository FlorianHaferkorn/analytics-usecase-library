import { readdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { apiError, apiSuccess, apiValidationError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';
import { requireRole } from '@/lib/auth/require-role';
import { getLifecycle } from '@/lib/governance/approval-workflow';
import {
  addBracketComment,
  createBracketVersion,
  getBracketComments,
  getBracketVersionById,
  getBracketVersions,
} from '@/lib/governance/review-repo';
import { logAuditEvent } from '@/lib/db/audit-repo';

const CORE_USECASES_DIR = join(process.cwd(), '..', 'core', 'usecases', 'core');

async function loadBracketYaml(bracketId: string): Promise<string> {
  const dirs = await readdir(CORE_USECASES_DIR);
  const match = dirs.find((dir) => dir.startsWith(bracketId));
  if (!match) {
    throw new Error(`No use case directory found for id: ${bracketId}`);
  }
  return readFile(join(CORE_USECASES_DIR, match, 'UseCase_Bracket.yaml'), 'utf-8');
}

async function resolveBracketYamlPath(bracketId: string): Promise<string> {
  const dirs = await readdir(CORE_USECASES_DIR);
  const match = dirs.find((dir) => dir.startsWith(bracketId));
  if (!match) {
    throw new Error(`No use case directory found for id: ${bracketId}`);
  }
  return join(CORE_USECASES_DIR, match, 'UseCase_Bracket.yaml');
}

export async function GET(request: Request) {
  const [, authErr] = await requireRole('viewer');
  if (authErr) return authErr;

  const { searchParams } = new URL(request.url);
  const bracketId = searchParams.get('bracketId');
  const compareVersionId = searchParams.get('compareVersionId');
  if (!bracketId) return apiValidationError(['bracketId required']);

  const currentYaml = compareVersionId ? await loadBracketYaml(bracketId) : null;
  const compareVersion = compareVersionId ? getBracketVersionById(compareVersionId) : null;

  return apiSuccess({
    lifecycle: getLifecycle(bracketId),
    comments: getBracketComments(bracketId),
    versions: getBracketVersions(bracketId).map((version) => ({
      id: version.id,
      bracket_id: version.bracket_id,
      label: version.label,
      note: version.note,
      created_by: version.created_by,
      created_at: version.created_at,
    })),
    compare: compareVersion && currentYaml
      ? {
          currentYaml,
          version: {
            id: compareVersion.id,
            label: compareVersion.label,
            note: compareVersion.note,
            yaml_content: compareVersion.yaml_content,
            created_by: compareVersion.created_by,
            created_at: compareVersion.created_at,
          },
        }
      : null,
  });
}

export async function POST(request: Request) {
  const [user, authErr] = await requireRole('editor');
  if (authErr) return authErr;

  const body = await request.json() as {
    bracketId?: string;
    action?: 'comment' | 'snapshot' | 'restore';
    comment?: string;
    label?: string;
    note?: string;
    actor?: string;
    versionId?: string;
  };

  if (!body.bracketId || !body.action) {
    return apiValidationError(['bracketId and action required']);
  }

  const actor = user.email;

  try {
    if (body.action === 'comment') {
      if (!body.comment || body.comment.trim().length < 3) {
        return apiValidationError(['comment must be at least 3 characters']);
      }
      const comment = addBracketComment(body.bracketId, actor, body.comment.trim());
      logAuditEvent('governance', body.bracketId, 'update', {
        before: null,
        after: { comment: comment.comment },
        justification: 'Bracket review comment added',
      }, 'default', actor);
      return apiSuccess({ comment });
    }

    if (body.action === 'restore') {
      if (!body.versionId) {
        return apiValidationError(['versionId required for restore']);
      }
      const version = getBracketVersionById(body.versionId);
      if (!version || version.bracket_id !== body.bracketId) {
        return apiError(ErrorCode.NOT_FOUND, 'Version not found for bracket', 404);
      }
      const targetPath = await resolveBracketYamlPath(body.bracketId);
      const beforeYaml = await loadBracketYaml(body.bracketId);
      await writeFile(targetPath, version.yaml_content, 'utf-8');
      logAuditEvent('bracket', body.bracketId, 'update', {
        before: { yaml: beforeYaml },
        after: { yaml: version.yaml_content, restoredFrom: version.id },
        justification: body.note?.trim() || `Restored snapshot ${version.label}`,
      }, 'default', actor);
      return apiSuccess({ restored: true, versionId: version.id, label: version.label });
    }

    const yamlContent = await loadBracketYaml(body.bracketId);
    const version = createBracketVersion(
      body.bracketId,
      body.label?.trim() || `Snapshot ${new Date().toLocaleString('de-DE')}`,
      body.note?.trim() || '',
      yamlContent,
      actor,
    );
    logAuditEvent('bracket', body.bracketId, 'update', {
      before: null,
      after: { versionId: version.id, label: version.label },
      justification: body.note?.trim() || 'Manual snapshot created',
    }, 'default', actor);
    return apiSuccess({
      version: {
        id: version.id,
        bracket_id: version.bracket_id,
        label: version.label,
        note: version.note,
        created_by: version.created_by,
        created_at: version.created_at,
      },
    });
  } catch (error) {
    return apiError(ErrorCode.INTERNAL_ERROR, error instanceof Error ? error.message : 'Review operation failed', 500);
  }
}