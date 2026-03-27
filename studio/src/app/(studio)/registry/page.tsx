import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { loadAllActionCodes } from '@/lib/core/action-loader';
import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { KpiRegistryTable } from '@/components/registry/kpi-registry-table';
import { ActionRegistryTable } from '@/components/registry/action-registry-table';
import { BracketRegistryTable } from '@/components/registry/bracket-registry-table';
import { IntegrityPanel } from '@/components/registry/integrity-panel';

export default async function RegistryPage() {
  const [kpis, actions, brackets] = await Promise.all([
    loadKpiCatalog(),
    loadAllActionCodes(),
    loadAllBrackets(),
  ]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)' }}>
      <IntegrityPanel
        kpiCount={kpis.length}
        actionCount={actions.length}
        bracketCount={brackets.length}
      />

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
    </div>
  );
}
