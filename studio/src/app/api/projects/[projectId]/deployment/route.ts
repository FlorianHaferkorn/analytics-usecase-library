import {requireRole} from '@/lib/auth/require-role';
import {projectDeployment} from '@/lib/bridge/project-deployment';
import {projectAutomation} from '@/lib/bridge/project-automation';
import {packageRepositoryError} from '@/lib/project-package/http';
import {apiError,apiSuccess} from '@/lib/api/response';
import {ErrorCode} from '@/lib/api/error-codes';

type Context={params:Promise<{projectId:string}>};
const HASH=/^[a-f0-9]{64}$/;
export async function POST(request:Request,{params}:Context) {
  const {projectId}=await params;
  const [,denied]=await requireRole('editor',projectId);
  if (denied) return denied;
  let body;
  try {
    const raw=await request.text();
    if (raw.length>2_000_000) return apiError(ErrorCode.VALIDATION_ERROR,'Evidence exceeds 2 MB',413);
    body=JSON.parse(raw);
    if (!body || typeof body.revisionHash!=='string' || !HASH.test(body.revisionHash) || !['plan','reconcile'].includes(body.mode) ||
      !body.observedState || typeof body.observedState!=='object' || Array.isArray(body.observedState) ||
      Object.keys(body).some(key=>!['revisionHash','mode','observedState','tenantId','environment','plan'].includes(key))) throw new Error('Invalid evidence');
    if (body.mode==='plan' && (typeof body.tenantId!=='string' || typeof body.environment!=='string' || body.environment.length>32)) throw new Error('Missing target');
    if (body.mode==='reconcile' && (body.plan?.project_ref!==projectId || body.plan?.revision_hash!==body.revisionHash)) throw new Error('Foreign plan');
  } catch {return apiError(ErrorCode.VALIDATION_ERROR,'Provide the pinned revision and explicit evidence for plan or reconciliation. Apply is not accepted.',422);}
  // Reconciliation must not accept a hash-rewritten foreign plan as authoritative.
  const status=await projectAutomation(projectId,body.revisionHash);
  if (!status.ok || !status.value) return packageRepositoryError(status);
  if (!status.value.generation_allowed) return apiError(ErrorCode.VALIDATION_ERROR,'The current released project revision is required',409);
  const payload=body.mode==='plan'
    ? {project_ref:projectId,revision_hash:body.revisionHash,tenant_id:body.tenantId,environment:body.environment,observed_state:body.observedState}
    : {plan:body.plan,observed_state:body.observedState};
  const result=await projectDeployment(projectId,body.mode,payload);
  if (!result.ok || !result.value) return packageRepositoryError(result);
  const response=apiSuccess(result.value);response.headers.set('Cache-Control','private, no-store');return response;
}
