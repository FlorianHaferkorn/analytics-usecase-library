import { buildLineageGraph } from '@/lib/core/lineage-builder';
import { loadAllContracts } from '@/lib/core/contract-loader';
import { LineageClient } from '@/app/(studio)/lineage/lineage-client';

interface PageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export default async function LineagePage({ searchParams }: PageProps) {
  const [graph, contracts, params] = await Promise.all([
    buildLineageGraph(),
    loadAllContracts(),
    searchParams,
  ]);

  const focus = params['focus'];
  const focusId = typeof focus === 'string' ? focus : undefined;

  return <LineageClient graph={graph} contracts={contracts} focusId={focusId} />;
}
