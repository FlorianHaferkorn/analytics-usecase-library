import { loadBracket } from '@/lib/core/bracket-loader';
import { loadKpiMap } from '@/lib/core/catalog-loader';
import { buildIRPackage, type IRPackage } from '@/lib/delivery/ir-builder';
import { generateGitHubWorkflow, generateValidationPipeline, generateDeployScript } from '@/lib/delivery/cicd-adapter';
import { auditWithActor } from '@/lib/db/audit-helpers';
import { apiSuccess, apiValidationError } from '@/lib/api/response';

export async function POST(request: Request) {
  const body = await request.json();
  const { useCaseIds } = body as { useCaseIds: string[] };

  if (!useCaseIds?.length) {
    return apiValidationError(['No use case IDs provided']);
  }

  const kpiMap = await loadKpiMap();

  const packages: IRPackage[] = [];
  for (const id of useCaseIds) {
    const bracket = await loadBracket(id);
    if (bracket) {
      packages.push(buildIRPackage(bracket, kpiMap));
    }
  }

  const workflow = generateGitHubWorkflow(packages);
  const validation = generateValidationPipeline(packages);
  const deployScript = generateDeployScript(packages);

  await auditWithActor('export', 'cicd', 'export', {
    before: null,
    after: { format: 'cicd', useCaseIds, packageCount: packages.length },
  });

  return apiSuccess({
    results: [{
      useCaseId: 'cicd-bundle',
      outputs: { workflow, validation, deployScript },
    }],
  });
}
