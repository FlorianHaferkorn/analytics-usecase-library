import { processGovernedExportRequest } from '@/lib/delivery/governed-export-handler';

export async function POST(request: Request) {
  return processGovernedExportRequest(request, ['osi'], 'osi');
}
