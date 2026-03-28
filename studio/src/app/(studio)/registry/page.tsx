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

export default async function RegistryPage() {
  const [kpis, actions, brackets, spines] = await Promise.all([
    loadKpiCatalog(),
    loadAllActionCodes(),
    loadAllBrackets(),
    loadAllSpines(),
  ]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)' }}>
      <IntegrityPanel
        kpiCount={kpis.length}
        actionCount={actions.length}
        bracketCount={brackets.length}
      />

      <RegistryClientWrapper />

      <section>
        <h2 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--slate-50)', marginBottom: 'var(--sp-2)' }}>
          KPI Catalog ({kpis.length})
        </h2>
        <KpiRegistryTable kpis={kpis} />
      </section>

      <section>
        <h2 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--slate-50)', marginBottom: 'var(--sp-2)' }}>
          Action Codes ({actions.length})
        </h2>
        <ActionRegistryTable actions={actions} />
      </section>

      <section>
        <h2 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--slate-50)', marginBottom: 'var(--sp-2)' }}>
          Use Case Brackets ({brackets.length})
        </h2>
        <BracketRegistryTable brackets={brackets} />
      </section>

      <section>
        <h2 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--slate-50)', marginBottom: 'var(--sp-2)' }}>
          Decision Spines ({spines.length})
        </h2>
        <SpineList spines={spines} />
      </section>
    </div>
  );
}
