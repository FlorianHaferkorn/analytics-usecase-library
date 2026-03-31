/**
 * Lineage Graph Builder
 *
 * Constructs a directed acyclic graph connecting data contracts (dimension/fact
 * tables) to KPIs to use case brackets, enabling visual lineage exploration.
 */

import { loadAllContracts } from './contract-loader';
import { loadKpiCatalog } from './catalog-loader';
import { loadAllBrackets } from './bracket-loader';
import type { DataContract } from '@/lib/schemas';
import type { CatalogKpi } from './catalog-loader';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';

export interface LineageNode {
  id: string;
  type: 'dimension' | 'fact' | 'kpi' | 'bracket';
  label: string;
  domain: string;
  metadata: Record<string, string>;
}

export interface LineageEdge {
  source: string;
  target: string;
  relationship: 'sources' | 'computes' | 'consumes';
}

export interface LineageGraph {
  nodes: LineageNode[];
  edges: LineageEdge[];
}

interface PreloadedData {
  contracts: DataContract[];
  kpis: CatalogKpi[];
  brackets: UseCaseBracketV20Lean[];
}

/** Extract table name from a lineage reference like "fact_sales.Net Sales Amount". */
function extractTable(ref: string): string | null {
  const dot = ref.indexOf('.');
  return dot > 0 ? ref.slice(0, dot) : null;
}

/**
 * Build a lineage graph from data contracts, KPIs, and brackets.
 * Accepts optional pre-loaded data for testing.
 */
export async function buildLineageGraph(
  preloaded?: PreloadedData,
): Promise<LineageGraph> {
  const [contracts, kpis, brackets] = preloaded
    ? [preloaded.contracts, preloaded.kpis, preloaded.brackets]
    : await Promise.all([loadAllContracts(), loadKpiCatalog(), loadAllBrackets()]);

  const nodes: LineageNode[] = [];
  const edges: LineageEdge[] = [];
  const nodeIds = new Set<string>();

  const addNode = (node: LineageNode) => {
    if (!nodeIds.has(node.id)) {
      nodeIds.add(node.id);
      nodes.push(node);
    }
  };

  const addEdge = (edge: LineageEdge) => {
    edges.push(edge);
  };

  // 1. Data contract nodes (dimensions + facts)
  for (const contract of contracts) {
    for (const dim of contract.dimension ?? []) {
      addNode({
        id: `dim:${dim.name}`,
        type: 'dimension',
        label: dim.name,
        domain: contract.domain,
        metadata: { columns: String(dim.columns.length) },
      });
    }
    for (const fact of contract.fact ?? []) {
      addNode({
        id: `fact:${fact.name}`,
        type: 'fact',
        label: fact.name,
        domain: contract.domain,
        metadata: { grain: fact.grain, columns: String(fact.columns.length) },
      });

      // Connect fact → dimension via foreign key refs
      for (const col of fact.columns) {
        if (col.ref) {
          const refTable = extractTable(col.ref);
          if (refTable && nodeIds.has(`dim:${refTable}`)) {
            addEdge({ source: `dim:${refTable}`, target: `fact:${fact.name}`, relationship: 'sources' });
          }
        }
      }
    }
  }

  // 2. KPI nodes + edges to source tables via lineage[]
  for (const kpi of kpis) {
    addNode({
      id: `kpi:${kpi.kpi_id}`,
      type: 'kpi',
      label: kpi.kpi_key,
      domain: kpi.domain_tag[0] ?? 'Unknown',
      metadata: { type: kpi.kpi_type, role: kpi.kpi_role },
    });

    // Connect to source tables via technical.lineage
    for (const ref of kpi.technical?.lineage ?? []) {
      const table = extractTable(ref);
      if (table) {
        const factId = `fact:${table}`;
        const dimId = `dim:${table}`;
        if (nodeIds.has(factId)) {
          addEdge({ source: factId, target: `kpi:${kpi.kpi_id}`, relationship: 'computes' });
        } else if (nodeIds.has(dimId)) {
          addEdge({ source: dimId, target: `kpi:${kpi.kpi_id}`, relationship: 'computes' });
        }
      }
    }
  }

  // 3. KPI-to-KPI dependency edges via depends_on_measures
  for (const kpi of kpis) {
    for (const dep of kpi.technical?.depends_on_measures ?? []) {
      if (nodeIds.has(`kpi:${dep}`)) {
        addEdge({ source: `kpi:${dep}`, target: `kpi:${kpi.kpi_id}`, relationship: 'computes' });
      }
    }
  }

  // 4. Bracket nodes + edges to KPIs
  for (const bracket of brackets) {
    addNode({
      id: `bracket:${bracket.id}`,
      type: 'bracket',
      label: bracket.title,
      domain: bracket.domain,
      metadata: { actions: String(bracket.orchestration.action_code_ids.length) },
    });

    const stratId = `kpi:${bracket.orchestration.strategic_kpi_id}`;
    if (nodeIds.has(stratId)) {
      addEdge({ source: stratId, target: `bracket:${bracket.id}`, relationship: 'consumes' });
    }

    for (const kpiId of bracket.orchestration.influencing_kpi_ids) {
      if (nodeIds.has(`kpi:${kpiId}`)) {
        addEdge({ source: `kpi:${kpiId}`, target: `bracket:${bracket.id}`, relationship: 'consumes' });
      }
    }
  }

  return { nodes, edges };
}
