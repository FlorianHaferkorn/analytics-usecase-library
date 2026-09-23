import 'server-only';
import {execFile} from 'node:child_process';
import {isAbsolute,join,resolve} from 'node:path';
import type {PackageRepositoryResult} from './project-package-repository';

export interface DeploymentPlan {
  principal_id?: string;
  project_ref: string; revision_hash: string; tenant_id: string; environment: string; plan_sha256: string;
  workspace_apply_ready: boolean; whole_project_apply_ready: false;
  operations: Array<{id: string; action: 'create'|'noop'|'conflict'|'blocked';reason:string;desired:{name:string};existing_id:string|null}>;
  capabilities:Array<{family:string;status:string;reason:string}>;
}
export interface DeploymentReadback {
  project_ref:string;revision_hash:string;plan_sha256:string;workspace_match:boolean;whole_project_verified:false;
  results:Array<{id:string;state:string;workspace_ids:string[]}>;
}
/** Offline planning/readback only. No tenant credentials or apply command accepted. */
export async function projectDeployment<T>(projectId:string,mode:'plan'|'reconcile',payload:Record<string,unknown>):Promise<PackageRepositoryResult<T>> {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/.test(projectId)) return {available:true,ok:false,status:422,error:'Invalid project identifier'};
  const root=process.env.ALUCA_REPO_ROOT || (process.env.NODE_ENV === 'test' ? resolve(process.cwd(),'..') : undefined);
  if (!root) return {available:false,ok:false,status:503,error:'Deployment planning unavailable'};
  const configured=process.env.STUDIO_PACKAGE_DATA_ROOT;
  const dataRoot=configured ? (isAbsolute(configured) ? configured : resolve(process.cwd(),configured)) : join(process.cwd(),'data','project-packages');
  const python=process.env.SUPERVERSION_PYTHON || (process.platform === 'win32' ? 'py' : 'python3');
  const args=[...(!process.env.SUPERVERSION_PYTHON && process.platform === 'win32' ? ['-3'] : []),'-m','tooling.superversion.project_package.deployment_plan','--repository',join(dataRoot,'repositories',projectId),'--schemas',join(root,'tooling','generator','schemas'),'--mode',mode];
  return new Promise(accept => {
    const child=execFile(python,args,{cwd:root,timeout:60_000,maxBuffer:16*1024*1024,env:{...process.env,PYTHONIOENCODING:'utf-8'}},(error,stdout) => {
      try {
        const result=JSON.parse(stdout) as {ok:boolean;value?:T;error?:string;status?:number};
        if (!error && result.ok && result.value) accept({available:true,ok:true,value:result.value});
        else accept({available:true,ok:false,status:result.status || 409,error:result.error || 'Deployment preflight failed'});
      } catch {accept({available:false,ok:false,status:503,error:'Deployment planner did not return a valid result'});}
    });
    child.stdin?.on('error',() => { /* Process completion handles failed startup. */ });
    child.stdin?.end(JSON.stringify(payload));
  });
}
