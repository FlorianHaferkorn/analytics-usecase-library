import type { Metadata } from 'next';
import { loadKpi } from '@/lib/core/catalog-loader';
import { DetailClient } from '@/components/detail/DetailClient';

interface DetailPageProps {
  params: Promise<{ type: string; id: string }>;
}

export async function generateMetadata({ params }: DetailPageProps): Promise<Metadata> {
  const { type, id } = await params;
  if (type === 'kpi') {
    const kpi = await loadKpi(id);
    if (kpi) return { title: `${kpi.kpi_key} | Studio` };
  }
  return { title: `${type}/${id} | Studio` };
}

export default async function DetailPage({ params }: DetailPageProps) {
  const { type, id } = await params;
  const kpi = type === 'kpi' ? await loadKpi(id) : null;
  return <DetailClient kpi={kpi} type={type} id={id} />;
}
