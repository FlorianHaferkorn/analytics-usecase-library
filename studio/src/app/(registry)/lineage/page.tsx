import { buildLineageGraph } from '@/lib/core/lineage-builder';
import { loadAllContracts } from '@/lib/core/contract-loader';
import { LineageClient } from '@/app/(studio)/lineage/lineage-client';

export default async function LineagePage() {
  const [graph, contracts] = await Promise.all([
    buildLineageGraph(),
    loadAllContracts(),
  ]);

  return <LineageClient graph={graph} contracts={contracts} />;
}
