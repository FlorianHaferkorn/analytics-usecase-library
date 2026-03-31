import { processExportRequest } from '@/lib/delivery/export-handler';
import { generateTmdlMeasures, generatePbipLayout } from '@/lib/delivery/fabric-adapter';

export async function POST(request: Request) {
  return processExportRequest(request, (ir) => ({
    tmdl: generateTmdlMeasures(ir),
    pbip: generatePbipLayout(ir),
  }), 'fabric');
}
