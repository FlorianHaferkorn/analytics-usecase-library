import { apiError, apiSuccess } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';
import { requireAuth } from '@/lib/auth/session';
import {
  persistWizardDraft,
  type WizardDraftInput,
  type WizardPersistKind,
} from '@/lib/studio/wizard-persist';

const KINDS: WizardPersistKind[] = ['kpi', 'bracket', 'action', 'source'];

function isDraft(v: unknown): v is WizardDraftInput {
  if (!v || typeof v !== 'object') return false;
  const o = v as Record<string, unknown>;
  return (
    typeof o.name === 'string' &&
    typeof o.ref === 'string' &&
    typeof o.domain === 'string' &&
    typeof o.type === 'string' &&
    typeof o.grain === 'string' &&
    typeof o.description === 'string'
  );
}

export async function POST(request: Request) {
  const [user, authError] = await requireAuth();
  if (authError) return authError;

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return apiError(ErrorCode.VALIDATION_ERROR, 'Invalid JSON body', 400);
  }

  const kind = (body as { kind?: string }).kind;
  const draft = (body as { draft?: unknown }).draft;

  if (!kind || !KINDS.includes(kind as WizardPersistKind)) {
    return apiError(ErrorCode.VALIDATION_ERROR, `kind must be one of: ${KINDS.join(', ')}`, 400);
  }
  if (!isDraft(draft)) {
    return apiError(ErrorCode.VALIDATION_ERROR, 'draft object is incomplete', 400);
  }

  try {
    const result = await persistWizardDraft(kind as WizardPersistKind, draft, user!.email);
    return apiSuccess(result);
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Persist failed';
    return apiError(ErrorCode.INTERNAL_ERROR, message, 500);
  }
}
