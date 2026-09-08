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

async function findBracketYamlPath(bracketId: string): Promise<string> {
  const dirs = await readdir(CORE_USECASES_DIR);
  const match = dirs.find((directory) => directory.startsWith(bracketId));
  if (!match) throw new Error(`No use case directory found for id: ${bracketId}`);
  return join(CORE_USECASES_DIR, match, 'UseCase_Bracket.yaml');
}

async function loadBracketYaml(bracketId: string): Promise<string> {
  return readFile(await findBracketYamlPath(bracketId), 'utf-8');
}

export async function handleReviewGET(request: Request, overrideProjectId?: string) {
  const { searchParams } = new URL(request.url);
  const bracketId = searchParams.get('bracketId');
  const compareVersionId = searchParams.get('compareVersionId');
  const projectId = overrideProjectId ?? searchParams.get('projectId') ?? 'default';

  const [, authError] = await requireRole('viewer', projectId);
  if (authError) return authError;
  if (!bracketId) return apiValidationError(['bracketId required']);

  const currentYaml = compareVersionId ? await loadBracketYaml(bracketId) : null;
  const compareVersion = compareVersionId ? getBracketVersionById(compareVersionId, projectId) : null;

  return apiSuccess({
    lifecycle: getLifecycle(bracketId, projectId),
    comments: getBracketComments(bracketId, projectId),
    versions: getBracketVersions(bracketId, projectId).map((version) => ({
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

export async function handleReviewPOST(request: Request, overrideProjectId?: string) {
  const body = await request.json() as {
    bracketId?: string;
    action?: 'comment' | 'snapshot' | 'restore';
    comment?: string;
    label?: string;
    note?: string;
    versionId?: string;
    projectId?: string;
  };
  const projectId = overrideProjectId ?? body.projectId ?? 'default';

  const [user, authError] = await requireRole('editor', projectId);
  if (authError) return authError;
  if (!body.bracketId || !body.action) {
    return apiValidationError(['bracketId and action required']);
  }

  const actor = user.email;
  try {
    if (body.action === 'comment') {
      if (!body.comment || body.comment.trim().length < 3) {
        return apiValidationError(['comment must be at least 3 characters']);
      }
      const comment = addBracketComment(body.bracketId, actor, body.comment.trim(), projectId);
      logAuditEvent('governance', body.bracketId, 'update', {
        before: null,
        after: { comment: comment.comment },
        justification: 'Bracket review comment added',
      }, projectId, actor);
      return apiSuccess({ comment });
    }

    if (body.action === 'restore') {
      if (!body.versionId) return apiValidationError(['versionId required for restore']);
      const version = getBracketVersionById(body.versionId, projectId);
      if (!version || version.bracket_id !== body.bracketId) {
        return apiError(ErrorCode.NOT_FOUND, 'Version not found for bracket', 404);
      }
      const targetPath = await findBracketYamlPath(body.bracketId);
      const beforeYaml = await loadBracketYaml(body.bracketId);
      await writeFile(targetPath, version.yaml_content, 'utf-8');
      logAuditEvent('bracket', body.bracketId, 'update', {
        before: { yaml: beforeYaml },
        after: { yaml: version.yaml_content, restoredFrom: version.id },
        justification: body.note?.trim() || `Restored snapshot ${version.label}`,
      }, projectId, actor);
      return apiSuccess({ restored: true, versionId: version.id, label: version.label });
    }

    const yamlContent = await loadBracketYaml(body.bracketId);
    const version = createBracketVersion(
      body.bracketId,
      body.label?.trim() || `Snapshot ${new Date().toLocaleString('de-DE')}`,
      body.note?.trim() || '',
      yamlContent,
      actor,
      projectId,
    );
    logAuditEvent('bracket', body.bracketId, 'update', {
      before: null,
      after: { versionId: version.id, label: version.label },
      justification: body.note?.trim() || 'Manual snapshot created',
    }, projectId, actor);
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
