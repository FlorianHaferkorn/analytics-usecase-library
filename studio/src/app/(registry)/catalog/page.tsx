import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { loadAllActionCodes } from '@/lib/core/action-loader';
import { CatalogLibrary } from '@/components/registry/catalog-library';
import { PendingDraftBanner } from '@/components/ui/pending-draft-banner';

export default async function CatalogPage({
  searchParams,
}: {
  searchParams?: Promise<{ kpi?: string; tab?: string }>;
}) {
  const [kpis, brackets, actions, resolved] = await Promise.all([
    loadKpiCatalog().catch(() => []),
    loadAllBrackets().catch(() => []),
    loadAllActionCodes().catch(() => []),
    searchParams ?? Promise.resolve({}),
  ]);

  const highlightKpiId = (resolved as { kpi?: string }).kpi ?? null;
  const initialTab = (resolved as { tab?: string }).tab ?? 'kpis';

  return (
    <>
      <PendingDraftBanner />
      <CatalogLibrary
        kpis={kpis}
        brackets={brackets}
        actions={actions}
        highlightKpiId={highlightKpiId}
        initialTab={initialTab}
      />
    </>
  );
}
