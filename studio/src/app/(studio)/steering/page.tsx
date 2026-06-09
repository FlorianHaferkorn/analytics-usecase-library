import { redirect } from 'next/navigation';
import { getSessionUser } from '@/lib/auth/session';

export default async function SteeringPage() {
  const user = await getSessionUser();
  if (!user) {
    redirect(`/login?callbackUrl=${encodeURIComponent('/steering')}`);
  }

  redirect('/blueprint');
}
