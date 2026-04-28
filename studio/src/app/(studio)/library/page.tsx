import { Metadata } from 'next';
import { Suspense } from 'react';
import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { LibraryClient } from './library-client';

export const metadata: Metadata = {
  title: 'Library | Studio',
};

export default async function LibraryPage() {
  const metrics = await loadKpiCatalog();

  return (
    <Suspense fallback={<div className="text-foreground-muted text-[13px]">Loading library…</div>}>
      <LibraryClient metrics={metrics} />
    </Suspense>
  );
}
