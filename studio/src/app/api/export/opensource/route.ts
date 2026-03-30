import { processExportRequest } from '@/lib/delivery/export-handler';
import { generateSqlViews, generateEvidencePage } from '@/lib/delivery/oss-adapter';

export async function POST(request: Request) {
  return processExportRequest(request, (ir) => ({
    sql: generateSqlViews(ir),
    evidence: generateEvidencePage(ir),
  }), 'opensource');
}
