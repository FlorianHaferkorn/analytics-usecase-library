import { redirect } from 'next/navigation';

export default async function CatalogPage({ searchParams }: { searchParams: Promise<{kpi?: string; tab?: string}> }) {
  const query = await searchParams;
  const target = new URLSearchParams({ view: 'manage' });
  if (query.kpi) target.set('kpi', query.kpi);
  if (query.tab) target.set('tab', query.tab);
  redirect('/library?' + target.toString());
}
