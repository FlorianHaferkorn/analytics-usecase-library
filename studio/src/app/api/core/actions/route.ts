import { NextResponse } from 'next/server';
import { loadAllActionCodes } from '@/lib/core/action-loader';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const domain = searchParams.get('domain');

  let actions = await loadAllActionCodes();

  if (domain) {
    actions = actions.filter((a) => a.owner_domain === domain);
  }

  return NextResponse.json({
    count: actions.length,
    actions,
  });
}
