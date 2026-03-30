import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { apiSuccess } from '@/lib/api/response';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const domain = searchParams.get('domain');

  let brackets = await loadAllBrackets();

  if (domain) {
    brackets = brackets.filter((b) => b.domain === domain);
  }

  return apiSuccess({ count: brackets.length, brackets });
}
