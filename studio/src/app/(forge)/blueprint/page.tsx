import { Suspense } from 'react';
import { BlueprintPageClient } from './blueprint-page-client';
import { ForgePageSkeleton } from '@/components/forge/forge-page-skeleton';

export default function BlueprintPage() {
  return (
    <Suspense fallback={<ForgePageSkeleton title="Blueprint" />}>
      <BlueprintPageClient />
    </Suspense>
  );
}
