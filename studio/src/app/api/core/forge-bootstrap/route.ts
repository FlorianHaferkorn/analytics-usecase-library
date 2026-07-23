import { loadForgeBootstrap } from '@/lib/core/forge-bootstrap';
import { apiSuccess } from '@/lib/api/response';
import { requireAuth } from '@/lib/auth/session';

export async function GET() {
  const [, authError] = await requireAuth();
  if (authError) return authError;

  const payload = await loadForgeBootstrap();
  return apiSuccess(payload);
}
