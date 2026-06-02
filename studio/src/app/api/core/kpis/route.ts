import { loadKpiCatalog, updateKpiInCatalog } from '@/lib/core/catalog-loader';
import { apiSuccess, apiError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';
import { requireAuth } from '@/lib/auth/session';
import { logAuditEvent } from '@/lib/db/audit-repo';

export async function GET(request: Request) {
  const [, authError] = await requireAuth();
  if (authError) return authError;

  const { searchParams } = new URL(request.url);
  const domain = searchParams.get('domain');
  const search = searchParams.get('q');

  let kpis = await loadKpiCatalog();

  if (domain) {
    kpis = kpis.filter((k) => (k.domain_tag ?? []).includes(domain));
  }

  if (search) {
    const q = search.toLowerCase();
    kpis = kpis.filter(
      (k) =>
        k.kpi_id.toLowerCase().includes(q) ||
        k.kpi_key.toLowerCase().includes(q) ||
        k.business?.purpose?.toLowerCase().includes(q)
    );
  }

  return apiSuccess({ count: kpis.length, kpis });
}

export async function PUT(request: Request) {
  const [user, authError] = await requireAuth();
  if (authError) return authError;

  let body: { kpi_id?: string; kpi_key?: string; business?: { definition?: string } };
  try {
    body = await request.json();
  } catch {
    return apiError(ErrorCode.VALIDATION_ERROR, 'Invalid JSON body', 400);
  }

  const kpiId = body.kpi_id?.trim();
  if (!kpiId) {
    return apiError(ErrorCode.VALIDATION_ERROR, 'kpi_id is required', 400);
  }

  const updated = await updateKpiInCatalog(kpiId, {
    kpi_key: body.kpi_key,
    business: body.business,
  });

  if (!updated) {
    return apiError(ErrorCode.NOT_FOUND, `KPI not found: ${kpiId}`, 404);
  }

  logAuditEvent(
    'kpi',
    kpiId,
    'update',
    {
      before: null,
      after: { kpi_key: updated.kpi_key, definition: updated.business.definition },
    },
    'default',
    user!.email,
  );

  return apiSuccess({ saved: true, kpi: updated });
}
