import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { loadAllActionCodes } from '@/lib/core/action-loader';
import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { loadAllSpines } from '@/lib/core/spine-loader';
import { KpiRegistryTable } from '@/components/registry/kpi-registry-table';
import { ActionRegistryTable } from '@/components/registry/action-registry-table';
import { BracketRegistryTable } from '@/components/registry/bracket-registry-table';
import { IntegrityPanel } from '@/components/registry/integrity-panel';
import { RegistryClientWrapper } from '@/components/registry/registry-client-wrapper';
import { SpineList } from '@/components/registry/spine-list';
import { ActivityTimeline } from '@/components/registry/activity-timeline';
import { CollapsiblePanel } from '@/components/ui/collapsible-panel';
import { StudioPage, StudioPageHeader } from '@/components/ui/studio-page';

export default async function CatalogPage() {
  const [kpis, actions, brackets, spines] = await Promise.all([
    loadKpiCatalog(),
    loadAllActionCodes(),
    loadAllBrackets(),
    loadAllSpines(),
  ]);

  return (
    <StudioPage style={{ gap: 'var(--sp-3)' }}>
      <StudioPageHeader
        eyebrow="Registry / Catalog"
        title="Catalog"
        description="Audit governed assets, inspect drift and approvals, and keep the catalog, action framework and brackets on one shared control surface."
        badge={`${kpis.length + actions.length + brackets.length} governed items`}
        tone="success"
      />

      <IntegrityPanel
        kpiCount={kpis.length}
        actionCount={actions.length}
        bracketCount={brackets.length}
      />

      <RegistryClientWrapper />

      <CollapsiblePanel title={`KPI Catalog (${kpis.length})`} description="Inspect governed KPI definitions and their readiness for downstream use cases." defaultOpen={true}>
        <KpiRegistryTable kpis={kpis} />
      </CollapsiblePanel>

      <CollapsiblePanel title={`Action Codes (${actions.length})`} description="Review the action framework and operational trigger surface in one table." defaultOpen={true}>
        <ActionRegistryTable actions={actions} />
      </CollapsiblePanel>

      <CollapsiblePanel title={`Use Case Brackets (${brackets.length})`} description="Trace current bracket definitions, governance state and lifecycle changes." defaultOpen={false}>
        <BracketRegistryTable brackets={brackets} />
      </CollapsiblePanel>

      <CollapsiblePanel title={`Decision Spines (${spines.length})`} description="Browse spine structures and ensure linkage consistency across domains." defaultOpen={false}>
        <SpineList spines={spines} />
      </CollapsiblePanel>

      <CollapsiblePanel title="Activity Log" description="Live audit trail — mutations appear here after any create, update, or delete action." defaultOpen={false}>
        <ActivityTimeline />
      </CollapsiblePanel>
    </StudioPage>
  );
}
