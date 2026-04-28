import { Metadata } from 'next';
import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { LibraryClient } from './library-client';

export const metadata: Metadata = {
  title: 'Library | Studio',
};

export default async function LibraryPage() {
  const metrics = await loadKpiCatalog();

  return <LibraryClient metrics={metrics} />;
}
