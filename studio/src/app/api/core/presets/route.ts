import { NextResponse } from 'next/server';
import { getRoiPreset } from '@/lib/core/roi-presets';

/**
 * GET /api/core/presets?kpiId=margin.gm.pct
 *
 * Query param avoids dot-in-path routing issues for KPI ids.
 */
export async function GET(request: Request) {
  const kpiId = new URL(request.url).searchParams.get('kpiId')?.trim();

  if (!kpiId) {
    return NextResponse.json(
      { error: { code: 'BAD_REQUEST', message: 'Missing required query parameter: kpiId' } },
      { status: 400 },
    );
  }

  const preset = getRoiPreset(kpiId);

  if (!preset) {
    return NextResponse.json(
      { error: { code: 'NOT_FOUND', message: `No preset found for KPI: ${kpiId}` } },
      { status: 404 },
    );
  }

  return NextResponse.json({ preset }, { status: 200 });
}
