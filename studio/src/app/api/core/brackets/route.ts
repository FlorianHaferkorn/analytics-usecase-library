import { mkdir, readdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { parseYaml, toYaml } from '@/lib/core/yaml-loader';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';
import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { invalidateForgeBootstrapCache } from '@/lib/core/forge-bootstrap';
import { apiCreated, apiError, apiSuccess, apiValidationError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';
import { logAuditEvent } from '@/lib/db/audit-repo';
import { requireAuth } from '@/lib/auth/session';
import { auth, type ProjectMembership } from '@/lib/auth/config';

const CORE_USECASES_DIR = join(process.cwd(), '..', 'core', 'usecases', 'core');

function projectAccessDeniedResponse(): Response {
  return new Response(JSON.stringify({ error: 'Forbidden', code: 'PROJECT_ACCESS_DENIED' }), {
    status: 403,
    headers: { 'Content-Type': 'application/json' },
  });
}

function getMembershipsFromSession(session: unknown): ProjectMembership[] {
  const anySession = session as Record<string, unknown> | null | undefined;
  return (anySession?.project_memberships as ProjectMembership[] | undefined) ?? [];
}

async function enforceLegacyProjectHeader(request: Request): Promise<Response | null> {
  const headerProjectId = request.headers.get('X-Project-Id');
  if (!headerProjectId) return null;

  const session = await auth();
  // No session => let the canonical handler return 401/appropriate response.
  if (!session?.user?.email) return null;

  const memberships = getMembershipsFromSession(session);
  const isMember = memberships.some((m) => m.projectId === headerProjectId);
  const gracefulFallback = memberships.length === 0 && headerProjectId === 'default';

  if (!isMember && !gracefulFallback) return projectAccessDeniedResponse();
  return null;
}

function slugify(value: string): string {
  return value
    .replace(/[^A-Za-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 80);
}

function buildFactsheet(bracket: UseCaseBracketV20Lean): string {
  return `---
id: ${bracket.id}
factsheet_type: business
---
# ${bracket.id} - ${bracket.title}

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** ${bracket.id}
- **Domain:** ${bracket.domain}
- **Business Owner:** ${bracket.governance.owner_role}
- **KPI Owner:** ${bracket.governance.steward_role}
- **Related Data Contract:** ${bracket.overrides?.data_contract_ref ?? 'TBD'}

---

## 1. Business Summary

**Purpose:** Draft scaffold generated from Discovery and refined in Steering.

---

## 2. Core Business Questions

- Which drivers explain ${bracket.orchestration.strategic_kpi_id} best?
- Which actions should be activated first?

---

## 3. KPI & Action Code Overview

> Full machine-readable configuration in UseCase_Bracket.yaml.
`;
}

export async function GET(request: Request) {
  const [, authError] = await requireAuth();
  if (authError) return authError;

  const denied = await enforceLegacyProjectHeader(request);
  if (denied) return denied;

  const { searchParams } = new URL(request.url);
  const domain = searchParams.get('domain');

  let brackets = await loadAllBrackets();

  if (domain) {
    brackets = brackets.filter((b) => b.domain === domain);
  }

  return apiSuccess({ count: brackets.length, brackets });
}

export async function POST(request: Request) {
  const [user, authError] = await requireAuth();
  if (authError) return authError;

  const denied = await enforceLegacyProjectHeader(request);
  if (denied) return denied;

  const body = await request.json() as { id?: string; title?: string; yaml?: string };
  if (!body.id || !body.title || !body.yaml) {
    return apiValidationError(['id, title and yaml are required']);
  }

  const bracketId = body.id;
  const bracketTitle = body.title;
  const bracketYaml = body.yaml;

  if (!/^[A-Z]{2,3}-\d{3}$/.test(bracketId)) {
    return apiError(ErrorCode.VALIDATION_ERROR, 'id must match pattern like COM-001 or XD-001', 400);
  }

  let parsed: UseCaseBracketV20Lean;
  try {
    parsed = parseYaml<UseCaseBracketV20Lean>(bracketYaml);
  } catch {
    return apiError(ErrorCode.VALIDATION_ERROR, 'yaml must be valid bracket YAML', 400);
  }

  const normalized: UseCaseBracketV20Lean = {
    ...parsed,
    id: bracketId,
    title: bracketTitle,
    documentation: { business_factsheet: './Business_Factsheet.md' },
  };

  const dirs = await readdir(CORE_USECASES_DIR);
  if (dirs.some((dir) => dir.startsWith(bracketId))) {
    return apiError(ErrorCode.CONFLICT, `Use case ${bracketId} already exists`, 409);
  }

  const dirName = `${bracketId}_${slugify(bracketTitle)}`;
  const targetDir = join(CORE_USECASES_DIR, dirName);
  await mkdir(targetDir, { recursive: false });

  const yamlContent = toYaml(normalized);
  await writeFile(join(targetDir, 'UseCase_Bracket.yaml'), yamlContent, 'utf-8');
  await writeFile(join(targetDir, 'Business_Factsheet.md'), buildFactsheet(normalized), 'utf-8');

  logAuditEvent('bracket', bracketId, 'create', {
    before: null,
    after: { title: bracketTitle, path: `core/usecases/core/${dirName}` },
    justification: 'Created from Steering draft scaffold',
  }, 'default', user.email);

  invalidateForgeBootstrapCache();

  return apiCreated({
    created: true,
    id: bracketId,
    path: `core/usecases/core/${dirName}/UseCase_Bracket.yaml`,
    factsheet: `core/usecases/core/${dirName}/Business_Factsheet.md`,
  });
}
