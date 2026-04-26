import { loadAllActionCodes } from '@/lib/core/action-loader';
import { apiSuccess } from '@/lib/api/response';
import { requireAuth } from '@/lib/auth/session';

export async function GET(request: Request) {
  const [, authError] = await requireAuth();
  if (authError) return authError;

  const { searchParams } = new URL(request.url);
  const domain = searchParams.get('domain');

  let actions = await loadAllActionCodes();

  if (domain) {
    actions = actions.filter((a) => a.owner_domain === domain);
  }

  return apiSuccess({ count: actions.length, actions });
}
