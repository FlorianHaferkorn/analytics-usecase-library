/**
 * Intermediate Representation (IR) Builder
 *
 * Transforms Core artifacts (UseCase Brackets, KPIs, Action Codes) into a
 * tool-agnostic IR that adapters consume to generate target-specific output.
 *
 * The IR is the contract between the Studio and all export adapters.
 */

import type { UseCaseBracketV20Lean } from '@/lib/schemas';
import type { CatalogKpi } from '@/lib/core/catalog-loader';

/** A measure to be generated in the target semantic model. */
export interface IRMeasure {
  id: string;
  name: string;
  expression: string;
  formatString: string;
  description: string;
  dependsOn: string[];
  folder: string;
}

/** A report page definition. */
export interface IRPage {
  id: string;
  title: string;
  template: string;
  components: IRComponent[];
}

/** A visual component on a report page. */
export interface IRComponent {
  slot: '3s' | '30s' | '300s';
  type: string;
  kpiIds: string[];
  config: Record<string, unknown>;
}

/** Complete IR for one use case export. */
export interface IRPackage {
  useCaseId: string;
  title: string;
  domain: string;
  measures: IRMeasure[];
  pages: IRPage[];
  actionCodes: string[];
  metadata: {
    generatedAt: string;
    schemaVersion: string;
    sourceCommit?: string;
  };
}

/** Build an IR package from a UseCase Bracket and its resolved KPIs. */
export function buildIRPackage(
  bracket: UseCaseBracketV20Lean,
  kpiMap: Map<string, CatalogKpi>
): IRPackage {
  // Collect all KPI IDs referenced by this bracket
  const allKpiIds = new Set<string>();
  allKpiIds.add(bracket.orchestration.strategic_kpi_id);
  for (const id of bracket.orchestration.influencing_kpi_ids) allKpiIds.add(id);
  for (const id of bracket.orchestration.supporting_kpi_ids ?? []) allKpiIds.add(id);

  // Build measures from resolved KPIs
  const measures: IRMeasure[] = [];
  for (const kpiId of allKpiIds) {
    const kpi = kpiMap.get(kpiId);
    if (!kpi?.technical) continue;

    measures.push({
      id: kpiId,
      name: kpi.technical.dax_name,
      expression: kpi.technical.dax_expression?.trim() ?? '',
      formatString: kpi.technical.formatString ?? '#,0',
      description: kpi.technical.description ?? kpi.business?.purpose ?? '',
      dependsOn: kpi.technical.depends_on_measures ?? [],
      folder: bracket.domain,
    });
  }

  // Build pages from UX layout rules
  const pages: IRPage[] = [];

  if (bracket.ux_layout_rules) {
    const layout = bracket.ux_layout_rules;

    // Page 1: Summary (Pulse + Investigator)
    if (layout.page_1_summary) {
      const components: IRComponent[] = [];

      if (layout.page_1_summary.component_3s) {
        components.push({
          slot: '3s',
          type: layout.page_1_summary.component_3s.visual_type ?? 'kpi_card',
          kpiIds: [layout.page_1_summary.component_3s.kpi_id].filter(Boolean) as string[],
          config: {},
        });
      }

      if (Array.isArray(layout.page_1_summary.component_30s)) {
        for (const comp of layout.page_1_summary.component_30s) {
          components.push({
            slot: '30s',
            type: comp.visual_type ?? 'bar_chart',
            kpiIds: comp.kpi_ids ?? (comp.kpi_id ? [comp.kpi_id] : []),
            config: {},
          });
        }
      }

      pages.push({
        id: `${bracket.id}_P1`,
        title: layout.page_1_summary.title ?? `${bracket.title} Summary`,
        template: layout.page_1_summary.template_id ?? 'pulse',
        components,
      });
    }

    // Page 2: Execution (Action Matrix)
    if (layout.page_2_execution) {
      const components: IRComponent[] = [];

      if (layout.page_2_execution.component_300s) {
        components.push({
          slot: '300s',
          type: 'evidence_grid',
          kpiIds: [],
          config: {
            evidence_grain: layout.page_2_execution.component_300s.evidence_grain,
            evidence_columns: layout.page_2_execution.component_300s.evidence_columns,
            action_panel: layout.page_2_execution.component_300s.action_panel,
          },
        });
      }

      pages.push({
        id: `${bracket.id}_P2`,
        title: layout.page_2_execution.title ?? `${bracket.title} Execution`,
        template: layout.page_2_execution.template_id ?? 'action_matrix',
        components,
      });
    }
  }

  return {
    useCaseId: bracket.id,
    title: bracket.title,
    domain: bracket.domain,
    measures,
    pages,
    actionCodes: bracket.orchestration.action_code_ids,
    metadata: {
      generatedAt: new Date().toISOString(),
      schemaVersion: bracket.schema_version,
    },
  };
}
