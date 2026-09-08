import { requireRole } from '@/lib/auth/require-role';
import { projectEstimation } from '@/lib/bridge/project-estimation';
import { packageRepositoryError } from '@/lib/project-package/http';
import { apiError, apiSuccess } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';

export async function POST(request: Request, {params}: {params: Promise<{projectId: string}>}) {
  const {projectId} = await params;
  const [,denied] = await requireRole('editor',projectId);
  if (denied) return denied;
  let body;
  try {
    const raw = await request.text();
    if (raw.length > 500_000) return apiError(ErrorCode.VALIDATION_ERROR,'Estimate scenario too large',413);
    body = JSON.parse(raw);
    if (!body || !/^[a-f0-9]{64}$/.test(body.revisionHash) || !body.scenario) throw new Error('Missing inputs');
  } catch {return apiError(ErrorCode.VALIDATION_ERROR,'A pinned revision and explicit scenario are required',422);}
  const result = await projectEstimation(projectId,body.revisionHash,body.scenario);
  if (!result.ok || !result.value) return packageRepositoryError(result);
  const response = apiSuccess(result.value);
  response.headers.set('Cache-Control','private, no-store');
  return response;
}
