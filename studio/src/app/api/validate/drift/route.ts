import { runDriftScan } from '@/lib/validation/drift-scanner';
import { apiSuccess } from '@/lib/api/response';

export async function GET() {
  const report = await runDriftScan();
  return apiSuccess(report);
}
