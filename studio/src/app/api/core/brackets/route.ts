import { NextResponse } from 'next/server';
import { loadAllBrackets } from '@/lib/core/bracket-loader';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const domain = searchParams.get('domain');

  let brackets = await loadAllBrackets();

  if (domain) {
    brackets = brackets.filter((b) => b.domain === domain);
  }

  return NextResponse.json({
    count: brackets.length,
    brackets,
  });
}
