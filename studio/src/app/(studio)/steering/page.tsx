import { redirect } from 'next/navigation';
import { getSessionUser } from '@/lib/auth/session';

export default async function SteeringPage({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const user = await getSessionUser();
  if (!user) {
    redirect(`/login?callbackUrl=${encodeURIComponent('/steering')}`);
  }

  const params = searchParams ? await searchParams : {};
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (typeof value === 'string') qs.set(key, value);
    else if (Array.isArray(value) && value[0]) qs.set(key, value[0]);
  }
  const query = qs.toString();
  redirect(query ? `/blueprint?${query}` : '/blueprint');
}
