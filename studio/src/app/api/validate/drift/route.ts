import { runDriftScan } from '@/lib/validation/drift-scanner';

export async function GET() {
  const report = await runDriftScan();
  return Response.json(report);
}
